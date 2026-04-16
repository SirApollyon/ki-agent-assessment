from collections.abc import Mapping

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = A4


def _format_score(value: float | None) -> str:
    return f"{value:.2f}" if isinstance(value, (int, float)) else "—"


def _draw_wrapped_text(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    text: str,
    max_width_chars: int = 110,
    line_height: int = 12,
) -> float:
    words = (text or "").split()
    current_line: list[str] = []
    lines: list[str] = []

    for word in words:
        candidate = " ".join(current_line + [word])
        if len(candidate) <= max_width_chars:
            current_line.append(word)
            continue

        lines.append(" ".join(current_line))
        current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height

    return y


def _draw_header(pdf: canvas.Canvas, title: str) -> None:
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(2 * cm, PAGE_HEIGHT - 2 * cm, title)


def _draw_level_scores(pdf: canvas.Canvas, scores: Mapping[str, object], x: float, y: float) -> None:
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, "Ebenen")
    pdf.setFont("Helvetica", 10)

    current_y = y - 0.8 * cm
    for level_name, value in (scores.get("level_scores") or {}).items():
        pdf.drawString(x, current_y, f"{level_name}: {_format_score(value)}")
        current_y -= 0.6 * cm

    blockers = scores.get("blockers") or []
    if blockers:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(x, current_y - 0.2 * cm, "Gatekeeper-Nein:")
        pdf.setFont("Helvetica", 10)
        _draw_wrapped_text(
            pdf,
            x,
            current_y - 0.9 * cm,
            ", ".join(blockers),
            max_width_chars=28,
            line_height=11,
        )


def _fallback_summary(scores: Mapping[str, object]) -> str:
    return (
        f"Basierend auf den Scores ergibt sich die Empfehlung '{scores.get('decision', '—')}'. "
        "Fokussiere primär auf rot oder gelb bewertete Bereiche und behebe "
        "Gatekeeper-Themen vor einem Rollout."
    )


def _draw_overview_page(
    pdf: canvas.Canvas,
    use_case_name: str,
    scores: Mapping[str, object],
    radar_path: str,
    ai_result: Mapping[str, object] | None,
) -> None:
    _draw_header(pdf, "KI-Potenzialanalyse – Report")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(2 * cm, PAGE_HEIGHT - 3 * cm, f"Use Case: {use_case_name}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(
        2 * cm,
        PAGE_HEIGHT - 4 * cm,
        "Entscheidung: "
        f"{scores.get('decision', '—')}  |  "
        f"Ampel: {scores.get('traffic', {}).get('overall', '—')}  |  "
        f"Gesamtscore: {_format_score(scores.get('overall_score'))}",
    )

    pdf.drawImage(
        radar_path,
        2 * cm,
        PAGE_HEIGHT - 15 * cm,
        width=12 * cm,
        height=12 * cm,
        preserveAspectRatio=True,
    )
    _draw_level_scores(pdf, scores, 15 * cm, PAGE_HEIGHT - 6 * cm)

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(2 * cm, 5.0 * cm, "Executive Summary")
    pdf.setFont("Helvetica", 10)

    summary = ai_result.get("overall_summary") if isinstance(ai_result, Mapping) else None
    _draw_wrapped_text(pdf, 2 * cm, 4.3 * cm, summary or _fallback_summary(scores))
    pdf.showPage()


def _draw_detail_page(pdf: canvas.Canvas, scores: Mapping[str, object], block_path: str | None) -> None:
    _draw_header(pdf, "Detailauswertung")

    if block_path:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(2 * cm, PAGE_HEIGHT - 3 * cm, "Radar – Bausteine")
        pdf.drawImage(
            block_path,
            2 * cm,
            PAGE_HEIGHT - 19 * cm,
            width=16 * cm,
            height=16 * cm,
            preserveAspectRatio=True,
        )

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(2 * cm, 6.2 * cm, "Ebenen-Scores (Übersicht)")
    pdf.setFont("Helvetica", 10)

    current_y = 5.5 * cm
    for level_name, value in (scores.get("level_scores") or {}).items():
        traffic = scores.get("traffic", {}).get(level_name, "—")
        label = f"{level_name}: {_format_score(value)} ({traffic})" if value is not None else f"{level_name}: —"
        pdf.drawString(2 * cm, current_y, label)
        current_y -= 0.6 * cm

    pdf.showPage()


def _draw_ai_page(pdf: canvas.Canvas, ai_result: Mapping[str, object] | None) -> None:
    _draw_header(pdf, "Handlungsempfehlungen (KI)")

    if not isinstance(ai_result, Mapping):
        pdf.setFont("Helvetica", 10)
        _draw_wrapped_text(
            pdf,
            2 * cm,
            PAGE_HEIGHT - 3.2 * cm,
            "Es wurden keine KI-Handlungsempfehlungen generiert oder sie sind nicht verfügbar. "
            "Bitte prüfen Sie die OpenAI-Einstellungen und laden Sie die Auswertung erneut.",
        )
        pdf.showPage()
        return

    actions = ai_result.get("top_actions") or []
    risks = ai_result.get("key_risks") or []

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(2 * cm, PAGE_HEIGHT - 3.2 * cm, "Top-Maßnahmen (priorisiert)")

    current_y = PAGE_HEIGHT - 4.0 * cm
    for index, action in enumerate(actions[:5], start=1):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(
            2 * cm,
            current_y,
            f"{index}. {action.get('title', '')}  [prio={action.get('priority', '')}, effort={action.get('effort', '')}]",
        )
        current_y -= 0.55 * cm

        pdf.setFont("Helvetica", 10)
        current_y = _draw_wrapped_text(pdf, 2 * cm, current_y, f"Warum: {action.get('why', '')}")
        current_y = _draw_wrapped_text(pdf, 2 * cm, current_y, f"Wie: {action.get('how', '')}")
        current_y -= 0.35 * cm

        if current_y < 4 * cm:
            pdf.showPage()
            _draw_header(pdf, "Handlungsempfehlungen (KI)")
            current_y = PAGE_HEIGHT - 2.5 * cm

    if risks:
        if current_y < 6 * cm:
            pdf.showPage()
            _draw_header(pdf, "Handlungsempfehlungen (KI)")
            current_y = PAGE_HEIGHT - 2.5 * cm

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(2 * cm, current_y, "Wesentliche Risiken")
        current_y -= 0.8 * cm

        pdf.setFont("Helvetica", 10)
        for risk in risks[:6]:
            current_y = _draw_wrapped_text(pdf, 2 * cm, current_y, f"• {risk}")

    pdf.showPage()


def build_pdf(
    report_path: str,
    use_case_name: str,
    scores: Mapping[str, object],
    radar_path: str,
    block_path: str | None = None,
    ai_result: Mapping[str, object] | None = None,
) -> None:
    pdf = canvas.Canvas(report_path, pagesize=A4)

    _draw_overview_page(pdf, use_case_name, scores, radar_path, ai_result)
    _draw_detail_page(pdf, scores, block_path)
    _draw_ai_page(pdf, ai_result)

    pdf.save()
