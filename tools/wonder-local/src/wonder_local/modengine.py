import importlib
import yaml
import sys
import torch
import logging
from rich.logging import RichHandler
import os
from pathlib import Path
from types import MethodType
from rich.console import Console

# we only use this outside the engine
console = Console()

MODULE_CONFIG_PATH = Path(__file__).parent / "modules.yaml"

class ModularInferenceEngine:
    def __init__(self):
        self.modules = {}
        self._method_config = {}
        self._invoked = set()
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = None

        """create a general logging facility"""
        DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
        if not logger.handlers:
            handler = RichHandler(markup=True, rich_tracebacks=True)
            logger.addHandler(handler)

        self.logger = logger

        """this needs to be the last call in __init__"""
        self._load_modules()

    """create a basic model config for any targets that want it done for them"""
    def default_engine(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
    
        self.model_name = "microsoft/phi-2"
        self.logger.info("[cyan]Loading default model:[/cyan] %s", self.model_name)
    
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
    
        if torch.backends.mps.is_available():
            self.device = "mps"
            self.model.to("mps")
            self.logger.debug("[green]Model moved to GPU (MPS).[/green]")
        else:
            self.device = "cpu"
            self.model.to("cpu")
            self.logger.debug("[yellow]MPS not available, using CPU instead.[/yellow]")
    
        self.logger.info("[bold green]🔧 ModularInferenceEngine is live on device:[/bold green] %s", self.device)

    def _load_modules(self):
        if not MODULE_CONFIG_PATH.exists():
            raise FileNotFoundError(f"Could not find {MODULE_CONFIG_PATH}")

        with open(MODULE_CONFIG_PATH, "r") as f:
            module_map = yaml.safe_load(f)

        for method_name, meta in module_map.items():
            try:
                module_path, func_name = meta["path"].rsplit(".", 1)
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)

                self.logger.debug("Loading [bold]%s[/bold] — object_method=[bold]%s[/bold]", method_name, meta.get('object_method', True))
                self.logger.debug("Resolved function: %s", func)

                self._method_config[method_name] = meta

                if meta.get("object_method", True):
                    bound_method = MethodType(func, self)
                    setattr(self, method_name, bound_method)
                    bound = getattr(self, method_name)
                    self.logger.debug("→ %s is type: %s | callable? %s", method_name, type(bound), callable(bound))
                    self.logger.debug("bound %s as object method → %s", method_name, getattr(self, method_name))
                else:
                    setattr(self, method_name, func)
                    bound = getattr(self, method_name)
                    self.logger.debug("→ %s is type: %s | callable? %s", method_name, type(bound), callable(bound))
                    self.logger.debug("bound %s as utility method → %s", method_name, getattr(self, method_name))

                self.modules[method_name] = meta
                self.logger.info("[cyan]✓ Loaded method:[/cyan] %s ← %s", method_name, meta['path'])
            except Exception as e:
                self.logger.warn("[red]✗ Failed to load %s from %s → %s[/red]", method_name, meta['path'], e)

    def status(self):
        self.logger.info("[bold magenta]🕭 Modular Engine Status:[/bold magenta]")
        self.logger.info("Model name: [green]%s[/green]", self.model_name)
        self.logger.info("Loaded modules:")
        for name, meta in self.modules.items():
            deps = meta.get("requires", [])
            dep_note = f"(requires: {', '.join(deps)})" if deps else ""
            self.logger.info("  %-20s ← %s %s", name, meta["path"], dep_note)

    def invoke(self, method_name, args):
        if method_name not in self.modules:
            self.logger.warn("[red]✗ Method '%s' not found[/red]", method_name)
            self.status()
            return

        if method_name in self._invoked:
            return  # Already called

        for dep in self.modules[method_name].get("requires", []):
            if dep in self._invoked:
                continue
            self.logger.debug("Invoking dependency '%s' from '%s'", dep, method_name)
            # Special case: forward args (like prompt) for estimate
            if dep == "estimate" and args:
                self.invoke(dep, [args[0]])
            else:
                self.invoke(dep, [])

        method = getattr(self, method_name)
        self.logger.debug("Invoking method '%s' with args: %s", method_name, args)
        result = method(*args)
        self._invoked.add(method_name)
        return result

if __name__ == "__main__":
    engine = ModularInferenceEngine()

    if len(sys.argv) == 1:
        engine.status()
        sys.exit(0)

    method_name = sys.argv[1]
    args = sys.argv[2:]

    try:
        result = engine.invoke(method_name, args)
        if result is not None:
            print(result)
    except Exception as e:
        console.print(f"[red]✗ Error during '{method_name}': {e}[/red]")
