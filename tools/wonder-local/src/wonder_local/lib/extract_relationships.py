import re
from typing import Dict, List


def extract_relationships(text: str, title: str) -> List[Dict[str, str]]:
    """
    Extracts semantic and syntactic relationships from a markdown text.
    Returns a list of dictionaries describing relationships.
    """
    relationships = []

    # Extract [[...]] style references
    for match in re.finditer(r"\[\[(.*?)\]\]", text):
        target = match.group(1).strip()
        if target and target != title:
            relationships.append(
                {"source": title, "target": target, "type": "links_to"}
            )

    # Define relationship types and patterns
    patterns = {
        r"requires|needs|must have|depends on": "requires",
        r"relates to|connects with|links to|associated with": "relates_to",
        r"extends|builds on|enhances": "extends",
        r"contrasts with|differs from|opposes": "contrasts_with",
        r"part of|belongs to|contained in": "part_of",
        r"similar to|like|analogous to": "similar_to",
        r"influences|affects|impacts": "influences",
    }

    sentences = re.split(r"[.!?]+", text)
    for sentence in sentences:
        for pattern, rel_type in patterns.items():
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                before = sentence[: match.start()].strip()
                after = sentence[match.end() :].strip()

                before_terms = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", before)
                after_terms = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", after)

                if before_terms and after_terms:
                    source = before_terms[-1]
                    target = after_terms[0]

                    if source != title and target != title:
                        continue

                    if target == title:
                        source, target = target, source

                    relationships.append(
                        {"source": source, "target": target, "type": rel_type}
                    )

    return relationships
