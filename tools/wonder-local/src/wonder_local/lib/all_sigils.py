import os
from pathlib import Path


def list_sigil_files(root: Path | None = None) -> list[Path]:
    if root is None:
        root = Path(os.environ["WONDER_ROOT"]) / "sigil"
    return sorted(root.rglob("*.md"))
