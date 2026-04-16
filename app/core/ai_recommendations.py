import os

from openai import OpenAI
from pydantic import BaseModel


class RecommendationAction(BaseModel):
    title: str
    why: str
    how: str
    priority: str
    effort: str


class RecommendationResult(BaseModel):
    overall_summary: str
    key_risks: list[str]
    top_actions: list[RecommendationAction]


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _detail_instructions(level: str) -> str:
    if level == "Kurz":
        return "Halte dich sehr kurz: max. 1-2 Saetze Summary, 5 Massnahmen mit je 1 Satz 'Warum' und 1 Satz 'Wie'."
    if level == "Detailliert":
        return "Sei detailliert: Summary 4-6 Saetze, Massnahmen mit konkreten Schritten (2-4 Bullet Steps)."
    return "Standard: Summary 2-4 Saetze, Massnahmen mit klaren 'Warum' und 'Wie' (je 1-2 Saetze)."


def generate_recommendations(
    use_case_name: str,
    scores: dict,
    gatekeepers: dict,
    detail_level: str = "Standard",
) -> dict:
    """
    Returns dict with keys:
    - overall_summary: str
    - key_risks: list[str]
    - top_actions: list[{title, why, how, priority, effort}]
    """

    payload = {
        "use_case_name": use_case_name,
        "decision": scores.get("decision"),
        "overall_score": scores.get("overall_score"),
        "level_scores": scores.get("level_scores"),
        "block_scores": scores.get("block_scores"),
        "gatekeepers": gatekeepers,
        "blockers": scores.get("blockers", []),
    }

    system = (
        "Du bist ein Berater fuer KMU bei der Einfuehrung von generativen KI-Agenten. "
        "Du gibst konkrete, umsetzbare Handlungsempfehlungen basierend auf Scores (1-5) "
        "fuer Strategie/Organisation, Umsetzbarkeit/Technik und Governance/Risiko. "
        "Beachte Gatekeeper: Wenn Compliance/Governance/Integration blockiert, muessen zuerst Mindestmassnahmen erfuellt werden."
    )

    user = (
        f"Use Case: {use_case_name}\n"
        f"Detailgrad: {detail_level}\n"
        f"{_detail_instructions(detail_level)}\n\n"
        "Hier sind die Bewertungsresultate als JSON:\n"
        f"{payload}\n\n"
        "Liefere JSON exakt gemaess Schema. "
        "Top_actions sollen priorisiert sein und direkt im KMU-Kontext umsetzbar."
    )

    client = _get_client()
    response = client.responses.parse(
        model="gpt-4.1-mini",
        text_format=RecommendationResult,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI response could not be parsed into RecommendationResult")

    return parsed.model_dump()
