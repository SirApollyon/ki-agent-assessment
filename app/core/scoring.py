from collections import defaultdict

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

def traffic_light(score: float) -> str:
    if score >= 4.0:
        return "Grün"
    if score >= 3.0:
        return "Gelb"
    return "Rot"

def compute_scores(items, gatekeepers):
    # items: list[(code, score)]
    by_prefix = defaultdict(list)
    unknown_items = []
    valid_prefixes = set(BLOCK_PREFIXES.values())

    for code, val in items:
        prefix = "".join([c for c in code if c.isalpha()])
        if prefix in valid_prefixes:
            by_prefix[prefix].append(float(val))
        else:
            unknown_items.append((code, val))

    block_scores = {}
    for block_name, prefix in BLOCK_PREFIXES.items():
        vals = by_prefix.get(prefix, [])
        block_scores[block_name] = sum(vals)/len(vals) if vals else None

    level_scores = {}
    for lvl, prefixes in LEVELS.items():
        vals = []
        for p in prefixes:
            # find all blocks with this prefix
            for bname, bprefix in BLOCK_PREFIXES.items():
                if bprefix == p and block_scores[bname] is not None:
                    vals.append(block_scores[bname])
        level_scores[lvl] = sum(vals)/len(vals) if vals else None

    overall = None
    if all(level_scores[lvl] is not None for lvl in LEVELS):
        overall = sum(level_scores[lvl] * WEIGHTS[lvl] for lvl in LEVELS)

    # Decision baseline
    decision = "PILOT"
    if overall is None:
        decision = "HOLD"
    elif overall >= 4.0:
        decision = "GO"
    elif overall < 3.0:
        decision = "HOLD"

    # Gatekeeper overrides
    blockers = [k for k,v in gatekeepers.items() if isinstance(v, str) and v.lower() == "nein"]
    if blockers:
        decision = "HOLD" if any(k in ["RC-G1", "GV-G1", "IT-G1"] for k in blockers) else "PILOT"

    return {
        "block_scores": block_scores,
        "level_scores": level_scores,
        "overall_score": overall,
        "blockers": blockers,
        "decision": decision,
        "unknown_items": unknown_items,
        "traffic": {
            "overall": traffic_light(overall) if overall is not None else "—",
            **{lvl: traffic_light(s) if s is not None else "—" for lvl,s in level_scores.items()},
        }
    }