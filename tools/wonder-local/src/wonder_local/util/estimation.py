from rich.console import Console
from transformers import pipeline
from functools import lru_cache

console = Console()

@lru_cache(maxsize=1)
def get_dry_pipeline():
    return pipeline("text-generation", model="distilgpt2", tokenizer="distilgpt2")

def generate_estimated(prompt: str) -> int:
    # Estimate an appropriate max_length using a small model.
    console.print("[blue]Estimating response size using distilgpt2...[/blue]")

    try:
        dry = get_dry_pipeline()
        sample = dry(prompt, max_new_tokens=128, num_return_sequences=1)[0]["generated_text"]

        input_ids = dry.tokenizer(prompt).input_ids
        estimated_tokens = int(len(input_ids) * 1.5)
        final_tokens = min(4096, max(16, estimated_tokens))

        console.print(f"[cyan]Estimated max_length:[/cyan] {final_tokens}")
        return final_tokens
    except Exception as e:
        console.print(f"[red]Estimation failed: {e}. Using default.[/red]")
        return 512
