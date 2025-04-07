"""Wonder Local - Offline inference engine for Wonder Framework."""

__version__ = "0.1.0"

from .engine import LocalInferenceEngine
from .cli import app

__all__ = ["LocalInferenceEngine", "app"] 