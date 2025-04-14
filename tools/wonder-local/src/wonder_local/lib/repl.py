from typing import Callable, Any, Optional, Union, List
from prompt_toolkit import PromptSession
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from wonder_local.lib.modengine import ModularInferenceEngine
import click
import json
import logging
import re


# REPL heap is a structured, shared mutable context passed to interpreter logic
class ReplHeap(dict):
    # A shared mutable context for REPL sessions, passed into interpreters to provide state
    def get_tasks(self, key="questions"):
        return self.get(key, [])


class Encounter:
    def __init__(
        self,
        data: Any,
        validator: Optional[Callable[[Any], bool]] = None,
        logger: Optional[logging.Logger] = None,
    ):
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

# this is a class that describes both the inputs and the validation for the inputs
# and which incidentally can create a usage string and a prompt string
# because thats borat very nice dot swf
class ReviewCommandSet:
    def __init__(self, commands: List[dict]):
        self.commands = commands

    def match(self, text: str) -> Optional[dict]:
        text = text.strip().lower()
        for cmd in self.commands:
            if "aliases" in cmd and text in cmd["aliases"]:
                return cmd
            if "regex" in cmd and re.fullmatch(cmd["regex"], text):
                return cmd
        return None

    def validate(self, text: str):
        if not self.match(text):
            raise ValidationError(message=self.error_message())

    def execute(self, question, response: str):
        cmd = self.match(response)
        if not cmd:
            raise ValueError("Invalid command")

        action = cmd.get("action")
        if callable(action):
            return action(question, response) if "regex" in cmd else action(question)
        return action  # e.g., "skip", "quit"

    def prompt_string(self) -> str:
        fragments = []
        for cmd in self.commands:
            if "aliases" in cmd:
                fragments.append(cmd["aliases"][0])
            elif "text" in cmd:
                fragments.append(cmd["text"])
            elif "regex" in cmd:
                fragments.append(cmd["regex"])
        return f"[{', '.join(fragments)}]"

    def usage_string(self) -> str:
        lines = ["Usage:"]
        for cmd in self.commands:
            if "aliases" in cmd:
                label = "/".join(cmd["aliases"])
            elif "text" in cmd:
                label = cmd["text"]
            elif "regex" in cmd:
                label = cmd["regex"]
            else:
                label = "<?>"
            lines.append(f"* {label} = {cmd['description']}")
        return "\n".join(lines)

    def is_valid(self, text: str) -> bool:
        return self.match(text) is not None

# a pretty burly validator class that is used for rlhf which is a very special kind of validator
class ReviewValidator(Validator):
    def __init__(self, review_commands):
        super().__init__()
        self.review_commandset = review_commands

    def validate(self, document):
        text = document.text.strip().lower()
        if self.review_commandset.is_valid(text):
            return
        raise ValidationError(message=self._error_message())

    def _error_message(self):
        lines = ["Invalid input.", "Valid options:"]
        for label, desc in self.review_commandset.get_descriptions():
            lines.append(f"  {label:14} → {desc}")
        return "\n".join(lines)

    def prompt_string(self):
        return self.review_commandset.prompt_string()

    def usage_string(self):
        return self.review_commandset.usage_string()

# very basic validator class
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
        interpreter: Optional[Callable[[Encounter], None]] = None,
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
