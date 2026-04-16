from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def _draw_wrapped_text(c, x, y, text, max_width_chars=110, line_height=12):
    """Einfache Zeilenumbrüche ohne Zusatzlibs."""
    words = (text or "").split()
    lines = []
    line = []
    for w in words:
        if len(" ".join(line + [w])) <= max_width_chars:
            line.append(w)
        else:
            lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))

    for ln in lines:
        c.drawString(x, y, ln)
        y -= line_height
    return y


def build_pdf(report_path, use_case_name, scores, radar_path, block_path=None, ai_result=None):
    c = canvas.Canvas(report_path, pagesize=A4)
    w, h = A4

    # ---------------------------
    # Seite 1: Overview + Summary
    # ---------------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, h - 2 * cm, "KI-Potenzialanalyse – Report")

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, h - 3 * cm, f"Use Case: {use_case_name}")

    overall = scores.get("overall_score")
    overall_str = f"{overall:.2f}" if isinstance(overall, (int, float)) else "—"

    c.setFont("Helvetica-Bold", 12)
    c.drawString(
        2 * cm,
        h - 4 * cm,
        f"Entscheidung: {scores.get('decision','—')}  |  Ampel: {scores.get('traffic',{}).get('overall','—')}  |  Gesamtscore: {overall_str}",
    )

    # Radar Ebenen
    c.drawImage(
        radar_path,
        2 * cm,
        h - 15 * cm,
        width=12 * cm,
        height=12 * cm,
        preserveAspectRatio=True,
    )

    # Ebenen-Scores rechts
    c.setFont("Helvetica-Bold", 11)
    c.drawString(15 * cm, h - 6 * cm, "Ebenen")
    c.setFont("Helvetica", 10)

    y = h - 6.8 * cm
    for lvl, val in (scores.get("level_scores") or {}).items():
        txt = f"{lvl}: {val:.2f}" if val is not None else f"{lvl}: —"
        c.drawString(15 * cm, y, txt)
        y -= 0.6 * cm

    # Gatekeeper
    blockers = scores.get("blockers") or []
    if blockers:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * cm, y - 0.2 * cm, "Gatekeeper-Nein:")
        c.setFont("Helvetica", 10)
        _draw_wrapped_text(
            c,
            15 * cm,
            y - 0.9 * cm,
            ", ".join(blockers),
            max_width_chars=28,
            line_height=11,
        )

    # Executive Summary
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, 5.0 * cm, "Executive Summary")
    c.setFont("Helvetica", 10)

    summary = None
    if isinstance(ai_result, dict):
        summary = ai_result.get("overall_summary")

    if not summary:
        summary = (
            f"Basierend auf den Scores ergibt sich die Empfehlung '{scores.get('decision','—')}'. "
            f"Fokussiere primär auf rot/gelb bewertete Bereiche und behebe Gatekeeper-Themen vor einem Rollout."
        )

    _draw_wrapped_text(c, 2 * cm, 4.3 * cm, summary, max_width_chars=110, line_height=12)

    c.showPage()

    # ---------------------------
    # Seite 2: Block-Radar + Ebene-Übersicht
    # ---------------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, h - 2 * cm, "Detailauswertung")

    if block_path:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, h - 3 * cm, "Radar – Bausteine")
        c.drawImage(
            block_path,
            2 * cm,
            h - 19 * cm,
            width=16 * cm,
            height=16 * cm,
            preserveAspectRatio=True,
        )

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, 6.2 * cm, "Ebenen-Scores (Übersicht)")
    c.setFont("Helvetica", 10)

    y = 5.5 * cm
    for lvl, val in (scores.get("level_scores") or {}).items():
        amp = scores.get("traffic", {}).get(lvl, "—")
        txt = f"{lvl}: {val:.2f} ({amp})" if val is not None else f"{lvl}: —"
        c.drawString(2 * cm, y, txt)
        y -= 0.6 * cm

    c.showPage()

    # ---------------------------
    # Seite 3: KI-Handlungsempfehlungen (wenn vorhanden)
    # ---------------------------
    if isinstance(ai_result, dict):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, h - 2 * cm, "Handlungsempfehlungen (KI)")

        actions = ai_result.get("top_actions") or []
        risks = ai_result.get("key_risks") or []

        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, h - 3.2 * cm, "Top-Maßnahmen (priorisiert)")

        y = h - 4.0 * cm
        for i, a in enumerate(actions[:5], start=1):
            title = a.get("title", "")
            prio = a.get("priority", "")
            effort = a.get("effort", "")
            why = a.get("why", "")
            how = a.get("how", "")

            c.setFont("Helvetica-Bold", 10)
            c.drawString(2 * cm, y, f"{i}. {title}  [prio={prio}, effort={effort}]")
            y -= 0.55 * cm

            c.setFont("Helvetica", 10)
            y = _draw_wrapped_text(c, 2 * cm, y, f"Warum: {why}", max_width_chars=110, line_height=12)
            y = _draw_wrapped_text(c, 2 * cm, y, f"Wie: {how}", max_width_chars=110, line_height=12)
            y -= 0.35 * cm

            if y < 4 * cm:
                c.showPage()
                y = h - 2.5 * cm

        if risks:
            if y < 6 * cm:
                c.showPage()
                y = h - 2.5 * cm

            c.setFont("Helvetica-Bold", 11)
            c.drawString(2 * cm, y, "Wesentliche Risiken")
            y -= 0.8 * cm

            c.setFont("Helvetica", 10)
            for rsk in risks[:6]:
                y = _draw_wrapped_text(c, 2 * cm, y, f"• {rsk}", max_width_chars=110, line_height=12)

        c.showPage()
    else:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, h - 2 * cm, "Handlungsempfehlungen (KI)")
        c.setFont("Helvetica", 10)
        _draw_wrapped_text(
            c,
            2 * cm,
            h - 3.2 * cm,
            "Es wurden keine KI-Handlungsempfehlungen generiert oder sie sind nicht verfügbar."
            " Bitte prüfen Sie die OpenAI-Einstellungen und laden Sie die Auswertung erneut.",
            max_width_chars=110,
            line_height=12,
        )
        c.showPage()

    c.save()