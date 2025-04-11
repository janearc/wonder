import os
import sys
import importlib
import inspect
import logging
from rich.logging import RichHandler
from rich.console import Console
from wonder_local.config.modules import MODULE_CONFIG

console = Console()

class ModularInferenceEngine:
    def __init__(self):
        self.modules = {}
        self._method_config = {}
        self._invoked = set()
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = None
        self.config = MODULE_CONFIG

        """create a general logging facility"""
        DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
        if not logger.handlers:
            handler = RichHandler(markup=True, rich_tracebacks=True)
            handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
            logger.debug(f"DEBUG_MODE is {DEBUG_MODE}")
            logger.debug(f"Logger level: {logger.level}, Handler level: {handler.level}")
            logger.addHandler(handler)

        self.logger = logger

        self._load_modules()

    def _load_modules(self):
        for name, meta in MODULE_CONFIG.items():
            path = meta["path"]
            object_method = meta.get("object_method", True)
            llamalike = meta.get("llamalike", False)
            module_path, func_name = path.rsplit(".", 1)

            try:
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)
                bound = func.__get__(self) if object_method else func

                self.modules[name] = bound
                self._method_config[name] = {
                    "path": path,
                    "object_method": object_method,
                    "llamalike": llamalike,
                    "requires": meta.get("requires", [])
                }

                self.logger.info("\u2713 Loaded method: %s \u2190 %s", name, path)

            except (ImportError, AttributeError) as e:
                self.logger.error("Failed to load method %s from %s: %s", name, path, e)

    def status(self):
        self.logger.info("[bold magenta]\U0001F56D Modular Engine Status:[/bold magenta]")
        self.logger.info("Model name: [green]%s[/green]", self.model_name)
        self.logger.info("Loaded modules:")
        for name, config in self._method_config.items():
            deps = config.get("requires", [])
            dep_note = f"(requires: {', '.join(deps)})" if deps else ""
            self.logger.info("  %-20s \u2190 %s %s", name, config["path"], dep_note)

    def invoke(self, method_name, *args):
        if method_name not in self.modules:
            self.logger.warning("[red]\u2717 Method '%s' not found[/red]", method_name)
            self.status()
            raise ValueError(f"Unknown method: {method_name}")

        self.logger.debug("Invoking method '%s' with args: %s", method_name, args)
        result = self.modules[method_name](*args)
        self._invoked.add(method_name)
        return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python modengine.py <method> [args...]")
        sys.exit(1)

    engine = ModularInferenceEngine()
    method = sys.argv[1]
    args = sys.argv[2:]

    try:
        result = engine.invoke(method, *args)
        if result is not None:
            print(result)
    except Exception as e:
        console.print(f"\u2717 Error during '{method}': {e}", style="bold red")
