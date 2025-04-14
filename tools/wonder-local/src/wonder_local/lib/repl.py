from typing import Callable, Any, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from wonder_local.lib.modengine import ModularInferenceEngine
import click
import json
import logging

# REPL heap is a structured, shared mutable context passed to interpreter logic
class ReplHeap(dict):
    # A shared mutable context for REPL sessions, passed into interpreters to provide state
    def get_tasks(self, key="questions"):
        return self.get(key, [])

class Encounter:
    def __init__(self, data: Any, validator: Optional[Callable[[Any], bool]] = None, logger: Optional[logging.Logger] = None):
        self.original = data
        self.current = data
        self.validator = validator
        self.logger = logger or logging.getLogger(__name__)

    def edit(self, validator: Optional[Callable[[Any], bool]] = None) -> bool:
        # open the user's $EDITOR with the data serialized as JSON
        edited = click.edit(json.dumps(self.current, indent=2))
        if not edited:
            return False
        try:
            parsed = json.loads(edited)
            if validator and not validator(parsed):
                raise ValueError("Custom validation failed")
            self.current = parsed
            return True
        except Exception as e:
            self.logger.error(f"❌ Validation error: {e}")
            return False

    def edit_json(self) -> bool:
        # edit assuming JSON structure, with built-in JSON validation
        return self.edit(validator=self.validator)


class YNQValidator(Validator):
    def validate(self, document):
        text = document.text.lower()
        if text not in ["y", "yes", "n", "no", "q"]:
            raise ValidationError(message="Please answer [y/n/q].")

class InteractiveShell:
    def __init__(
        self,
        modengine: ModularInferenceEngine,
        name: str = "wonder-repl",
        prompt_str: str = "> ",
        heap: Optional[ReplHeap] = None,
        interpreter: Optional[Callable[[Encounter], None]] = None
    ):
        self.name = name
        self.prompt_str = prompt_str
        self.session = PromptSession()
        self.heap = heap or ReplHeap()
        self.interpreter = interpreter or self.default_interpreter
        self.running = False
        self.modengine = modengine
        self.logger = modengine.logger

    def default_interpreter(self, encounter: Encounter):
        click.secho("Default interpreter. Override this.", fg="yellow")
        click.secho(str(encounter.current), fg="cyan")

    def run(self):
        self.running = True
        self.logger.info(f"{__name__} running shell")
        self.interpreter(self.modengine, self.heap, self.session)
