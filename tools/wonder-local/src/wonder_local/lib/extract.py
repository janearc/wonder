import re
from typing import Tuple, Optional


def extract_title_and_content(markdown: str) -> Tuple[Optional[str], str]:
    """
    Extracts the title (first markdown H1) and the rest of the content.

    Args:
        markdown: The raw markdown text.

    Returns:
        A tuple of (title, content). Title is None if not found.
    """
    title_match = re.match(r'#\s+(.+?)(?:\n|$)', markdown)
    title = title_match.group(1).strip() if title_match else None

    content = markdown[title_match.end():].strip() if title_match else markdown.strip()
    return title, content

