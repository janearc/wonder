from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

def load_model(self, *args):
    """Load the tokenizer and model into self."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            progress.add_task(description="Loading tokenizer...", total=None)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Ensure padding token is set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            progress.add_task(description="Loading model...", total=None)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map="auto",
                low_cpu_mem_usage=True,
            )

            # Prefer MPS if available
            if torch.backends.mps.is_available():
                self.device = "mps"
                self.model.to("mps")
                console.print("[green]Model moved to GPU (MPS).[/green]")
            else:
                self.device = "cpu"
                self.model.to("cpu")
                console.print("[yellow]MPS not available, using CPU instead.[/yellow]")

            console.print("[bold green]Model loaded successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]Error loading model: {str(e)}[/red]")
        raise
