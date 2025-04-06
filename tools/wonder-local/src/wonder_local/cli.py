from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .engine import LocalInferenceEngine

app = typer.Typer(help="Wonder Local - Offline inference engine using Mistral-7B")
console = Console()

@app.command()
def setup(
    model_id: str = typer.Option(
        "mistralai/Mistral-7B-v0.1",
        help="HuggingFace model identifier"
    ),
    cache_dir: Optional[Path] = typer.Option(
        None,
        help="Directory to cache model files"
    ),
    device: str = typer.Option(
        "auto",
        help="Device to run inference on (auto, cpu, mps, etc.)"
    ),
):
    """Initialize and test the Wonder local inference engine."""
    try:
        console.print("[bold blue]Setting up Wonder local inference engine...[/]")
        engine = LocalInferenceEngine(
            model_id=model_id,
            cache_dir=cache_dir,
            device_map=device
        )
        
        # Get and display model info
        info = engine.get_model_info()
        table = Table(title="Model Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in info.items():
            table.add_row(key, str(value))
        
        console.print(table)
        
        # Test generation
        test_prompt = "What is the purpose of Wonder Framework?"
        console.print("\n[bold]Testing generation with prompt:[/]")
        console.print(Panel(test_prompt, title="Prompt"))
        
        response = engine.generate(test_prompt, max_new_tokens=100)[0]
        console.print(Panel(response, title="Response"))
        
        console.print("\n[bold green]Setup complete! The engine is ready for use.[/]")
        
    except Exception as e:
        console.print(f"[bold red]Error during setup:[/] {str(e)}")
        raise typer.Exit(1)

@app.command()
def load():
    """Load the Mistral-7B model."""
    try:
        engine = LocalInferenceEngine()
        engine.load_model()
        console.print("[green]Model loaded successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def generate(
    prompt: str = typer.Argument(..., help="The prompt to generate from"),
    max_length: int = typer.Option(100, help="Maximum length of generated text"),
):
    """Generate text from a prompt using the loaded model."""
    try:
        engine = LocalInferenceEngine()
        engine.load_model()
        result = engine.generate(prompt, max_length)
        console.print("\n[bold]Generated Text:[/bold]")
        console.print(result)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 