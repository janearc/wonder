import torch


def generate(self, *args) -> str:
    # Ensure a prompt was passed
    if not args:
        raise ValueError("Prompt required for generation.")

    # Combine all positional arguments into a single prompt string
    prompt = " ".join(args)

    # Use configured default model name if none explicitly provided
    default_model = self.config.get("load_model", {}).get(
        "default_model", "microsoft/phi-2"
    )

    # Ensure the model and tokenizer are loaded and ready
    self.model = self.invoke("load_model", default_model)

    if not self.model or not self.tokenizer:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    # Dynamically estimate the ideal max length for the response
    max_length = self.invoke("estimate", prompt)

    # Tokenize input and move to correct device
    inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

    # Generate a response using sampling with top-p and top-k constraints
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

    # Decode the output into a clean string and return
    return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
