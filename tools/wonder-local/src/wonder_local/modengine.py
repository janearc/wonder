import importlib
import yaml
import sys
from pathlib import Path
from types import MethodType
from rich.console import Console

console = Console()
MODULE_CONFIG_PATH = Path(__file__).parent / "modules.yaml"

class ModularInferenceEngine:
    def __init__(self, model_name: str = "microsoft/phi-2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self.modules = {}
        self._method_config = {}
        self._invoked = set()
        console.print(f"[bold green]🔧 ModularInferenceEngine is live on device:[/bold green] {self.device}")
        self._load_modules()

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

                console.print(f"[blue][DEBUG][/blue] Loading [bold]{method_name}[/bold] — object_method=[bold]{meta.get('object_method', True)}[/bold]")
                console.print(f"[blue][DEBUG][/blue] Resolved function: [green]{func}[/green]")

                self._method_config[method_name] = meta

                if meta.get("object_method", True):
                    bound_method = MethodType(func, self)
                    setattr(self, method_name, bound_method)
                    bound = getattr(self, method_name)
                    console.print(f"[bold blue]→ {method_name} is type:[/bold blue] {type(bound)} | callable? {callable(bound)}")
                    console.print(f"[blue][DEBUG][/blue] Bound [bold]{method_name}[/bold] as object method → [cyan]{getattr(self, method_name)}[/cyan]")
                else:
                    setattr(self, method_name, func)
                    bound = getattr(self, method_name)
                    console.print(f"[bold blue]→ {method_name} is type:[/bold blue] {type(bound)} | callable? {callable(bound)}")
                    console.print(f"[blue][DEBUG][/blue] Bound [bold]{method_name}[/bold] as static method → [cyan]{getattr(self, method_name)}[/cyan]")

                self.modules[method_name] = meta
                console.print(f"[cyan]✓ Loaded method:[/cyan] {method_name} ← {meta['path']}")
            except Exception as e:
                console.print(f"[red]✗ Failed to load {method_name} from {meta['path']} → {e}[/red]")

    def status(self):
        console.print("\n[bold magenta]🕭 Modular Engine Status:[/bold magenta]")
        console.print(f"Model name: [green]{self.model_name}[/green]")
        console.print("Loaded modules:")
        for name, meta in self.modules.items():
            deps = meta.get("requires", [])
            dep_note = f"(requires: {', '.join(deps)})" if deps else ""
            console.print(f"  [yellow]{name}[/yellow] ← {meta['path']} {dep_note}")

    def invoke(self, method_name, args):
        if method_name not in self.modules:
            console.print(f"[red]✗ Method '{method_name}' not found[/red]")
            self.status()
            return

        if method_name in self._invoked:
            return  # Already called

        for dep in self.modules[method_name].get("requires", []):
            if dep in self._invoked:
                continue
            console.print(f"[DEBUG] Invoking dependency '{dep}' from '{method_name}'")
            # Special case: forward args (like prompt) for estimate
            if dep == "estimate" and args:
                self.invoke(dep, [args[0]])
            else:
                self.invoke(dep, [])

        method = getattr(self, method_name)
        console.print(f"[DEBUG] Invoking method '{method_name}' with args: {args}")
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
