# Wonder Local

This directory contains tools for running/training Wonder locally (vs against a remote model). Attempts to run on mps if available and will fall back to cpu. This is where local wonder-repls will live when they are built.

## Features

- Dynamic method dispatch via `modengine.py`
- Auto-discovery of local models in Hugging Face cache
- Optional fine-tuning with structured Markdown inputs
- Modular method loading from `modules.yaml`
- Apple MPS support for running on Mac GPU
- Integrated training, generation, estimation, and REPL modes

## Requirements

- Python 3.10+
- Poetry for environment management

## Installation

```bash
cd tools/wonder-local
poetry install
```

You probably want to define `$WONDER_ROOT` because things look for that.

## Usage

All entrypoints are handled via `modengine.py` and routed dynamically through the modular engine:

```bash
poetry run python src/wonder_local/modengine.py <method> [args...]
```

### Example: Local Model Discovery

```bash
poetry run python src/wonder_local/modengine.py local_models
```

### Example: Text Generation

```bash
poetry run python src/wonder_local/modengine.py generate "What is Wonder Framework?"
```

### Example: Fine-tune a model on sigils

```bash
poetry run python src/wonder_local/modengine.py train ~/wonder/sigil
```

## Configuration

Modules are configured in `modules.yaml`. Each method declares its path, whether it's an object method, and any required dependencies:

```yaml
train:
  path: wonder_local.model.train.train
  object_method: true
  requires:
    - load_model
```

Default model paths or IDs (like `microsoft/phi-2`) can also be specified there:

```yaml
load_model:
  path: wonder_local.model.load_model.load_model
  object_method: true
  default_model: microsoft/phi-2
```

## Development

Format, type-check, and test like a pro:

```bash
poetry run black .
poetry run isort .
poetry run vulture src --min-confidence 90
poetry run mypy .
poetry run pytest
```

## Notes

- All model loading assumes safetensors format unless stated otherwise
- If `DEBUG=true` is in your environment, you'll get rich logging with tracebacks
- REPLs, LLaMA-specific extensions, and alignment tooling are also supported

## License

Same as Wonder Framework

---

Made with love, YAML, and just a little MPS magic 🚀
