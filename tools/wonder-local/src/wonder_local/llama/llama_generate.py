import os
from pathlib import Path
from rich.console import Console
from llama_cpp import Llama

console = Console()

def llama_generate(self, *args):
    import ctypes
    from llama_cpp import llama_log_set
    llama_log_set(None, ctypes.c_void_p(0)) # thanks, but no my dude

    if not args:
        raise ValueError("Prompt required for llama_generate.")

    prompt = " ".join(args)

    # Default path to the TinyLlama GGUF model
    default_model_path = Path.home() / "Models" / "tinyllama" / "tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    model_path = os.getenv("LLAMA_MODEL_PATH", str(default_model_path))

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model not found at: {model_path}")

    self.logger.info(f"[cyan]Running llama.cpp inference with model:[/cyan] {model_path}")

    try:
        # Initialize the model (only once per session ideally)
        if not hasattr(self, "llama") or self.llama is None:
            self.llama = Llama(
              model_path=str(model_path),
              n_ctx=512,
              n_threads=6,
              verbose=False
            )

        output = self.llama(prompt, max_tokens=256, stop=["</s>"])
        return output["choices"][0]["text"].strip()

    except Exception as e:
        self.logger.error(f"[red]LLaMA inference failed:[/red] {e}")
        raise

