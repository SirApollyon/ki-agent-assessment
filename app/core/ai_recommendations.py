import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

AI_MODEL = "gpt-4.1-mini"


class RecommendationAction(BaseModel):
    title: str
    why: str
    how: str
    priority: Literal["high", "medium", "low"]
    effort: Literal["S", "M", "L"]


class RecommendationResult(BaseModel):
    overall_summary: str
    key_risks: list[str] = Field(default_factory=list)
    top_actions: list[RecommendationAction] = Field(default_factory=list)


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _detail_instructions(level: str) -> str:
    if level == "Kurz":
        return "Halte dich sehr kurz: maximal 1-2 Sätze Summary, 5 Maßnahmen mit je 1 Satz 'Warum' und 1 Satz 'Wie'."
    if level == "Detailliert":
        return "Sei detailliert: Summary 4-6 Sätze, Maßnahmen mit konkreten Schritten in 2-4 Bullet-Points."
    return "Standard: Summary 2-4 Sätze, Maßnahmen mit klarem 'Warum' und 'Wie' in je 1-2 Sätzen."


def _build_payload(use_case_name: str, scores: dict, gatekeepers: dict) -> dict:
    return {
        "use_case_name": use_case_name,
        "decision": scores.get("decision"),
        "overall_score": scores.get("overall_score"),
        "level_scores": scores.get("level_scores"),
        "block_scores": scores.get("block_scores"),
        "gatekeepers": gatekeepers,
        "blockers": scores.get("blockers", []),
    }


def generate_recommendations(
    use_case_name: str,
    scores: dict,
    gatekeepers: dict,
    detail_level: str = "Standard",
) -> dict:
    payload = _build_payload(use_case_name, scores, gatekeepers)
    client = _get_client()

    response = client.responses.parse(
        model=AI_MODEL,
        text_format=RecommendationResult,
        input=[
            {
                "role": "system",
                "content": (
                    "Du bist ein Berater für KMU bei der Einführung von generativen KI-Agenten. "
                    "Du gibst konkrete, umsetzbare Handlungsempfehlungen basierend auf Scores von 1 bis 5 "
                    "für Strategie, Umsetzbarkeit und Governance. "
                    "Wenn Compliance, Governance oder Integration blockieren, priorisiere zuerst Mindestmaßnahmen."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Use Case: {use_case_name}\n"
                    f"Detailgrad: {detail_level}\n"
                    f"{_detail_instructions(detail_level)}\n\n"
                    "Hier sind die Bewertungsresultate als JSON:\n"
                    f"{payload}\n\n"
                    "Liefere ein JSON-Objekt passend zu diesem Schema:\n"
                    "{"
                    '"overall_summary": "string", '
                    '"key_risks": ["string"], '
                    '"top_actions": ['
                    '{"title": "string", "why": "string", "how": "string", "priority": "high|medium|low", "effort": "S|M|L"}'
                    "]"
                    "}.\n"
                    "Top_actions sollen priorisiert sein und direkt im KMU-Kontext umsetzbar."
                ),
            },
        ],
    )

    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI response could not be parsed into RecommendationResult")

    return parsed.model_dump()
