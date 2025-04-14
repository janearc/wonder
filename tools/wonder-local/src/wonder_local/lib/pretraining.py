from typing import List, Optional
from pathlib import Path
import json

from pydantic import BaseModel, Field


# Represents a single question and its associated metadata
class QuestionEntry(BaseModel):
    question: str = Field(
        ..., description="The instruction-style question generated from the context."
    )
    answers: List[str] = Field(
        ..., description="List of valid model-generated answers for this question."
    )
    synthesis_answer: str = Field(
        "",
        description="A distilled, high-quality response that accurately synthesizes the correct answer.",
    )
    approved: bool = Field(
        False,
        description="Whether this question has been approved for use in training.",
    )
    approved: bool = Field(
        False,
        description="Whether this question has been approved for use in training.",
    )


# Represents a set of related questions, all from a single context
class QuestionSet(BaseModel):
    context: str = Field(..., description="The full XML-encoded markdown context.")
    questions: List[QuestionEntry] = Field(
        ..., description="A list of question entries generated from the context."
    )
    filename: Optional[str] = Field(
        None, description="The source filename of the question set (for tracking)."
    )
    reviewed: bool = Field(
        False, description="Whether this question set has been reviewed."
    )

    # Alternate constructor for creating a QuestionSet from raw data
    @classmethod
    def from_context_and_answers(cls, context: str, qa_dict: dict) -> "QuestionSet":
        question_entries = []
        for question, answers in qa_dict.items():
            question_entries.append(
                QuestionEntry(
                    question=question,
                    answers=answers,
                    synthesis_answer="",  # to be filled later, possibly by a model
                )
            )
        return cls(context=context, questions=question_entries)

    # Property that returns number of questions in this set
    @property
    def question_count(self) -> int:
        return len(self.questions)

    # Property that returns total number of answers in this set
    @property
    def answer_count(self) -> int:
        return sum(len(q.answers) for q in self.questions)

    # Retrieves a specific question
    def get_question(self, index: int) -> QuestionEntry:
        return self.questions[index]

    # Marks a specific question as approved or not
    def set_approval(self, index: int, approved: bool):
        self.questions[index].approved = approved

    # Returns the context text
    def get_context(self) -> str:
        return self.context

    # Returns all answers associated with a specific question
    def get_answers(self, index: int) -> List[str]:
        return self.questions[index].answers

    # Return an iterable of (index, question) pairs for convenience
    def iter_questions(self):
        return enumerate(self.questions)


# Container for a full set of question sets
class SigilReviewCorpus(BaseModel):
    sets: List[QuestionSet] = Field(..., description="All question sets for review.")

    # Total number of questions across all sets
    @property
    def total_questions(self) -> int:
        return sum(qset.question_count for qset in self.sets)

    # Total number of answers across all sets
    @property
    def total_answers(self) -> int:
        return sum(qset.answer_count for qset in self.sets)

    # Number of question sets loaded
    @property
    def length(self) -> int:
        return len(self.sets)

    # Removes and returns the first QuestionSet
    def pop(self) -> QuestionSet:
        return self.sets.pop(0)

    # Adds a QuestionSet to the end
    def push(self, qset: QuestionSet):
        self.sets.append(qset)

    # Returns all QuestionSets
    def qsets(self) -> List[QuestionSet]:
        return self.sets

    # only return questionsets that have not been reviewed
    def qsets_to_review(self) -> List[QuestionSet]:
        return [qset for qset in self.sets if not qset.reviewed]

    # only return questionsets that have not been approved
    def qsets_not_approved(self) -> List[QuestionSet]:
        return [
            qset for qset in self.sets if not all(q.approved for q in qset.questions)
        ]


# Reads all -review.json files from a directory and returns a populated SigilReviewCorpus
def DataToSigilReviewCorpus(data: str) -> SigilReviewCorpus:
    root = Path(data)
    files = root.glob("**/*-review.json")
    question_sets = []

    for file in files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
                qset = QuestionSet(**data)
                qset.filename = str(file)
                question_sets.append(qset)
        except Exception as e:
            raise RuntimeError(f"Failed to load {file}: {e}")

    return SigilReviewCorpus(sets=question_sets)
