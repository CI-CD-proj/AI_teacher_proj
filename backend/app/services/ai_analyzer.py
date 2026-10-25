import json
import re
from typing import Any, Dict

from app.core.config import settings
from app.models import Question

SYSTEM_PROMPT = """Сен Қазақстан мектебіндегі тәжірибелі мұғалімсің.
Оқушының АШЫҚ сұраққа берген жауабын қазақ тілінде талда.

Тек JSON қайтар. Басқа мәтін жазба.
Схема:
{
  "correctness": "correct" | "partial" | "incorrect",
  "is_correct": true | false,
  "score": 0-100,
  "what_is_wrong": "Не дұрыс емес / не жетіспейді (қысқа, нақты)",
  "why_wrong": "Неліктен қате немесе толық емес (түсіндірме)",
  "where_to_start": "Қай тақырыптан / қандай ұғымнан бастап қайталау керек",
  "what_to_study": ["нақты тақырып 1", "нақты тақырып 2"],
  "correct_direction": "Дұрыс жауапқа қарай қысқа бағыт (даяр жауапты толық жазып берме, ойлауға көмектес)"
}

Ережелер:
- Қазақ тілінде жаз.
- Мектеп оқушысына түсінікті сөйле.
- Егер жауап бос болса — correctness=incorrect, score=0.
- Егер жауап ішінара дұрыс болса — partial, score 40-75.
- Даяр эссе жазып берме, бағыт бер.
"""


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _fallback(reason: str) -> Dict[str, Any]:
    return {
        "correctness": "unknown",
        "is_correct": None,
        "score": 0,
        "what_is_wrong": "Жауапты автоматты тексеру мүмкін болмады.",
        "why_wrong": reason,
        "where_to_start": "Мұғаліммен бірге осы сұрақтың тақырыбын қайталаңыз.",
        "what_to_study": [],
        "correct_direction": "Жауабыңызды тақырыптың негізгі ұғымдарымен салыстырып көріңіз.",
    }


def analyze_open_answer(question: Question, student_answer: str) -> Dict[str, Any]:
    if not (student_answer or "").strip():
        return {
            "correctness": "incorrect",
            "is_correct": False,
            "score": 0,
            "what_is_wrong": "Жауап жазылмаған.",
            "why_wrong": "Ашық сұраққа мәтіндік жауап қажет.",
            "where_to_start": question.topic or "Сұрақтың тақырыбынан",
            "what_to_study": [question.topic] if question.topic else [],
            "correct_direction": "Сұрақты қайта оқып, негізгі идеяны өз сөзіңізбен жазыңыз.",
        }

    if not settings.gemini_api_key:
        result = _fallback(
            "GEMINI_API_KEY орнатылмаған. .env файлына Google Gemini кілтін қойыңыз."
        )
        result["what_is_wrong"] = "AI талдауы өшірулі (API кілті жоқ)."
        return result

    user_prompt = f"""Пән/сынып контексі сұрақтан шығады.
Тақырып: {question.topic or "көрсетілмеген"}
Сұрақ: {question.prompt}
Мұғалімнің үлгі/анықтамалық жауабы: {question.reference_answer or "берілмеген"}
Оқушы жауабы: {student_answer}
"""

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            user_prompt,
            generation_config={
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
        data = _extract_json(response.text or "")
        correctness = str(data.get("correctness") or "partial").lower()
        if correctness not in {"correct", "partial", "incorrect"}:
            correctness = "partial"
        score_pct = float(data.get("score") or 0)
        score_pct = max(0, min(100, score_pct))
        what_to_study = data.get("what_to_study") or []
        if isinstance(what_to_study, str):
            what_to_study = [what_to_study]
        is_correct = correctness == "correct"
        if data.get("is_correct") is False:
            is_correct = False
        if correctness == "partial":
            is_correct = False
        return {
            "correctness": correctness,
            "is_correct": is_correct,
            "score": score_pct,
            "what_is_wrong": data.get("what_is_wrong") or "",
            "why_wrong": data.get("why_wrong") or "",
            "where_to_start": data.get("where_to_start") or "",
            "what_to_study": [str(x) for x in what_to_study if str(x).strip()],
            "correct_direction": data.get("correct_direction") or "",
        }
    except Exception as exc:
        return _fallback(f"Gemini қатесі: {exc}")
