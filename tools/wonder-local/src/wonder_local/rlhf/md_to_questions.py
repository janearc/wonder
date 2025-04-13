import json
from functools import lru_cache
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from wonder_local.lib.benchmark import Benchmark
from wonder_local.lib.markdown_xml import markdown_to_xml
from wonder_local.lib.pretraining import QuestionEntry, QuestionSet
from wonder_local.lib.all_sigils import list_sigil_files

@lru_cache(maxsize=1)
def get_tokenizer_and_model():
    # TODO: i'm not sure we can change this given the specificity of our prompts below
    #       but i very much would prefer to
    # TODO: be more flexible about this in the future, but flan is nice enough for now.
    model_name = "google/flan-t5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    model.eval()
    return tokenizer, model

def md_to_questions(self, file_path: str):
    try:
        with open(file_path, "r") as f:
            md = f.read()
    except Exception as e:
        self.logger.error(f"❌ Failed to read file '{file_path}': {e}")
        return

    root = markdown_to_xml(md)
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]
    context = "\n\n".join(paragraphs)

    # Dynamically estimate the ideal max length for the response
    input_length = self.invoke("estimate", context)

    tokenizer, model = get_tokenizer_and_model()

    # this is a hard limit in flan, we'll probably do this more gracefully in the future
    max_input_length = 512

    if input_length > max_input_length:
        self.logger.warning(
            f"⚠️ Skipping file '{file_path}': context too long ({input_length} > {max_input_length})"
        )
        return

    # we're using this prompt for flan to derive questions from the provided context
    # which can then be subsequently answered by flan, and used in training other models
    # through the use of outputted normalized json question/answer/synthesis objects
    question_prompt = (
        "Identify three distinct concepts discussed in the following paragraph. "
        "For each concept, generate one instruct-style question that would help a model understand "
        "its meaning and how it relates to the other two concepts. Prefix each question with 'Q>' on a new line.\n\n"
        f"Paragraph: {context}"
    )

    benchmark = Benchmark(label="md_to_questions", input_tokens=input_length)
    benchmark.start()

    unique_questions = set()
    question_attempts = 0

    # we are going to ask the model to generate questions for us (prompt above) until
    # we don't get any new questions. this allows it to process the context a sufficient
    # number of times that nuance in meaning can emerge rather than just saying "what is this?"
    while True:
        inputs = tokenizer(question_prompt, return_tensors="pt")

        # these variables were arrived at through trial and error and seem to work
        # well enough for flan, but probably won't work well for other models. they
        # may need to be modified if we move away from flan or the model seems
        # too lazy or too spicy.
        outputs = model.generate(
            **inputs,
            max_length=input_length,
            temperature=0.8,
            top_p=0.95,
            top_k=75,
            do_sample=True,
            num_return_sequences=1,
        )
        questions_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        raw_questions = re.split(r"[Qq]?>", questions_text)

        # find legitimate questions and toss the ones that are bogus
        parsed_questions = [
            re.sub(r"^\s*\d+\.?\s*", "", q).strip()
            for q in raw_questions
            if q.strip() and q.strip().endswith("?")
        ]

        prev_len = len(unique_questions)
        unique_questions.update(parsed_questions)
        question_attempts += 1
        if len(unique_questions) == prev_len or question_attempts >= 10:
            break

    answers = {}
    total_output_tokens = 0
    for question in unique_questions:
        sub_prompt = f"{question} Answer based only on this context:\n\n{context}"
        answer_set = set()
        answer_attempts = 0

        # generate a set of answers for each question we have derived from the
        # original context provided
        while True:
            input_ids = tokenizer(sub_prompt, return_tensors="pt")

            # these variables were arrived at through trial and error and seem to work
            # well enough for flan, but probably won't work well for other models. they
            # may need to be modified if we move away from flan or the model seems
            # too lazy or too spicy.
            output = model.generate(
                **input_ids,
                max_length=384,
                temperature=0.9,
                top_p=0.95,
                top_k=100,
                do_sample=True,
                num_return_sequences=1,
            )
            answer = (
                tokenizer.decode(output[0], skip_special_tokens=True).strip().lower()
            )
            total_output_tokens += len(tokenizer(answer).input_ids)
            prev_len = len(answer_set)
            answer_set.add(answer)
            answer_attempts += 1
            if len(answer_set) == prev_len or answer_attempts >= 5:
                break

        answers[question] = list(answer_set)

    benchmark.output_tokens = total_output_tokens
    benchmark.stop()

    question_entries = [
        QuestionEntry(question=q, answers=a, approved=False) for q, a in answers.items()
    ]
    question_set = QuestionSet(context=context, questions=question_entries)

    sigil_name = Path(file_path).stem
    out_path = Path("data/rlhf/sigil/instruction")
    out_path.mkdir(parents=True, exist_ok=True)
    try:
        with open(out_path / f"{sigil_name}-review.json", "w") as f:
            json.dump(question_set.model_dump(), f, indent=2)
    except Exception as e:
        self.logger.error(f"❌ Failed to write file '{sigil_name}-review.json': {e}")
        return

    self.logger.info("\n[📚] QA Extraction Complete")
    self.logger.info("\n[❓] Questions and Answers:")
    for q, a_list in answers.items():
        self.logger.debug(f"\nQ: {q}")
        for a in a_list:
            self.logger.debug(f" - {a}")

    benchmark.report()

    num_qs = question_set.question_count
    num_as = question_set.answer_count
    self.logger.info(
        f"\n[❓] Generated {num_qs} questions with {num_as} answers for approval."
    )

def md_to_questions_all(self, sigil_path: str):

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

        # no return value, logs and writes to disk. this function also does error
        # handling around file access so we don't have to
        # self.logger.info(f"sending sigil {s} to pretrainer")
        md_to_questions(self, s)


# i think the below can be omitted because we handle this in modengine
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python modengine.py md_to_questions <markdown_file>")
        sys.exit(1)

    command = sys.argv[1]
    path = sys.argv[2]

    if command == "md_to_questions":
        md_to_questions(path)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
