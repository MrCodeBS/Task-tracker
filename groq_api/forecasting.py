
import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from database import db

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _task_key(task_description: str) -> str:
    return re.sub(r"\s+", " ", (task_description or "").strip().lower())


def _keyword_score(text: str, fallback: int) -> int:
    text_lower = (text or "").strip().lower()
    mapping = {
        "very low": 15,
        "low": 30,
        "light": 35,
        "medium": 50,
        "moderate": 55,
        "high": 75,
        "heavy": 80,
        "very high": 90,
        "overloaded": 92,
        "positive": 78,
        "neutral": 50,
        "negative": 24,
        "anxious": 28,
        "calm": 70,
    }
    for key, score in mapping.items():
        if key in text_lower:
            return score
    return fallback


def _coerce_score(value, text_fallback: str, fallback: int) -> int:
    if isinstance(value, (int, float)):
        score = int(value)
        return max(0, min(100, score))

    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            score = int(match.group())
            return max(0, min(100, score))

    return _keyword_score(text_fallback, fallback)


def normalize_forecast(raw: dict) -> dict:
    """Normalize raw model output into stable chart-friendly keys."""
    mood = str(raw.get("mood", "Unknown")).strip()
    stress = str(raw.get("stress", "Unknown")).strip()
    load = str(raw.get("load", "Unknown")).strip()

    mood_score = _coerce_score(raw.get("mood_score"), mood, 55)
    stress_score = _coerce_score(raw.get("stress_score"), stress, 50)
    load_score = _coerce_score(raw.get("load_score"), load, 50)

    summary = str(
        raw.get("summary")
        or raw.get("rationale")
        or raw.get("notes")
        or "No summary provided."
    ).strip()

    return {
        "mood": mood,
        "stress": stress,
        "load": load,
        "mood_score": mood_score,
        "stress_score": stress_score,
        "load_score": load_score,
        "summary": summary,
    }

def get_forecast(task_description: str, force_refresh: bool = False) -> dict:
    """
    Get a mood, stress, and load forecast from Groq API.
    """
    task_key = _task_key(task_description)
    if not task_key:
        return {"error": "Please provide a task description."}

    cached = db.get_cached_forecast(task_key)
    if cached and not force_refresh:
        return cached

    if not GROQ_API_KEY:
        return {"error": "Groq API key not configured."}

    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a forecasting assistant. "
                        "For identical task text, produce identical output. "
                        "Return ONLY valid JSON with keys: "
                        "mood, stress, load, mood_score, stress_score, load_score, summary. "
                        "Use strict labels: mood in [positive, neutral, negative]; "
                        "stress in [low, medium, high]; load in [low, medium, high]. "
                        "Scores must be integers from 0 to 100. "
                        "Keep summary concise (1-2 sentences)."
                    )
                },
                {
                    "role": "user",
                    "content": f"Task: {task_description}",
                }
            ],
            model=GROQ_MODEL,
            temperature=0,
            top_p=1,
            response_format={"type": "json_object"},
        )
        response_content = chat_completion.choices[0].message.content
        normalized = normalize_forecast(json.loads(response_content))
        db.save_cached_forecast(task_key, task_description, normalized)
        return normalized
    except Exception as e:
        return {"error": f"Error getting forecast from Groq: {e}"}


