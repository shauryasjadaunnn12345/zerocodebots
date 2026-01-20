import json
from typing import Any, Dict


def normalize_ai_payload(raw_text: str) -> Dict[str, Any]:
    """
    Ensure the AI output is a valid JSON payload with the required shape:
    { "intent": "answer|lead|booking|greeting|unknown", "message": "text", "data": {} }

    Falls back gracefully if parsing fails or the structure is invalid.
    """
    raw_text = (raw_text or "").strip()

    # Default fallback if anything goes wrong
    fallback = {
        "intent": "unknown",
        "message": raw_text or "Sorry, I couldn't fetch a response from the AI.",
        "data": {},
    }

    # Some models (e.g. Gemma) may wrap JSON in Markdown code fences,
    # e.g. ```json { ... } ``` – strip those if present.
    candidate = raw_text
    if candidate.startswith("```"):
        # Remove leading ```lang and trailing ```
        parts = candidate.split("```")
        if len(parts) >= 3:
            # parts[0] == "", parts[1] == "json\n{...}", parts[-1] == ""
            inner = parts[1]
            # Drop possible language prefix like "json\n"
            if "\n" in inner:
                inner = inner.split("\n", 1)[1]
            candidate = inner.strip()

    try:
        parsed = json.loads(candidate)
    except Exception:
        # Model returned free text instead of JSON
        return fallback

    if not isinstance(parsed, dict):
        return fallback

    intent = parsed.get("intent", "unknown")
    message = parsed.get("message", "")
    data = parsed.get("data", {})

    allowed_intents = {"answer", "lead", "booking", "greeting", "unknown"}

    if intent not in allowed_intents:
        intent = "unknown"

    if not isinstance(message, str) or not message.strip():
        message = fallback["message"]

    if not isinstance(data, dict):
        data = {}

    # Allow an optional `image` object inside data. Normalize minimal expected fields.
    image = data.get("image")
    if isinstance(image, dict):
        image_url = image.get("url")
        caption = image.get("caption") or image.get("description") or image.get("reason") or ""
        # Keep only the safe fields we expect; URL may be absent (backend can attach it).
        normalized_image = {}
        if isinstance(image_url, str) and image_url.strip():
            normalized_image["url"] = image_url.strip()
        if isinstance(caption, str) and caption.strip():
            normalized_image["caption"] = caption.strip()

        if normalized_image:
            data["image"] = normalized_image
        else:
            # Keep descriptive reason if present but no URL/caption
            reason = image.get("reason")
            if isinstance(reason, str) and reason.strip():
                data["image"] = {"reason": reason.strip()}
            else:
                data.pop("image", None)

    return {
        "intent": intent,
        "message": message.strip(),
        "data": data,
    }


