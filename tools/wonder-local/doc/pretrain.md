# pretraining todo

- define the schema and document
- create `md_to_question_update` and `md_to_question_update_all` targets
- create a manual-review for thumbs-up/thumbs-down on pretraining guidance
- determine a way to build the synthesis answer
- determine the way to feed pretraining questions to a model resulting in
  training outputs on disk
- use taxonometry to determine the difference in performance between
  the un-trained version of the model and the trained version of the model
- add the benchmark data into the pretraining data
- see if we can use taxonometry benchmark data to specifically shape llm
  performance

- actually write this document

## synthesis answer generation and validation

### what is a synthesis answer?

a synthesis answer is a human- or model-generated summary of multiple valid answers
to a question. it is intended to consolidate semantically similar responses into a
single, legible representation of understanding. synthesis answers serve both as a
training target and a measure of alignment and clarity.

### synthesis answer pipeline (proposed)

1. **generate multiple answers per question**
   - answers are either extracted from the text directly or proposed by a model.
   - each answer is validated through human review or acceptance criteria.

2. **generate synthesis**
   - using the accepted answers, generate a concise synthesis that captures shared meaning.
   - this can be done manually or via a summarization-capable model (e.g., flan-t5 or llama3).

3. **validate synthesis**
   - **invert** the synthesis: instruct a model to turn it back into a question.
   - **regenerate**: ask that question using the original passage as context.
   - **compare**: the regenerated answer should closely match the original synthesis.
     - high similarity indicates legibility and alignment.
     - divergence indicates the synthesis was unclear, compressed, or overfitted.

4. **store and log**
   - if validated, include the synthesis in the pretraining record.
   - log alignment confidence (e.g., similarity score, round-trip agreement).

this approach makes synthesis answers *proof-carrying knowledge artifacts*—they're not just
compressed summaries, they're validated by the very same model they'll train.
