import yaml
from transformers import pipeline
from rich.console import Console
from pathlib import Path

console = Console()
yaml_path = Path(__file__).parent / "necessary_models.yaml"

def bootstrap_models():
    if not yaml_path.exists():
        console.print(f"[red]✗ Config file not found: {yaml_path}[/red]")
        return

    with open(yaml_path, "r") as f:
        model_list = yaml.safe_load(f)

    for model_name in model_list:
        console.print(f"[blue]⏳ Checking:[/blue] {model_name}")
        try:
            pipeline("text-generation", model=model_name, tokenizer=model_name)
            console.print(f"[green]✓ Cached:[/green] {model_name}")
        except Exception as e:
            console.print(f"[red]✗ Failed to load {model_name}: {e}[/red]")

if __name__ == "__main__":
    bootstrap_models()
