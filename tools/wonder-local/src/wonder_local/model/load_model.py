from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from pathlib import Path

def load_model(self, model_path=None):
    self.logger.info("[cyan]Loading model...[/cyan]")

    # Read default model name or path from config
    default_model = self.config.get("load_model", {}).get("default_model", "microsoft/phi-2")
    default_model_path = Path(default_model)
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    if model_path:
        self.model_name = model_path
    elif default_model_path.exists():
        self.model_name = str(default_model_path)
    else:
        self.model_name = default_model  # treat as model ID if not a path

    model_path_obj = Path(self.model_name)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        progress.add_task(description="Loading tokenizer...", total=None)
        try:
            if model_path_obj.exists():
                tokenizer = AutoTokenizer.from_pretrained(model_path_obj, local_files_only=True)
            else:
                tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=False)
        except Exception as e:
            raise RuntimeError(f"Failed to load tokenizer from {self.model_name}: {e}")

        progress.add_task(description="Loading model...", total=None)
        try:
            if model_path_obj.exists():
                model = AutoModelForCausalLM.from_pretrained(model_path_obj, local_files_only=True)
            else:
                model = AutoModelForCausalLM.from_pretrained(self.model_name, local_files_only=False)
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {self.model_name}: {e}")

    if torch.backends.mps.is_available():
        device = "mps"
        model.to("mps")
        self.logger.info("[green]Model moved to GPU (MPS).[/green]")
    else:
        device = "cpu"
        model.to("cpu")
        self.logger.warning("[yellow]MPS not available, using CPU instead.[/yellow]")

    self.model = model
    self.tokenizer = tokenizer
    self.device = device

    self.logger.info(f"[bold green]\U0001F527 Model loaded successfully on device: {self.device}[/bold green]")
    return model
