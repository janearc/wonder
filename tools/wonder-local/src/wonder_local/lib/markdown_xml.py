import re
from typing import List
from xml.etree import ElementTree as ET

import markdown
from bs4 import BeautifulSoup


def markdown_to_xml(md_text: str) -> ET.Element:
    """
    Converts Markdown text into an XML tree for structured parsing.
    Automatically unwraps hard-wrapped paragraphs and strips inline formatting tags.
    """
    # Step 1: Normalize line endings
    md_text = md_text.replace("\r\n", "\n").replace("\r", "\n")

    # Step 2: Unwrap hard-wrapped paragraphs (merge lines unless separated by blank line)
    lines = md_text.split("\n")
    unwrapped_lines: List[str] = []
    buffer: List[str] = []

    for line in lines:
        if line.strip() == "":
            if buffer:
                unwrapped_lines.append(" ".join(buffer))
                buffer = []
            unwrapped_lines.append("")  # Preserve blank line as paragraph break
        else:
            buffer.append(line.strip())

    if buffer:
        unwrapped_lines.append(" ".join(buffer))

    unwrapped_text = "\n".join(unwrapped_lines)

    # Step 3: Convert to HTML using markdown lib
    html = markdown.markdown(unwrapped_text, extensions=["extra"])

    # Step 4: Strip inline formatting like <strong>, <em>, etc.
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["strong", "em", "code", "span"]):
        tag.unwrap()

    # Step 5: Parse to XML tree
    root = ET.fromstring(f"<root>{str(soup)}</root>")
    return root
