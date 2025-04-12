import textacy
import spacy
from pathlib import Path
from typing import List, Dict, Any

nlp = spacy.load("en_core_web_sm")

def parse_concepts_from_markdown(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a markdown file into concept entries using semantic and syntactic heuristics.
    Returns a list of dictionaries with type, source, and target text chunks.
    """
    text = file_path.read_text(encoding="utf-8")
    doc = nlp(text)

    concepts = []

    # Definition-style concepts
    for sent in doc.sents:
        if any(phrase in sent.text.lower() for phrase in [" is ", " refers to ", " defined as "]):
            concepts.append({
                "type": "definition",
                "source": sent.text.strip(),
                "target": None
            })

    # Contrast
    for sent in doc.sents:
        if any(phrase in sent.text.lower() for phrase in ["unlike", "however", "in contrast", "opposes"]):
            concepts.append({
                "type": "contrast",
                "source": sent.text.strip(),
                "target": None
            })

    # Consequence
    for sent in doc.sents:
        if any(phrase in sent.text.lower() for phrase in ["therefore", "as a result", "leads to"]):
            concepts.append({
                "type": "consequence",
                "source": sent.text.strip(),
                "target": None
            })

    # Example
    for sent in doc.sents:
        if any(phrase in sent.text.lower() for phrase in ["for instance", "e.g.", "such as"]):
            concepts.append({
                "type": "example",
                "source": sent.text.strip(),
                "target": None
            })

    # Analogy
    for sent in doc.sents:
        if any(phrase in sent.text.lower() for phrase in ["similar to", "like a", "metaphor for"]):
            concepts.append({
                "type": "analogy",
                "source": sent.text.strip(),
                "target": None
            })

    return concepts

