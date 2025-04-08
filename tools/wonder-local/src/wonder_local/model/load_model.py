from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from pathlib import Path

def load_model(self, model_path=None):
    self.logger.info("[cyan]Loading model...[/cyan]")

    default_local_model = Path("./fine-tuned.o")
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    if model_path:
        self.model_name = model_path
    elif default_local_model.exists():
        self.model_name = str(default_local_model)
    else:
        # Attempt to find any model directory in the cache as a fallback
        candidates = list(cache_dir.glob("models--*/*"))
        if candidates:
            self.model_name = str(candidates[0])
            self.logger.info(f"[yellow]Using cached model: {self.model_name}[/yellow]")
        else:
            raise ValueError("No model path provided and no local/cached model found.")

    model_path_obj = Path(self.model_name)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        progress.add_task(description="Loading tokenizer...", total=None)
        if model_path_obj.exists():
            self.tokenizer = AutoTokenizer.from_pretrained(model_path_obj, local_files_only=True)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)

        progress.add_task(description="Loading model...", total=None)
        if model_path_obj.exists():
            self.model = AutoModelForCausalLM.from_pretrained(model_path_obj, local_files_only=True)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name, local_files_only=True)

    if torch.backends.mps.is_available():
        self.device = "mps"
        self.model.to("mps")
        self.logger.info("[green]Model moved to GPU (MPS).[/green]")
    else:
        self.device = "cpu"
        self.model.to("cpu")
        self.logger.warning("[yellow]MPS not available, using CPU instead.[/yellow]")

    self.logger.info(f"[bold green]\U0001F527 Model loaded successfully on device: {self.device}[/bold green]")

