# src/wonder-local/model/train.py

import os
from pathlib import Path

import torch
from datasets import Dataset
from rich.console import Console
from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments

default_data_dir = os.path.join(os.environ.get("WONDER_ROOT", "."), "sigil")

console = Console()


def train(
    self,
    model_id: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    data_dir: str = default_data_dir,
    output_dir: str = "./fine-tuned",
    epochs: int = 3,
    batch_size: int = 1,  # safer default for MPS
    learning_rate: float = 5e-5,
):
    """Fine-tune the model on text files in a directory recursively."""
    console.print("[bold green]🧪 engine.train() is live[/bold green]")

    if not self.model or not self.tokenizer:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    data_path = Path(data_dir)
    if not data_path.is_dir():
        raise ValueError(f"{data_dir} is not a valid directory.")

    console.print("[green]Collecting markdown files for training...[/green]")
    texts = []
    for file in data_path.rglob("*.md"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                texts.append(f.read())
        except Exception as e:
            console.print(f"[red]Error reading file {file}: {str(e)}[/red]")

    if not texts:
        raise ValueError("No markdown files found in the directory for training.")

    console.print(
        f"[green]Collected {len(texts)} markdown files. Tokenizing training data...[/green]"
    )
    encodings = self.tokenizer(
        texts, truncation=True, padding=True, return_tensors="pt"
    )
    train_dataset = Dataset.from_dict(encodings)

    data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        save_steps=500,
        save_total_limit=2,
        logging_steps=100,
        report_to="none",
    )

    if torch.backends.mps.is_available():
        self.model.to("mps")
        console.print("[green]Model moved to GPU (MPS).[/green]")
    else:
        self.model.to("cpu")
        console.print("[yellow]MPS not available, using CPU instead.[/yellow]")

    trainer = Trainer(
        model=self.model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
    )

    console.print(
        ":satellite: [bold green]Model is on device:[/bold green]",
        f"[magenta]{next(self.model.parameters()).device}[/magenta]",
    )

    console.print("[green]Starting training...[/green]")
    trainer.train()
    console.print("[green]Training complete![/green]")

    console.print("[green]Saving fine-tuned model...[/green]")
    trainer.save_model(output_dir)
    console.print(f"[green]Model saved to {output_dir}[/green]")
