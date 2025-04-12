from rich.console import Console
from transformers import pipeline

console = Console()


def generate_estimated(prompt: str) -> int:
    """Estimate an appropriate max_length using a small model."""
    console.print("[blue]Estimating response size using distilgpt2...[/blue]")
    try:
        dry = pipeline("text-generation", model="distilgpt2", tokenizer="distilgpt2")
        sample = dry(prompt, max_new_tokens=128, num_return_sequences=1)[0][
            "generated_text"
        ]
        estimated_tokens = int(len(sample.split()) * 1.5)
        final_tokens = min(4096, max(256, estimated_tokens))
        console.print(f"[cyan]Estimated max_length:[/cyan] {final_tokens}")
        return final_tokens
    except Exception as e:
        console.print(f"[red]Estimation failed: {e}. Using default.[/red]")
        return 512
