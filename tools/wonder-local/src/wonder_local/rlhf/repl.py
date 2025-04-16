import json
import re
import difflib
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from wonder_local.lib.modengine import ModularInferenceEngine
from wonder_local.lib.pretraining import (
    DataToSigilReviewCorpus,
    QuestionEntry,
    AnswerEntry,
    QuestionSet,
    SigilReviewCorpus,
)
from wonder_local.lib.repl import (
    InteractiveShell,
    ReplHeap,
    ReviewCommandSet,
    ReviewValidator,
)

def rlhf_repl(self, *args):
    self.logger.info(f"arguments: {args}")
    data_dir = args[0]
    self.logger.info(f"reading {data_dir} to find pretraining data")

    src = DataToSigilReviewCorpus(data=data_dir)
    count = src.length
    self.logger.info(f"discovered {count} question sets")

    shell = InteractiveShell(
        name="rlhf-review",

        # this will be overwritten by the interpreter object's commandset
        prompt_str="approve [y/n/q] > ",

        # this is essentially the state for the shell/interpreter
        heap=ReplHeap(questions=src.sets),

        # this is basically the interpreter itself
        interpreter=review_interpreter,

        # this gives the shell access to the ModularInferenceEngine
        modengine=self,
    )

    try:
        shell.run()
    except KeyboardInterrupt:
        self.logger.info("User quit early with Ctrl+C.")
        self.logger.info("Exiting repl shell via interrupt")

    self.logger.info("exiting repl shell")
    return

def review_interpreter(
    modengine: ModularInferenceEngine,
    heap: ReplHeap,
    session: PromptSession
):
    def approve_selected(question, response):
        selected = set(int(x.strip()) for x in response.split(","))
        question.approved = True
        question.answers = [
            a for idx, a in enumerate(question.answers, 1) if idx in selected
        ]

    def reject_selected(question, response):
        to_reject = set(int(x.strip()) for x in response[1:].split(","))
        question.approved = True
        question.answers = [
            a for idx, a in enumerate(question.answers, 1) if idx not in to_reject
        ]

    # see InteractiveShell for particulars. this structure represents the way this
    # interpreter runs and what each command actually does
    review_commands = [
        {"aliases": ["y", "yes"], "description": "approve all answers", "action": lambda q: setattr(q, "approved", True)},
        {"aliases": ["n", "no"], "description": "reject all answers", "action": lambda q: setattr(q, "approved", False)},
        {"aliases": ["q"], "description": "quit review", "action": "quit"},
        {"aliases": ["rq"], "description": "reject the question entirely", "action": lambda q: (setattr(q, "approved", False), q.answers.clear())},
        {"aliases": ["a"], "description": "approve question, skip answer review", "action": lambda q: setattr(q, "approved", True)},
        {"aliases": ["k"], "description": "skip this question", "action": "skip"},
        {"aliases": ["ks"], "description": "skip this entire question set", "action": "skip_set"},
        {"regex": r"\d+(?:\s*,\s*\d+)*", "text": "1,2,3", "description": "approve specific answers", "action": lambda q, r: approve_selected(q, r)},
        {"regex": r"!\d+(?:\s*,\s*\d+)*", "text": "!2,3", "description": "reject specific answers", "action": lambda q, r: reject_selected(q, r)},
    ]

    qsets = heap.get_tasks("questions")
    click.clear()

    # this becomes the main loop for the interpreter
    for i, qset in enumerate(qsets):
        click.secho(f"\n[Set {i+1}]", fg="white", bold=True)
        context = qset.get_context()
        click.secho(f"Reviewing file: {qset.filename}\n", fg="magenta")
        click.secho(f"Context:\n{context}\n", fg="cyan")

        if qset.reviewed:
            click.secho("  ✅ This question set has already been reviewed.", fg="green")
            if not click.confirm("Review again?", default=False):
                continue

        validator = ReviewValidator(ReviewCommandSet(review_commands))
        click.secho(f"{validator.usage_string()}\n", fg="green")

        skip_this_set = False

        # store the original state of the object so we can provide a diff to review
        # when the user is ready to write
        original_dump = json.dumps(qset.model_dump(), indent=2)

        for j, question in qset.iter_questions():
            click.secho(f"  [Question {j+1}] {question.question}", fg="cyan")
            click.secho("  Answers:", fg="magenta")
            for idx, ans in enumerate(question.answers):
                click.secho(f"    [{idx+1}] {ans}", fg="green")

            response = session.prompt(
                validator.prompt_string(),
                validator=validator,
                validate_while_typing=False,
            ).lower()

            handled = False
            for cmd in review_commands:
                if "aliases" in cmd and response in cmd["aliases"]:
                    action = cmd["action"]
                    if action == "quit":
                        modengine.logger.info("User quit early.")
                        return
                    elif action == "skip":
                        click.secho("  ⏭️  Skipped", fg="yellow")
                        handled = True
                        break
                    elif action == "skip_set":
                        click.secho("  ⏭️  Skipping entire set", fg="yellow")
                        skip_this_set = True
                        handled = True
                        break
                    else:
                        action(question)
                        click.secho(f"  ✅ {cmd['description'].capitalize()}", fg="green")
                        handled = True
                        break
                elif "regex" in cmd and re.fullmatch(cmd["regex"], response):
                    cmd["action"](question, response)
                    click.secho(f"  ✅ {cmd['description'].capitalize()}", fg="green")
                    handled = True
                    break

            if not handled:
                click.secho("  ❌ Unknown command.", fg="red")

            if skip_this_set:
                # pop out of the inner loop
                break

        if skip_this_set:
            continue

        # mark this set as reviewed as we've finished the set
        qset.reviewed = True

        # End of qset — show diff if changed
        new_dump = json.dumps(qset.model_dump(), indent=2)
        if new_dump != original_dump:
            if click.confirm("Changes detected. View diff?", default=False):
                diff = difflib.unified_diff(
                    original_dump.splitlines(),
                    new_dump.splitlines(),
                    fromfile="original",
                    tofile="modified",
                    lineterm=""
                )
                # go through the diff and pretty-print it like `git diff`
                for line in diff:
                    if line.startswith("+") and not line.startswith("+++"):
                        click.secho(line, fg="green")
                    elif line.startswith("-") and not line.startswith("---"):
                        click.secho(line, fg="red")
                    else:
                        click.echo(line)

            if click.confirm("Write changes to file?", default=True):
                try:
                    with open(qset.filename, "w") as f:
                        f.write(new_dump)
                    click.secho("  ✅ File saved.", fg="green")
                except Exception as e:
                    click.secho(f"  ❌ Failed to write file: {e}", fg="red")

        click.secho(f"Finished review of {qset.filename}\n", fg="green")
        click.clear()

    modengine.logger.debug("Exiting rlhf interpreter")

