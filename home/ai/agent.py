from typing import Any, Dict, TypedDict
import json

import requests
from django.conf import settings

from home.ai.prompts import build_context_prompt
from home.ai.parsers import normalize_ai_payload
from home.models import Project


# Optional LangChain imports – if unavailable, we fall back to the
# existing raw OpenRouter HTTP integration so the chatbot keeps working.
try:  # pragma: no cover - import-time optional dependency
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate

    LANGCHAIN_AVAILABLE = True
except Exception:  # ImportError or anything unexpected
    ChatOpenAI = None  # type: ignore
    PromptTemplate = None  # type: ignore
    LANGCHAIN_AVAILABLE = False


# Optional LangGraph imports – if unavailable, we still call the
# backend directly. When present, we use it for intent routing.
try:  # pragma: no cover - import-time optional dependency
    from langgraph.graph import StateGraph, START, END

    LANGGRAPH_AVAILABLE = True
except Exception:  # ImportError or anything unexpected
    StateGraph = None  # type: ignore
    START = None  # type: ignore
    END = None  # type: ignore
    LANGGRAPH_AVAILABLE = False


class ChatState(TypedDict, total=False):
    project_id: int
    question: str
    language: str
    intent: str
    message: str
    data: Dict[str, Any]


def _call_openrouter_raw(prompt: str) -> Dict[str, Any]:
    """
    Legacy/raw OpenRouter call that expects a JSON string response
    and normalizes it. Used as a fallback when LangChain is not
    available or fails.
    """
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_KEY}",
        "Referer": "https://zerocodebots.onrender.com/",
        "X-Title": "Project Chatbot",
        "Content-Type": "application/json",
    }

    # NOTE: Some providers behind OpenRouter (e.g. Google Gemini/Gemma)
    # do not allow separate developer/system instructions. To avoid the
    # "Developer instruction is not enabled" 400 error, we send a single
    # user message containing our full prompt and JSON instructions.
    data = {
        "model": "google/gemma-3-12b-it:free",  # or claude/gpt
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30,
        )
    except Exception as e:
        print("DEBUG request error (raw):", str(e))
        return {
            "intent": "unknown",
            "message": "Sorry, I couldn't reach the AI service.",
            "data": {},
        }

    print("DEBUG status (raw):", response.status_code)
    print("DEBUG response (raw):", response.text)

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("DEBUG parse error (raw):", str(e))
        return {
            "intent": "unknown",
            "message": "Sorry, I couldn't fetch a valid response from the AI.",
            "data": {},
        }

    return normalize_ai_payload(content)


def _call_openrouter_langchain(prompt: str) -> Dict[str, Any]:
    """
    LangChain-based call to the same OpenRouter backend, using:
    - PromptTemplate for prompt composition
    - JsonOutputParser for structured output

    Falls back to the raw client if anything goes wrong.
    """
    if not LANGCHAIN_AVAILABLE:
        return _call_openrouter_raw(prompt)

    try:
        # PromptTemplate: we keep a simple template that injects the
        # already-constructed prompt text.
        template = PromptTemplate.from_template("{full_prompt}")

        llm = ChatOpenAI(
            model="google/gemma-3-12b-it:free",
            api_key=settings.OPENROUTER_KEY,
            base_url="https://openrouter.ai/api",  # => /v1/chat/completions under the hood
            # These headers mirror the legacy integration as closely as possible.
            default_headers={
                "Referer": "https://zerocodebots.onrender.com",
                "X-Title": "Project Chatbot",
            },
        )

        # Render prompt and invoke LLM directly. Different LangChain
        # versions may return a BaseMessage or raw string; handle both
        # and always normalize through our JSON contract.
        rendered = template.format(full_prompt=prompt)
        result = llm.invoke(rendered)

        if hasattr(result, "content"):
            content = result.content  # type: ignore[assignment]
        else:
            content = str(result)

        return normalize_ai_payload(content)
    except Exception as e:
        print("DEBUG LangChain error:", str(e))
        # Fallback to raw HTTP client so chatbot keeps working.
        return _call_openrouter_raw(prompt)


def _call_backend(prompt: str) -> Dict[str, Any]:
    """
    Unified backend caller. For now we always use the raw OpenRouter
    client to avoid version-specific LangChain issues.
    """
    return _call_openrouter_raw(prompt)


_graph_app = None


def _route_from_classify(state: ChatState) -> str:
    intent = (state.get("intent") or "unknown").lower()
    if intent == "lead":
        return "lead"
    if intent == "unknown":
        return "unknown"
    if intent in {"answer", "greeting"}:
        return "answer"
    # Default branch
    return "answer"


