import numpy as np

from afctrain.evaluate import choose_threshold, decide, report

CLASSES = ["fufu", "ugali", "other"]
OTHER = 2


def test_decide_refuses_low_confidence_and_other():
    probs = np.array([[0.9, 0.05, 0.05], [0.4, 0.35, 0.25], [0.1, 0.1, 0.8]])
    assert decide(probs, OTHER, 0.5).tolist() == [0, 2, 2]
    assert decide(probs, OTHER, 0.0).tolist() == [0, 0, 2]


def test_threshold_maximises_correct_answers():
    probs = np.array([[0.9, 0.05, 0.05], [0.55, 0.45, 0.0], [0.6, 0.3, 0.1], [0.2, 0.2, 0.6]])
    y = np.array([0, 2, 2, 2])  # the 0.55 and 0.6 images are "other" foods the model calls fufu
    t = choose_threshold(probs, y, OTHER)
    assert 0.6 < t <= 0.9
    assert (decide(probs, OTHER, t) == y).all()


def test_threshold_ties_go_to_the_lowest():
    probs = np.array([[0.9, 0.05, 0.05], [0.55, 0.45, 0.0]])
    assert choose_threshold(probs, np.array([0, 0]), OTHER) == 0.0


def test_report_counts():
    probs = np.array([[0.9, 0.1, 0.0], [0.2, 0.7, 0.1], [0.3, 0.3, 0.4], [0.7, 0.2, 0.1], [0.1, 0.1, 0.8]])
    y = np.array([0, 1, 1, 2, 2])
    r = report(probs, y, CLASSES, OTHER, 0.5, ["a", "a", "b", "b", "b"])
    assert r["accuracy_final"] == 0.6
    assert r["dish_images"] == {"count": 3, "correct": 0.6667, "refused": 0.3333, "wrong_dish": 0.0}
    assert r["other_images"] == {"count": 2, "correctly_refused": 0.5, "wrongly_accepted": 0.5}
    assert r["per_class"]["ugali"] == {"support": 2, "recall": 0.5, "precision": 1.0}
    assert r["confusion_matrix"]["rows_true_cols_predicted"][2] == [1, 0, 1]
    assert r["per_source"] == {"a": {"images": 2, "accuracy_final": 1.0}, "b": {"images": 3, "accuracy_final": 0.3333}}
