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

All entrypoints are handled via `src/wonder-local/entry.py` and routed dynamically through the modular engine:

```bash
# list models available locally
poetry run wonder local_models

# grab a model from hugging face
poetry run wonder hf_get model/model-name

# verify whether mps is available on the local machine
poetry run wonder mpstest

# attempt to load a language model
poetry run wonder load_model model/model-name

# run unit/regression tests
poetry run wonder run_tests

# list available sigils
poetry run wonder sigils /path/to/sigils/dir

# generate taxonometric profile of a sigil
poetry run wonder sigil_profile /path/to/sigil.md

# generate taxonometric profile for all sigils
poetry run wonder sigil_profile_all /path/to/sigils/dir

# use the default language model to generate text
poetry run wonder generate "what is a dog?"

# generate pretraining data from a sigil
poetry run wonder md_to_questions /path/to/sigil.md

# generate pretraining data from all sigils
poetry run wonder md_to_questions_all /path/to/sigil/dir

# run the rlhf shell to update training data
poetry run wonder rlhf_repl /path/to/pretraining/data
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
