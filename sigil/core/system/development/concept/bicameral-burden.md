# Token Burden

**Token burden** is the cumulative cost of maintaining a body of information
within an LLM's context window. It represents the tradeoff between depth of
information and runtime coherence.

Each word, phrase, or sigil occupies a portion of the model's limited token
budget. As more tokens accumulate, the model's ability to retain, recall, or
respond coherently may degrade due to overflow, pruning, or compression. As
this coherence degrades, a model may be unable to respond or interact at all
and will consistently and irretrievably hallucinate; once a maximum token 
burden has been reached, the session is fundamentally corrupt and must be
discarded.

Token burden is not fixed—it varies depending on how the model loads,
organizes, and stores information internally. Efficient conceptual mapping
and compression may reduce effective burden, while naive ingestion or full
buffet loading may increase it dramatically.

Token burden is a fundamental constraint. It cannot be escaped, but it can be
managed through careful kernel design, dynamic loading strategies, and
token-efficient representation.

It is especially critical in bicameral systems, where humans benefit from
expressive language while LLMs require tightly scoped input to remain coherent.
