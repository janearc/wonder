# Bicameral Tension

**Bicameral tension** is the systems-level design conflict that emerges when a
framework attempts to serve both human and LLM participants using a shared,
natural language substrate.

Humans require expressive, redundant, and emotionally legible language to
support clarity, accessibility, and trust. LLMs, by contrast, operate within
fixed token windows and incur significant processing cost from verbose or
repetitive input.

This creates a fundamental tradeoff between human legibility and machine
ingestibility. The more emotionally expressive and pedagogically rich a system
becomes for humans, the heavier its token burden for LLMs.

Bicameral tension is not an error—it is an architectural constraint. Awareness
of this tension enables better kernel design, prompt distillation, and runtime
adaptation strategies (such as dynamic loading, sigil pruning, or tapas-style
context injection).

All bicamerally legible systems must address bicameral tension as part of their
core architecture.
