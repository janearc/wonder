from typing import Callable, Any, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import prompt
from wonder_local.modengine import ModularInferenceEngine
from pydantic import BaseModel
import click
import json


class Encounter:
    def __init__(self, data: Any, logger, validator: Optional[Callable[[Any], bool]] = None):
        if not logger:
            raise RuntimeError("Logger is required for Encounter")
        self.original = data
        self.current = data
        self.logger = logger
        self.validator = validator

    def edit(self, parser: Optional[Callable[[str], Any]] = None) -> bool:
        edited = click.edit(json.dumps(self.current, indent=2) if parser == json.loads else str(self.current))
        if not edited:
            return False
        try:
            parsed = parser(edited) if parser else edited
            if self.validator and not self.validator(parsed):
                raise ValueError("Custom validation failed")
            self.current = parsed
            return True
        except Exception as e:
            self.logger.error(f"❌ Validation error: {e}")
            return False

    def edit_json(self) -> bool:
        return self.edit(parser=json.loads)


class InteractiveShell:
    def __init__(
        self,
        modengine: ModularInferenceEngine,
        name: str = "wonder-repl",
        prompt_str: str = "> ",
        heap: list = None,
        interpreter: Optional[Callable[[Encounter], None]] = None,
    ):
        self.name = name
        self.prompt_str = prompt_str
        self.session = PromptSession()
        self.heap = heap or []
        self.interpreter = interpreter or self.default_interpreter
        self.running = False
        self.logger = modengine.logger

    def default_interpreter(self, encounter: Encounter):
        click.echo("Default interpreter. Override this.")
        click.echo(str(encounter.current))

    def run(self):
        self.running = True
        self.logger.info(f"{__name__} running shell")
        while self.heap:
            item = self.heap.pop(0)
            encounter = Encounter(item, logger=self.logger)
            self.interpreter(encounter)
            while True:
                answer = self.session.prompt(self.prompt_str)
                if answer.lower() in ["y", "yes"]:
                    click.echo("✅ Committed.")
                    break
                elif answer.lower() in ["n", "no"]:
                    if encounter.edit_json():
                        continue
                    else:
                        click.echo("Aborting edit.")
                elif answer.lower() == "q":
                    self.running = False
                    return
                else:
                    click.echo("Please answer [y/n/q].")

