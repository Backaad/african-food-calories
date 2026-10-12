"""Honest evaluation: per-dish accuracy, confusion matrix, refusals.

The app shows a dish only if the model is confident enough and its best guess
is not "other"; otherwise it says "dish not recognised". The confidence
threshold is chosen on the validation set, then everything is measured once on
the test set, which was never used for training or for choosing anything.
"""

import numpy as np


def decide(probs: np.ndarray, other: int, threshold: float) -> np.ndarray:
    """Final answer per image: the top class, or `other` when refused."""
    top = probs.argmax(1)
    refused = (probs.max(1) < threshold) | (top == other)
    return np.where(refused, other, top)


def choose_threshold(probs: np.ndarray, y: np.ndarray, other: int,
                     grid=tuple(np.round(np.arange(0.0, 0.96, 0.05), 2))) -> float:
    """Threshold with the most correct final answers on the validation set.

    Correct = right dish accepted, or an "other" image refused. Ties go to the
    lower threshold (fewer refusals).
    """
    scores = [(float((decide(probs, other, t) == y).mean()), -t) for t in grid]
    best_score, neg_t = max(scores)
    return -neg_t


def confusion(y: np.ndarray, pred: np.ndarray, n: int) -> np.ndarray:
    cm = np.zeros((n, n), dtype=int)
    np.add.at(cm, (y, pred), 1)
    return cm


def report(probs: np.ndarray, y: np.ndarray, classes: list[str], other: int, threshold: float,
           sources: list[str] | None = None) -> dict:
    n = len(classes)
    top1 = probs.argmax(1)
    top3 = np.argsort(-probs, axis=1)[:, :3]
    pred = decide(probs, other, threshold)
    is_dish = y != other

    per_class = {}
    cm = confusion(y, pred, n)
    for i, name in enumerate(classes):
        support = int((y == i).sum())
        predicted = int(cm[:, i].sum())
        per_class[name] = {
            "support": support,
            "recall": round(cm[i, i] / support, 4) if support else None,  # accuracy on this dish's images
            "precision": round(cm[i, i] / predicted, 4) if predicted else None,
        }

    def rate(mask):
        return round(float(mask.mean()), 4) if mask.size else None

    result = {
        "threshold": threshold,
        "images": int(len(y)),
        "accuracy_final": rate(pred == y),  # with refusals
        "accuracy_top1_no_refusal": rate(top1 == y),
        "accuracy_top3_no_refusal": rate((top3 == y[:, None]).any(1)),
        "dish_images": {
            "count": int(is_dish.sum()),
            "correct": rate((pred == y)[is_dish]),
            "refused": rate((pred == other)[is_dish]),  # "dish not recognised" on a known dish
            "wrong_dish": rate(((pred != y) & (pred != other))[is_dish]),
        },
        "other_images": {
            "count": int((~is_dish).sum()),
            "correctly_refused": rate((pred == other)[~is_dish]),
            "wrongly_accepted": rate((pred != other)[~is_dish]),
        },
        "per_class": per_class,
        "confusion_matrix": {"labels": classes, "rows_true_cols_predicted": cm.tolist()},
    }
    if sources is not None:
        src = np.asarray(sources)
        result["per_source"] = {
            s: {"images": int((src == s).sum()), "accuracy_final": rate((pred == y)[src == s])}
            for s in sorted(set(sources))
        }
    return result


def plot_confusion(cm: np.ndarray, classes: list[str], path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    norm = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(1.2 + 0.6 * len(classes), 1.0 + 0.6 * len(classes)))
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title)
    for i in range(len(classes)):
        for j in range(len(classes)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        color="white" if norm[i, j] > 0.5 else "black", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
