import sys
import torch
import xml.etree.ElementTree as ET
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from wonder_local.lib.markdown_xml import markdown_to_xml
from wonder_local.lib.benchmark import Benchmark


def md_to_questions(self, file_path: str):
    with open(file_path, "r") as f:
        md = f.read()

    root = markdown_to_xml(md)
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]
    context = "\n\n".join(paragraphs)

    # Dynamically estimate the ideal max length for the response
    input_length = self.invoke("estimate", context)
    max_input_length = 512  # for flan-t5-large

    if input_length > max_input_length:
        self.logger.warning(f"⚠️ Skipping file '{file_path}': context too long ({input_length} > {max_input_length})")
        return

    model_name = "google/flan-t5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

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
    while True:
        inputs = tokenizer(question_prompt, return_tensors="pt")
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
        parsed_questions = [re.sub(r"^\s*\d+\.?\s*", "", q).strip() for q in raw_questions if q.strip()]
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
        while True:
            input_ids = tokenizer(sub_prompt, return_tensors="pt")
            output = model.generate(
                **input_ids,
                max_length=384,
                temperature=0.9,
                top_p=0.95,
                top_k=100,
                do_sample=True,
                num_return_sequences=1,
            )
            answer = tokenizer.decode(output[0], skip_special_tokens=True).strip().lower()
            total_output_tokens += len(tokenizer(answer).input_ids)
            prev_len = len(answer_set)
            answer_set.add(answer)
            answer_attempts += 1
            if len(answer_set) == prev_len or answer_attempts >= 5:
                break
        answers[question] = list(answer_set)

    benchmark.output_tokens = total_output_tokens
    benchmark.stop()

    print("\n[📚] QA Extraction Complete")
    print("\n[❓] Questions and Answers:")
    for q, a_list in answers.items():
        print(f"\nQ: {q}")
        for a in a_list:
            print(f" - {a}")

    benchmark.report()


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
