from typing import Any

from home.models import Project


def build_context_prompt(project: Project, user_question: str, language_code: str = "en") -> str:
    """
    Build the strict context prompt for the per-project chatbot.

    This is kept in a separate module so it can be swapped or extended
    (e.g., with LangChain prompt templates) without touching views.
    """
    qas = project.qas.all()
    context = "\n".join(
        f"Q{idx + 1}: {qa.question}\nA{idx + 1}: {qa.answer}"
        for idx, qa in enumerate(qas)
    )

    # Constrain to supported languages, defaulting to English.
    language_code = (language_code or "en").lower()
    if language_code not in {"en", "hi"}:
        language_code = "en"

    language_label = "English" if language_code == "en" else "Hindi"

    return f"""
You are a strict assistant. Only answer based on the context provided below.
Do NOT make up any answers or add extra information.

The user's preferred language code is "{language_code}" and the corresponding
language is "{language_label}". You MUST write the "message" field of your
JSON response entirely in this language and be natural and fluent.

Context:
{context}

If the answer is not found in the above context, you MUST set "intent" to "unknown"
and respond with a helpful fallback message in the JSON "message" field in the same
language as requested above.

You MUST respond ONLY with a single valid JSON object with this exact structure
and no extra text before or after it:
{{
  "intent": "answer" | "lead" | "booking" | "greeting" | "unknown",
  "message": "text response to show to the user",
  "data": {{}}
}}


Note on images: If the correct response should include an image that exists in the
project's knowledge base, set the `data` field to include an `image` object with
non-sensitive descriptive fields only (the backend will attach the actual image URL
if available). Example:

    "data": {{"image": {{"reason": "illustrates the product feature", "caption": "Front view of Model X"}}}}

Do NOT include external URLs in the `image` field — leave URL resolution to the
backend code which has access to project media.

User Question: {user_question}
"""


