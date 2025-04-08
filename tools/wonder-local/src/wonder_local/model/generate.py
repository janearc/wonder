from rich.console import Console
import torch

console = Console()

def generate(self, *args) -> str:
    if not args:
        raise ValueError("Prompt required for generation.")

    prompt = " ".join(args)

    """just use the default engine for this"""
    self.default_engine()

    if not self.model or not self.tokenizer:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    if not hasattr(self, "estimate"):
        raise RuntimeError("Missing 'estimate' method on engine")

    """try to figure out what the max length of response should be"""
    max_length = self.estimate(prompt)

    inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
    outputs = self.model.generate(
        **inputs,
        max_length=max_length,
        num_return_sequences=1,
        temperature=0.3,
        top_p=0.8,
        top_k=40,
        do_sample=True,
        pad_token_id=self.tokenizer.eos_token_id,
        repetition_penalty=1.1,
        no_repeat_ngram_size=3,
        use_cache=True,
    )
    return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
