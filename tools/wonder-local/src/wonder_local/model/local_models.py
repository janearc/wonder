import os
from pathlib import Path

def local_models(self, *args):
    """List Hugging Face models already downloaded to local cache."""
    cache_path = Path.home() / ".cache" / "huggingface" / "hub"
    if not cache_path.exists():
        self.logger.info("[red]No huggingface cache found.[/red]")
        return

    models = set()
    for entry in cache_path.glob("models--*"):
        if entry.is_dir():
            model_name = entry.name.replace("models--", "").replace("--", "/")
            models.add(model_name)

    if not models:
        self.logger.info("[yellow]No local models detected.[/yellow]")
        return

    self.logger.info("[green]📦 Local Hugging Face models cached:[/green]")
    for name in sorted(models):
        self.logger.info(" - %s", name)
