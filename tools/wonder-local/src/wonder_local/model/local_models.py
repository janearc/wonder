import os
from pathlib import Path
from rich.console import Console

console = Console()

def local_models(self, *args):
    """List Hugging Face models already downloaded to local cache."""
    cache_path = Path.home() / ".cache" / "huggingface" / "hub"
    if not cache_path.exists():
        console.print("[red]No huggingface cache found.[/red]")
        return

    models = set()
    for entry in cache_path.glob("models--*"):
        if entry.is_dir():
            model_name = entry.name.replace("models--", "").replace("--", "/")
            models.add(model_name)

    if not models:
        console.print("[yellow]No local models detected.[/yellow]")
        return

    console.print("[green]📦 Local Hugging Face models cached:[/green]")
    for name in sorted(models):
        console.print(f" - {name}")
