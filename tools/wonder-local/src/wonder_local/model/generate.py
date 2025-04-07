from rich.console import Console
import torch

console = Console()

def generate(self, *args) -> str:
    if not args:
        raise ValueError("Prompt required for generation.")

    prompt = " ".join(args)

    if not self.model or not self.tokenizer:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    if not hasattr(self, "estimate"):
        raise RuntimeError("Missing 'estimate' method on engine")

    console.print(f"[dim]Estimating length for prompt: '{prompt}'[/dim]")
    console.print(f"[dim]self.estimate is: {self.estimate} ({type(self.estimate)})[/dim]")
    console.print(f"[bold yellow]Calling self.estimate directly...[/bold yellow]")
    console.print(f"[yellow]About to call self.estimate('test call')[/yellow]")
    test_output = self.estimate("test call")
    console.print(f"[yellow]Test output from estimate: {test_output}[/yellow]")

    max_length = self.estimate(prompt)

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
