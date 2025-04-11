import yaml
from pathlib import Path

module_yaml = Path(__file__).with_name("modules.yaml")

with open(module_yaml, "r", encoding="utf-8") as f:
    MODULE_CONFIG = yaml.safe_load(f)
