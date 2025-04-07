import pytest
from wonder_local.engine import LocalInferenceEngine

def test_engine_initialization():
    """Test that the engine initializes correctly."""
    engine = LocalInferenceEngine()
    assert engine.model is None
    assert engine.tokenizer is None
    assert engine.device in ["mps", "cpu"]

def test_model_loading():
    """Test that the model loads correctly."""
    engine = LocalInferenceEngine()
    engine.load_model()
    assert engine.model is not None
    assert engine.tokenizer is not None

def test_generation():
    """Test that text generation works."""
    engine = LocalInferenceEngine()
    engine.load_model()
    prompt = "What is 2+2?"
    response = engine.generate(prompt, max_length=50)
    assert isinstance(response, str)
    assert len(response) > 0 