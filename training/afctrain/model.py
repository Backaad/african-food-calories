"""Models, input pipeline, training and distillation (Keras 3, TensorFlow backend)."""

import numpy as np
import tensorflow as tf
import keras

ARCHITECTURES = {
    "mobilenet_v3_large": keras.applications.MobileNetV3Large,
    "mobilenet_v3_small": keras.applications.MobileNetV3Small,
    "efficientnet_v2_s": keras.applications.EfficientNetV2S,
}


# ---------------------------------------------------------------- input pipeline


def load_image(path, image_size: int):
    """Decode a file and resize the whole image to image_size x image_size, RGB, float 0-255.

    The phone app must do exactly the same (see model_info.json).
    """
    data = tf.io.read_file(path)
    img = tf.io.decode_image(data, channels=3, expand_animations=False)
    img = tf.image.resize(tf.cast(img, tf.float32), (image_size, image_size))
    return tf.clip_by_value(img, 0.0, 255.0)


def augmenter(seed: int = 0) -> keras.Sequential:
    return keras.Sequential([
        keras.layers.RandomFlip("horizontal", seed=seed),
        keras.layers.RandomRotation(0.05, seed=seed),
        keras.layers.RandomZoom((-0.25, 0.0), seed=seed),
        keras.layers.RandomContrast(0.2, seed=seed),
        keras.layers.RandomBrightness(0.2, value_range=(0, 255), seed=seed),
    ], name="augment")


def make_dataset(paths: list[str], labels: list[int], image_size: int, batch_size: int,
                 training: bool, seed: int = 0) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices((paths, np.asarray(labels, dtype="int32")))
    if training:
        ds = ds.shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)
    ds = ds.map(lambda p, y: (load_image(p, image_size), y), num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size)
    if training:
        aug = augmenter(seed)
        ds = ds.map(lambda x, y: (tf.clip_by_value(aug(x, training=True), 0.0, 255.0), y),
                    num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE)


def class_weights(labels: list[int], num_classes: int) -> dict[int, float]:
    """Inverse-frequency weights, so small classes count as much as big ones."""
    counts = np.bincount(labels, minlength=num_classes).astype(float)
    counts[counts == 0] = 1.0
    weights = len(labels) / (num_classes * counts)
    return {i: float(w) for i, w in enumerate(weights)}


# ---------------------------------------------------------------- models


def build_classifier(arch: str, num_classes: int, image_size: int, weights: str | None = "imagenet",
                     dropout: float = 0.2) -> tuple[keras.Model, keras.Model]:
    """Pretrained backbone + new head. Returns (model producing logits, backbone).

    The backbone includes its own preprocessing: inputs are RGB floats in 0-255.
    """
    backbone = ARCHITECTURES[arch](
        input_shape=(image_size, image_size, 3), include_top=False, weights=weights,
        pooling="avg", include_preprocessing=True,
    )
    backbone.trainable = False
    inputs = keras.Input((image_size, image_size, 3), name="image")
    x = backbone(inputs, training=False)  # BatchNorm stays in inference mode, also when fine-tuning
    x = keras.layers.Dropout(dropout)(x)
    logits = keras.layers.Dense(num_classes, name="logits")(x)
    return keras.Model(inputs, logits, name=arch), backbone


def with_softmax(model: keras.Model) -> keras.Model:
    """Same model, outputting probabilities (what the app receives)."""
    probs = keras.layers.Softmax(name="probabilities")(model.output)
    return keras.Model(model.input, probs, name=f"{model.name}_probs")


def unfreeze_top(backbone: keras.Model, n_layers: int) -> None:
    """Make the last n layers trainable, except BatchNormalization layers."""
    backbone.trainable = True
    for i, layer in enumerate(backbone.layers):
        trainable = i >= len(backbone.layers) - n_layers
        layer.trainable = trainable and not isinstance(layer, keras.layers.BatchNormalization)


