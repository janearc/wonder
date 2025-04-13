import os
from pathlib import Path

import torch
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(self, model_path=None):
    self.logger.info("[cyan]Loading model...[/cyan]")

    # Pull default model from config, or use phi-2 as fallback
    default_model = self.config.get("load_model", {}).get(
        "default_model", "microsoft/phi-2"
    )
    default_model_path = Path(default_model)
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    # Decide which model name/path to use based on availability
    if model_path:
        self.model_name = model_path
    elif default_model_path.exists():
        self.model_name = str(default_model_path)
    else:
        self.model_name = default_model  # treat as model ID for HF hub

    model_path_obj = Path(self.model_name)

    # Use rich progress bar while loading tokenizer and model
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        # Load tokenizer
        progress.add_task(description="Loading tokenizer...", total=None)
        try:
            if model_path_obj.exists():
                tokenizer = AutoTokenizer.from_pretrained(
                    model_path_obj, local_files_only=True
                )
            else:
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, local_files_only=False
                )
        except Exception as e:
            raise RuntimeError(f"Failed to load tokenizer from {self.model_name}: {e}")

        # Load model
        progress.add_task(description="Loading model...", total=None)
        try:
            if model_path_obj.exists():
                model = AutoModelForCausalLM.from_pretrained(
                    model_path_obj, local_files_only=True
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name, local_files_only=False
                )
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {self.model_name}: {e}")

    # Move model to device (MPS preferred, fallback to CPU)
    if torch.backends.mps.is_available():
        device = "mps"
        model.to("mps")
        self.logger.info("[green]Model moved to GPU (MPS).[/green]")
    else:
        device = "cpu"
        model.to("cpu")
        self.logger.warning("[yellow]MPS not available, using CPU instead.[/yellow]")

    # Assign components to self for engine access
    self.model = model
    self.tokenizer = tokenizer
    self.device = device

    self.logger.info(
        f"[bold green]🔧 Model loaded successfully on device: {self.device}[/bold green]"
    )
    return model, tokenizer, device
