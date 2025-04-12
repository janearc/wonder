from typing import List
from pydantic import BaseModel, Field

class QuestionEntry(BaseModel):
    question: str = Field(..., description="The instruction-style question generated from the context.")
    answers: List[str] = Field(..., description="List of valid model-generated answers for this question.")
    synthesis_answer: str = Field("", description="A distilled, high-quality response that accurately synthesizes the correct answer.")
    approved: bool = Field(False, description="Whether this question has been approved for use in training.")


class QuestionSet(BaseModel):
    context: str = Field(..., description="The full XML-encoded markdown context.")
    questions: List[QuestionEntry] = Field(..., description="A list of question entries generated from the context.")

    @classmethod
    def from_context_and_answers(cls, context: str, qa_dict: dict) -> "QASet":
        question_entries = []
        for question, answers in qa_dict.items():
            question_entries.append(QuestionEntry(
                question=question,
                answers=answers,
                synthesis_answer=""  # to be filled later, possibly by a model
            ))
        return cls(context=context, questions=question_entries)

    @property
    def question_count(self) -> int:
        return len(self.questions)

    @property
    def answer_count(self) -> int:
        return sum(len(q.answers) for q in self.questions)