def _compile(model: keras.Model, lr: float) -> None:
    model.compile(
        optimizer=keras.optimizers.Adam(lr),
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )


def _callbacks(patience: int):
    return [keras.callbacks.EarlyStopping(monitor="val_accuracy", mode="max", patience=patience,
                                          restore_best_weights=True)]


def train_classifier(model, backbone, train_ds, val_ds, cfg: dict, weights: dict | None, verbose=1) -> dict:
    """Two stages: train the head on a frozen backbone, then fine-tune the top layers."""
    history = {}
    _compile(model, cfg["lr_head"])
    h = model.fit(train_ds, validation_data=val_ds, epochs=cfg["epochs_head"], class_weight=weights,
                  callbacks=_callbacks(cfg.get("patience", 3)), verbose=verbose)
    history["head"] = h.history
    if cfg.get("epochs_finetune", 0) > 0:
        unfreeze_top(backbone, cfg["fine_tune_layers"])
        _compile(model, cfg["lr_finetune"])
        h = model.fit(train_ds, validation_data=val_ds, epochs=cfg["epochs_finetune"], class_weight=weights,
                      callbacks=_callbacks(cfg.get("patience", 3)), verbose=verbose)
        history["finetune"] = h.history
    return history


# ---------------------------------------------------------------- distillation


class Distiller(keras.Model):
    """Train `student` to match the true label and the softened outputs of `teacher`.

    loss = alpha * CE(label, student) + (1 - alpha) * T^2 * KL(softmax(teacher/T) || softmax(student/T))
    """

    def __init__(self, student: keras.Model, teacher: keras.Model, alpha: float = 0.3, temperature: float = 4.0):
        super().__init__()
        self.student, self.teacher = student, teacher
        self.alpha, self.temperature = alpha, temperature
        self.teacher.trainable = False
        self.ce = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        self.kl = keras.losses.KLDivergence()
        self.loss_tracker = keras.metrics.Mean(name="loss")
        self.acc = keras.metrics.SparseCategoricalAccuracy(name="accuracy")

    @property
    def metrics(self):
        return [self.loss_tracker, self.acc]

    def call(self, x, training=False):
        return self.student(x, training=training)

    def _loss(self, y, student_logits, teacher_logits, sample_weight=None):
        t = self.temperature
        hard = self.ce(y, student_logits, sample_weight=sample_weight)
        soft = self.kl(tf.nn.softmax(teacher_logits / t), tf.nn.softmax(student_logits / t)) * t * t
        return self.alpha * hard + (1 - self.alpha) * soft

    def train_step(self, data):
        x, y, sample_weight = keras.utils.unpack_x_y_sample_weight(data)
        teacher_logits = self.teacher(x, training=False)
        with tf.GradientTape() as tape:
            student_logits = self.student(x, training=True)
            loss = self._loss(y, student_logits, teacher_logits, sample_weight)
        variables = self.student.trainable_variables
        self.optimizer.apply_gradients(zip(tape.gradient(loss, variables), variables))
        self.loss_tracker.update_state(loss)
        self.acc.update_state(y, student_logits)
        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y, _ = keras.utils.unpack_x_y_sample_weight(data)
        student_logits = self.student(x, training=False)
        self.loss_tracker.update_state(self.ce(y, student_logits))
        self.acc.update_state(y, student_logits)
        return {m.name: m.result() for m in self.metrics}


def distill(student, student_backbone, teacher, train_ds, val_ds, cfg: dict, weights, verbose=1) -> dict:
    """Continue training an already trained student with the teacher's soft targets."""
    unfreeze_top(student_backbone, cfg["fine_tune_layers"])
    distiller = Distiller(student, teacher, cfg["alpha"], cfg["temperature"])
    distiller.compile(optimizer=keras.optimizers.Adam(cfg["lr"]))
    h = distiller.fit(train_ds, validation_data=val_ds, epochs=cfg["epochs"], class_weight=weights,
                      callbacks=_callbacks(cfg.get("patience", 3)), verbose=verbose)
    return h.history
