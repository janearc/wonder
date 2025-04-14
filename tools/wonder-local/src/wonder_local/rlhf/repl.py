from prompt_toolkit import PromptSession
from pathlib import Path
import json
import click
from wonder_local.lib.repl import InteractiveShell, ReplHeap, YNQValidator
from wonder_local.lib.modengine import ModularInferenceEngine
from wonder_local.lib.pretraining import QuestionEntry, QuestionSet, DataToSigilReviewCorpus, SigilReviewCorpus

def rlhf_repl(self, *args):
    self.logger.info(f"arguments: {args}")
    data_dir = args[0]
    self.logger.info(f"reading {data_dir} to find pretraining data")

    src = DataToSigilReviewCorpus(data=data_dir)
    count = src.length
    self.logger.info(f"discovered {count} question sets")

    shell = InteractiveShell(
        name="rlhf-review",
        prompt_str="approve [y/n/q] > ",
        heap=ReplHeap(questions=src.sets),
        interpreter=review_interpreter,
        modengine=self
    )

    shell.run()

    self.logger.info("exiting repl shell")

    return
def review_interpreter(modengine: ModularInferenceEngine, heap: ReplHeap, session: PromptSession):
    modengine.logger.info(f"Entering interpreter {__name__}")
    prompt_str = "approve [y/n/q] > "

    qsets = heap.get_tasks("questions")
    modengine.logger.debug(f"Processing {len(qsets)} question sets for review")

    for i, qset in enumerate(qsets):
        click.secho(f"\n[Set {i+1}]", fg="white", bold=True)
        context = qset.get_context()
        click.secho(f"Context:\n{context}\n", fg="cyan")

        for j, question in qset.iter_questions():
            click.secho(f"  [Question {j+1}] {question.question}", fg="blue")
            click.secho("  Answers:", fg="magenta")
            for ans in question.answers:
                click.secho(f"    - {ans}", fg="green")

            response = session.prompt(prompt_str, validator=YNQValidator(), validate_while_typing=False).lower()

            if response in ["y", "yes"]:
                question.approved = True
                click.secho("  ✅ Approved", fg="green")
            elif response in ["n", "no"]:
                question.approved = False
                click.secho("  ❌ Rejected", fg="red")
            elif response == "q":
                modengine.logger.info("User quit early.")
                return

    modengine.logger.debug("Exiting rlhf interpreter")

