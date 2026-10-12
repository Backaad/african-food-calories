"""Training, evaluation and export of the african-food-calories classifier."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OTHER = "other"  # label of the "dish not recognised" class