def _node_classify_intent(state: ChatState) -> ChatState:
    """
    START → classify_intent
    Use the model to determine intent/message/data.
    """
    project_id = state.get("project_id")
    question = state.get("question") or ""
    language = (state.get("language") or "en").lower()

    if not project_id:
        # Defensive: should not happen, but keep flow safe.
        payload = {
            "intent": "unknown",
            "message": "Missing project information.",
            "data": {},
        }
    else:
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            payload = {
                "intent": "unknown",
                "message": "Project not found.",
                "data": {},
            }
        else:
            prompt = build_context_prompt(project, question, language_code=language)
            payload = _call_backend(prompt)

            # Enrich payload with project media when appropriate.
            # If the model did not include an `image` in `data`, attempt to
            # resolve a matching QA image from the project's knowledge base.
            try:
                if isinstance(payload, dict):
                    payload.setdefault("data", {})
                    if payload.get("intent") == "answer" and "image" not in (payload.get("data") or {}):
                        user_q = (question or "").lower()
                        # Prefer exact substring matches against QA question/answer text.
                        for qa in project.qas.all():
                            if not qa.image:
                                continue
                            q_text = (qa.question or "").lower()
                            a_text = (qa.answer or "").lower()
                            if user_q and (user_q in q_text or user_q in a_text):
                                payload["data"]["image"] = {
                                    "url": qa.image.url,
                                    "caption": qa.image_description or "",
                                }
                                break

                        # If user explicitly asked for an image but no exact match,
                        # attach the first available QA image as a helpful fallback.
                        if "image" not in payload["data"] and any(k in user_q for k in ("image", "photo", "picture", "show", "visual", "see")):
                            for qa in project.qas.all():
                                if qa.image:
                                    payload["data"]["image"] = {
                                        "url": qa.image.url,
                                        "caption": qa.image_description or "",
                                    }
                                    break
            except Exception as e:
                # Non-fatal; ensure we don't break the chat flow if media lookup fails.
                print("DEBUG image enrichment error:", str(e))

    state["intent"] = payload.get("intent", "unknown")
    state["message"] = payload.get("message", "")
    state["data"] = payload.get("data") or {}
    return state


def _node_save_lead(state: ChatState) -> ChatState:
    """
    [lead] → save_lead

    This node is intentionally side-effect free at the AI layer.
    Actual Lead creation and analytics are handled in the Django
    view layer based on the returned intent/data.
    """
    # Placeholder to enrich state if needed in future.
    return state


def _node_fallback(state: ChatState) -> ChatState:
    """
    [unknown] → fallback
    """
    message = state.get("message") or ""
    if not message.strip():
        state["message"] = "I'm not sure how to handle that yet, but your message was received."
    state["intent"] = state.get("intent") or "unknown"
    return state


def _node_respond(state: ChatState) -> ChatState:
    """
    Terminal node that just passes the state through.
    """
    return state


def _get_graph_app():
    """
    Lazily build and cache the LangGraph app that routes intents:

    START → classify_intent
      → [answer] → respond
      → [lead]   → save_lead → respond
      → [unknown]→ fallback  → respond
    """
    global _graph_app
    if _graph_app is not None or not LANGGRAPH_AVAILABLE:
        return _graph_app

    graph = StateGraph(ChatState)
    graph.add_node("classify_intent", _node_classify_intent)
    graph.add_node("save_lead", _node_save_lead)
    graph.add_node("fallback", _node_fallback)
    graph.add_node("respond", _node_respond)

    graph.add_edge(START, "classify_intent")
    # Use the simpler add_conditional_edges signature supported by the
    # installed LangGraph version (no explicit default branch argument).
    graph.add_conditional_edges(
        "classify_intent",
        _route_from_classify,
        {
            "answer": "respond",
            "lead": "save_lead",
            "unknown": "fallback",
        },
    )
    graph.add_edge("save_lead", "respond")
    graph.add_edge("fallback", "respond")
    graph.add_edge("respond", END)

    _graph_app = graph.compile()
    return _graph_app


def _run_intent_graph(project: Project, user_question: str, language_code: str) -> Dict[str, Any]:
    """
    Execute the LangGraph intent routing per chat request when
    LangGraph is available. Falls back to a direct backend call
    when it is not installed.
    """
    if not LANGGRAPH_AVAILABLE:
        # No graph support – behave like before, just call backend once.
        prompt = build_context_prompt(project, user_question, language_code=language_code)
        return _call_backend(prompt)

    app = _get_graph_app()
    if app is None:
        # Safety net, although this should not happen.
        prompt = build_context_prompt(project, user_question, language_code=language_code)
        return _call_backend(prompt)

    initial_state: ChatState = {
        "project_id": project.id,
        "question": user_question,
        "language": language_code,
    }

    final_state: ChatState = app.invoke(initial_state)

    return {
        "intent": final_state.get("intent", "unknown"),
        "message": final_state.get("message", ""),
        "data": final_state.get("data", {}) or {},
    }


def generate_openrouter_answer(project: Project, user_question: str, language_code: str = "en") -> Dict[str, Any]:
    """
    Call the OpenRouter / Gemma model for a given project + question and
    return a normalized payload:

    {
      "intent": "answer|lead|booking|unknown",
      "message": "text",
      "data": {},
    }

    This function is the main AI agent entrypoint.
    It now executes a LangGraph intent-routing graph per request
    when available, while still falling back to the existing
    LangChain/raw backend behaviour. The views/frontend remain
    unchanged.
    """
    # Constrain to supported languages at the agent boundary.
    language_code = (language_code or "en").lower()
    if language_code not in {"en", "hi"}:
        language_code = "en"

    return _run_intent_graph(project, user_question, language_code)


