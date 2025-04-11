import os
from pathlib import Path


def local_models(self, *args):
    """
    Scans the Hugging Face cache directory for locally downloaded models
    that contain a config.json file (indicating that the model has been fully downloaded).

    This function does not attempt to load the models or validate them
    beyond the presence of their configuration file.
    """
    cache_path = Path.home() / ".cache" / "huggingface" / "hub"
    if not cache_path.exists():
        self.logger.info("[red]No huggingface cache found.[/red]")
        return

    models = set()
    # Recursively look for all config.json files inside any snapshot
    for config_path in cache_path.rglob("*/snapshots/*/config.json"):
        parts = config_path.parts
        try:
            # Try to find the index of the org+model name (e.g., models--meta-llama--llama-3-8b)
            idx = parts.index("models--")
        except ValueError:
            # Fall back to looking for a part that starts with "models--"
            idx = next(
                (i for i, part in enumerate(parts) if part.startswith("models--")), None
            )

        if idx is not None and idx + 1 < len(parts):
            # Convert models--org--name to org/name
            model_parts = parts[idx].replace("models--", "")
            model_name = model_parts.replace("--", "/")
            models.add(model_name)

    if not models:
        self.logger.info("[yellow]No local models with config.json detected.[/yellow]")
        return

    self.logger.info("[green]📦 Local Hugging Face models with config.json:[/green]")
    for name in sorted(models):
        self.logger.info(" - %s", name)
