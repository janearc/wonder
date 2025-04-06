import typer
from rich.console import Console
from pathlib import Path
from .engine import LocalInferenceEngine

app = typer.Typer()
console = Console()

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

@app.command()
def train(
    data_dir: str = typer.Argument(..., help="Directory containing markdown files for training"),
    output_dir: str = typer.Option("./fine-tuned", help="Directory to save the fine-tuned model"),
    epochs: int = typer.Option(3, help="Number of training epochs"),
    batch_size: int = typer.Option(2, help="Batch size for training"),
    learning_rate: float = typer.Option(5e-5, help="Learning rate for training"),
):
    """Fine-tune the model on text files in a directory recursively."""
    try:
        engine = LocalInferenceEngine()
        engine.load_model()
        engine.train(data_dir, output_dir, epochs, batch_size, learning_rate)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
