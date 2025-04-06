from pathlib import Path
from typing import Dict, List, Optional, Union
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from datasets import Dataset
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

class LocalInferenceEngine:
    """Local inference engine for Wonder using Phi-2."""
    
    def __init__(self, model_name: str = "microsoft/phi-2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        # Force CPU for now to avoid MPS issues
        self.device = "cpu"
        console.print(f"[green]Using device: {self.device}[/green]")

    def load_model(self):
        """Load the model and tokenizer."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                # Load tokenizer
                progress.add_task(description="Loading tokenizer...", total=None)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
                # Set padding token to be the same as the EOS token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                # Load model
                progress.add_task(description="Loading model...", total=None)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,  # Use float32 instead of float16
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                )
                
            console.print("[green]Model loaded successfully![/green]")
        except Exception as e:
            console.print(f"[red]Error loading model: {str(e)}[/red]")
            raise

    def train(self, data_dir: str, output_dir: str = "./fine-tuned", epochs: int = 3, batch_size: int = 2, learning_rate: float = 5e-5):
        """Fine-tune the model on text files in a directory recursively."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
    
        from pathlib import Path
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
    
        console.print(f"[green]Collected {len(texts)} markdown files. Tokenizing training data...[/green]")
        encodings = self.tokenizer(texts, truncation=True, padding=True, return_tensors="pt")
        train_dataset = Dataset.from_dict(encodings)  # Create a Dataset from the encodings
    
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
            report_to="none"
        )

        # Move model to the correct device (MPS)
        self.model.to("mps")  # Move the model to the MPS device
    
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )
    
        console.print("[green]Starting training...[/green]")
        trainer.train()
        console.print("[green]Training complete![/green]")
    
        console.print("[green]Saving fine-tuned model...[/green]")
        trainer.save_model(output_dir)
        console.print(f"[green]Model saved to {output_dir}[/green]")

    def generate(self, prompt: str, max_length: int = 100) -> str:
        """Generate text from a prompt."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
                no_repeat_ngram_size=3,
                use_cache=True,
            )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            console.print(f"[red]Error during generation: {str(e)}[/red]")
            raise

    def get_model_info(self) -> Dict[str, Union[str, int]]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "model_type": self.model.config.model_type,
            "vocab_size": self.model.config.vocab_size,
            "hidden_size": self.model.config.hidden_size,
            "num_attention_heads": self.model.config.num_attention_heads,
            "device": str(next(self.model.parameters()).device),
        } 
