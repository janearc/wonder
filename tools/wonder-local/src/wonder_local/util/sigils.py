import os
from pathlib import Path
from wonder_local.lib.all_sigils import list_sigil_files

def sigils(self, *args):
    sigil_path = args[0] if args else None

    if not sigil_path:
        self.logger.debug("No explicit path provided, using config defaults")
        sigil_path = self.config.get("sigils", {}).get("default_path")

    if not sigil_path or not Path(sigil_path).exists():
        self.logger.warning("Supplied or config-defined sigil path not readable, falling back")
        sigil_path = Path(os.environ["WONDER_ROOT"]) / "sigil"

        if not sigil_path.exists():
            raise RuntimeError("No suitable path available for sigil discovery")

    sigil_files = list_sigil_files(Path(sigil_path))
    for s in sigil_files:
        self.logger.info(f"Sigil located: {s}")

    return
