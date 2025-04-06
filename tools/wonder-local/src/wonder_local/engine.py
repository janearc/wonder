from pathlib import Path
from typing import Dict, List, Optional, Union
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline
)
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