import openpyxl
import re

REQUIRED_SHEETS = {"Input"}
CODE_PATTERN = re.compile(r"^([A-Za-z]+)")


def load_workbook(path: str):
    wb = openpyxl.load_workbook(path, data_only=True)
    missing = REQUIRED_SHEETS - set(wb.sheetnames)
    if missing:
        raise ValueError(f"Fehlende Sheets im Excel: {', '.join(sorted(missing))}. "
                         f"Bitte dein Template verwenden.")
    return wb


def _normalize_code(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    match = CODE_PATTERN.match(value)
    return match.group(1).upper() if match else None


def _parse_score(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None
    return None


def read_inputs(wb):
    ws = wb["Input"]

    use_case_name = ws["B4"].value or "Unbenannter Use Case"

    items = []
    gatekeepers = {}

    for row in range(1, ws.max_row + 1):
        code = _normalize_code(ws.cell(row=row, column=3).value)  # C
        score = _parse_score(ws.cell(row=row, column=5).value)  # E
        if code and score is not None:
            items.append((code, score))

    for row in range(1, ws.max_row + 1):
        gcode = ws.cell(row=row, column=1).value  # A
        gval = ws.cell(row=row, column=7).value  # G
        if isinstance(gcode, str) and gcode.strip().upper().endswith(("-G1", "-G2")):
            if isinstance(gval, str):
                gatekeepers[gcode.strip()] = gval.strip()

    if not items:
        raise ValueError("Keine Item-Bewertungen gefunden. Bitte im Tab 'Input' die 1–5 Werte ausfüllen.")

    return {
        "use_case_name": use_case_name,
        "items": items,
        "gatekeepers": gatekeepers,
    }
