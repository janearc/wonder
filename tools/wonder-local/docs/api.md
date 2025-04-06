# Wonder Local API Documentation

## LocalInferenceEngine

The core class for local inference using Phi-2 model.

### Initialization

```python
from wonder_local import LocalInferenceEngine

engine = LocalInferenceEngine(model_name="microsoft/phi-2")
```

Parameters:
- `model_name` (str): HuggingFace model identifier (default: "microsoft/phi-2")

### Methods

#### load_model()

Loads the model and tokenizer into memory.

```python
engine.load_model()
```

#### generate(prompt: str, max_length: int = 100) -> str

Generates text from a prompt.

Parameters:
- `prompt` (str): Input text to generate from
- `max_length` (int): Maximum length of generated text (default: 100)

Returns:
- `str`: Generated text

Example:
```python
response = engine.generate("What is the capital of France?", max_length=200)
```

#### get_model_info() -> Dict[str, Union[str, int]]

Returns information about the loaded model.

Returns:
- Dictionary containing model information (name, type, vocab size, etc.)

## CLI

The package provides a command-line interface for easy interaction.

### Commands

#### load

Load the model into memory.

```bash
wonder-local load
```

#### generate

Generate text from a prompt.

```bash
wonder-local generate "Your prompt here" --max-length 200
```

Options:
- `--max-length`: Maximum length of generated text (default: 100) 