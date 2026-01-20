from typing import Literal


LanguageCode = Literal["en", "hi"]


def detect_language(text: str | None, default: LanguageCode = "en") -> LanguageCode:
    """
    Very lightweight language detector for English vs Hindi.

    - If we detect any Devanagari characters or common Hindi words,
      we classify as Hindi ("hi").
    - Otherwise we default to English ("en").

    This avoids adding heavy external dependencies while being
    good enough for typical chatbot queries.
    """
    if not text:
        return default

    text = text.strip()
    if not text:
        return default

    # Heuristic 1: Devanagari Unicode block.
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"

    # Heuristic 2: very common Hindi tokens (in Latin script).
    lowered = text.lower()
    hindi_markers = ["namaste", "namaskar", "shukriya", "dhanyavaad", "kaise ho", "kya", "kyu", "nahi"]
    if any(marker in lowered for marker in hindi_markers):
        return "hi"

    return "en"



