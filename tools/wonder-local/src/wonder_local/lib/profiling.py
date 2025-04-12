def profile_linguistic_complexity(text: str) -> dict:
    return {
        "token_count": len(tokenizer.encode(text)),
        "sentence_count": len(sent_tokenize(text)),
        "avg_sentence_length": avg_sentence_len(text),
        "flesch_kincaid": textstat.flesch_kincaid_grade(text),
        "zipf_avg": avg_zipf_score(text),
        "dependency_depth": max_dependency_depth(text),
        "relationship_count": gizzard.get_relationships_for(text),
    }
