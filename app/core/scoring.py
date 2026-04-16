from collections import defaultdict
from typing import cast

BLOCK_PREFIXES = {
    "Strategische Zielklarheit": "SZK",
    "Management-Commitment": "MC",
    "Problem- & Use-Case-Fit": "PUF",
    "Erwarteter Nutzen": "EN",
    "Change-Fähigkeit": "CF",
    "Datenverfügbarkeit & -qualität": "DQ",
    "IT & Integrationsfähigkeit": "IT",
    "Kompetenzen & Skills": "SK",
    "Ressourcen (Zeit & Budget)": "RB",
    "Pilotierbarkeit & Skalierbarkeit": "PS",
    "Recht & Compliance": "RC",
    "Ethik & Fairness": "EF",
    "Transparenz & Nachvollziehbarkeit": "TN",
    "Governance & Verantwortlichkeiten": "GV",
    "Risikoprofil Use Case": "RU",
}

LEVELS = {
    "Ebene 1": ["SZK", "MC", "PUF", "EN", "CF"],
    "Ebene 2": ["DQ", "IT", "SK", "RB", "PS"],
    "Ebene 3": ["RC", "EF", "TN", "GV", "RU"],
}

WEIGHTS = {"Ebene 1": 0.35, "Ebene 2": 0.35, "Ebene 3": 0.30}
HARD_BLOCKER_CODES = {"RC-G1", "GV-G1", "IT-G1"}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def traffic_light(score: float) -> str:
    if score >= 4.0:
        return "Grün"
    if score >= 3.0:
        return "Gelb"
    return "Rot"


def _prefix_from_code(code: str) -> str:
    return "".join(character for character in code if character.isalpha())


def _group_scores_by_prefix(items: list[tuple[str, float]]) -> tuple[dict[str, list[float]], list[tuple[str, float]]]:
    grouped_scores: dict[str, list[float]] = defaultdict(list)
    unknown_items: list[tuple[str, float]] = []
    valid_prefixes = set(BLOCK_PREFIXES.values())

    for code, value in items:
        prefix = _prefix_from_code(code)
        if prefix in valid_prefixes:
            grouped_scores[prefix].append(float(value))
        else:
            unknown_items.append((code, value))

    return grouped_scores, unknown_items


def _compute_block_scores(grouped_scores: dict[str, list[float]]) -> dict[str, float | None]:
    return {
        block_name: _mean(grouped_scores.get(prefix, []))
        for block_name, prefix in BLOCK_PREFIXES.items()
    }


def _compute_level_scores(block_scores: dict[str, float | None]) -> dict[str, float | None]:
    level_scores: dict[str, float | None] = {}

    for level_name, prefixes in LEVELS.items():
        values = [
            score
            for block_name, block_prefix in BLOCK_PREFIXES.items()
            if block_prefix in prefixes
            for score in [block_scores[block_name]]
            if score is not None
        ]
        level_scores[level_name] = _mean(values)

    return level_scores


def _decision_from_scores(overall_score: float | None, blockers: list[str]) -> str:
    if blockers:
        return "HOLD" if any(code in HARD_BLOCKER_CODES for code in blockers) else "PILOT"
    if overall_score is None:
        return "HOLD"
    if overall_score >= 4.0:
        return "GO"
    if overall_score < 3.0:
        return "HOLD"
    return "PILOT"


def compute_scores(items: list[tuple[str, float]], gatekeepers: dict[str, str]) -> dict[str, object]:
    grouped_scores, unknown_items = _group_scores_by_prefix(items)
    block_scores = _compute_block_scores(grouped_scores)
    level_scores = _compute_level_scores(block_scores)

    overall_score = None
    if all(level_scores[level_name] is not None for level_name in LEVELS):
        overall_score = sum(
            cast(float, level_scores[level_name]) * WEIGHTS[level_name]
            for level_name in LEVELS
        )

    blockers = [
        code
        for code, value in gatekeepers.items()
        if isinstance(value, str) and value.strip().lower() == "nein"
    ]

    return {
        "block_scores": block_scores,
        "level_scores": level_scores,
        "overall_score": overall_score,
        "blockers": blockers,
        "decision": _decision_from_scores(overall_score, blockers),
        "unknown_items": unknown_items,
        "traffic": {
            "overall": traffic_light(overall_score) if overall_score is not None else "—",
            **{
                level_name: traffic_light(score) if score is not None else "—"
                for level_name, score in level_scores.items()
            },
        },
    }
