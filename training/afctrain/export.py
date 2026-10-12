"""Export to TensorFlow Lite (float16) and check it answers like the original."""

import tempfile
from pathlib import Path

import numpy as np
import tensorflow as tf


def to_tflite_float16(model, path: Path) -> Path:
    """Convert a Keras model (outputting probabilities) to a float16 .tflite file."""
    with tempfile.TemporaryDirectory() as tmp:
        saved = Path(tmp) / "saved_model"
        model.export(str(saved), format="tf_saved_model", verbose=False)
        converter = tf.lite.TFLiteConverter.from_saved_model(str(saved))
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        path.write_bytes(converter.convert())
    return path


def _interpreter(path: Path):
    try:
        from ai_edge_litert.interpreter import Interpreter  # LiteRT, the successor of tf.lite
    except ImportError:
        Interpreter = tf.lite.Interpreter
    interpreter = Interpreter(model_path=str(path))
    interpreter.allocate_tensors()
    return interpreter


def tflite_predict(path: Path, images: np.ndarray) -> np.ndarray:
    """Run the .tflite model image by image (as the phone does)."""
    interpreter = _interpreter(path)
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]
    results = []
    for image in images:
        interpreter.set_tensor(inp["index"], image[None].astype(inp["dtype"]))
        interpreter.invoke()
        results.append(interpreter.get_tensor(out["index"])[0])
    return np.asarray(results)


def parity(reference: np.ndarray, lite: np.ndarray) -> dict:
    """How closely the phone model matches the original on the same images."""
    return {
        "images": int(len(reference)),
        "top1_agreement": round(float((reference.argmax(1) == lite.argmax(1)).mean()), 4),
        "max_abs_probability_difference": round(float(np.abs(reference - lite).max()), 5),
        "mean_abs_probability_difference": round(float(np.abs(reference - lite).mean()), 6),
    }
