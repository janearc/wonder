# Wonder Local

Local inference engine for Wonder Framework using Mistral-7B. This tool enables offline access to Wonder's capabilities by running a local language model.

## Features

- Local inference using Mistral-7B (no internet required after setup)
- 4-bit quantization for efficient memory usage
- Simple CLI interface for setup and generation
- Compatible with Apple Silicon (M-series) processors
- Future support for fine-tuning on Wonder sigils

## Requirements

- Python 3.9 or higher
- Poetry for dependency management
- 16GB+ RAM recommended (48GB ideal)
- Apple Silicon Mac (M1/M2/M3) or compatible hardware

## Installation

1. Clone the Wonder repository
2. Navigate to the wonder-local directory:
   ```bash
   cd tools/wonder-local
   ```
3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Usage

### Initial Setup

Before first use, you need to download and set up the model:

```bash
wonder-local setup
```

This will:
- Download the Mistral-7B model (if not cached)
- Configure the model for your hardware
- Run a test generation to verify everything works

You can customize the setup with options:
```bash
wonder-local setup --help
```

### Text Generation

Generate text using the model:

```bash
wonder-local generate "Tell me about the ethic of care in Wonder Framework"
```

Options for generation:
```bash
wonder-local generate --help
```

Common options:
- `--max-tokens`: Control response length
- `--temperature`: Control randomness (0.0-1.0)
- `--model-id`: Use a different model

## Development

The package uses Poetry for dependency management. To set up for development:

```bash
poetry install --with dev
```

Run tests:
```bash
poetry run pytest
```

Format code:
```bash
poetry run black .
poetry run isort .
```

Type checking:
```bash
poetry run mypy .
```

## Future Plans

- [ ] Fine-tuning on Wonder sigils
- [ ] Chat interface similar to ChatGPT
- [ ] Context management for sigils
- [ ] Integration with Wonder CLI
- [ ] Support for different model architectures
- [ ] Training pipeline for custom models

## License

Same as Wonder Framework 