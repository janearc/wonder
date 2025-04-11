import os
from pathlib import Path


def local_models(self, *args):
    """List Hugging Face models already downloaded to local cache."""
    cache_path = Path.home() / ".cache" / "huggingface" / "hub"
    if not cache_path.exists():
        self.logger.info("[red]No huggingface cache found.[/red]")
        return

    models = set()
    for config_path in cache_path.rglob("*/snapshots/*/config.json"):
        # This pattern will match paths like ~/.cache/huggingface/hub/models--org--name/snapshots/commit_hash/config.json
        parts = config_path.parts
        try:
            idx = parts.index("models--")
        except ValueError:
            idx = next(
                (i for i, part in enumerate(parts) if part.startswith("models--")), None
            )
        if idx is not None and idx + 1 < len(parts):
            model_parts = parts[idx].replace("models--", "")
            model_name = model_parts.replace("--", "/")
            models.add(model_name)

    if not models:
        self.logger.info("[yellow]No local models with config.json detected.[/yellow]")
        return

    self.logger.info("[green]📦 Local Hugging Face models with config.json:[/green]")
    for name in sorted(models):
        self.logger.info(" - %s", name)
