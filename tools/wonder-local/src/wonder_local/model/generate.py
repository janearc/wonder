from rich.console import Console
import torch

console = Console()

def generate(self, *args) -> str:
    if not args:
        raise ValueError("Prompt required for generation.")

    prompt = " ".join(args)

    default_model = self.config.get("load_model", {}).get("default_model", "microsoft/phi-2")
    self.model = self.invoke("load_model", default_model)

    if not self.model or not self.tokenizer:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    """try to figure out what the max length of response should be"""
    max_length = self.invoke("estimate", prompt)

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

