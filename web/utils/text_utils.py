"""
Text processing utility functions
"""
import re


def format_conversation(messages: list) -> str:
    """Convert frontend message format to readable conversation text

    Args:
        messages: Message list, each containing role and content

    Returns:
        Formatted conversation text
    """
    lines = []
    for idx, turn in enumerate(messages, 1):
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        label = {"doctor": "Doctor", "patient": "Patient"}.get(role, role)
        lines.append(f"[Turn {idx}] {label}: {content}")
    return "\n\n".join(lines)


def extract_keywords(text: str) -> list:
    """Extract keywords from text (simple tokenization)

    Args:
        text: Input text

    Returns:
        Keyword list
    """
    if not text:
        return []
    cn_words = re.findall(r'[一-鿿]{2,}', text)
    num_units = re.findall(r'\d+\s*[年月周天次小时]', text)
    return list(set(cn_words + num_units))


def text_overlap(text1: str, text2: str) -> float:
    """Calculate character-level Jaccard similarity between two texts

    Args:
        text1: Text 1
        text2: Text 2

    Returns:
        Similarity (0.0 ~ 1.0)
    """
    if not text1 or not text2:
        return 0.0
    set1 = set(text1)
    set2 = set(text2)
    intersection = set1 & set2
    union = set1 | set2
    if not union:
        return 0.0
    return len(intersection) / len(union)
