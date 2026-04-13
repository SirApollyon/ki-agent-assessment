from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def build_pdf(report_path, use_case_name, scores, radar_path, block_path=None):
    c = canvas.Canvas(report_path, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, h-2*cm, "KI-Potenzialanalyse – Report")

    c.setFont("Helvetica", 11)
    c.drawString(2*cm, h-3*cm, f"Use Case: {use_case_name}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, h-4*cm, f"Entscheidung: {scores['decision']}  |  Ampel: {scores['traffic']['overall']}")

    c.drawImage(radar_path, 2*cm, h-15*cm, width=12*cm, height=12*cm, preserveAspectRatio=True)

    y = h-16*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Ebenen-Scores:")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    for lvl, val in scores["level_scores"].items():
        c.drawString(2*cm, y, f"{lvl}: {val:.2f}" if val is not None else f"{lvl}: —")
        y -= 0.6*cm

    if scores["blockers"]:
        y -= 0.4*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y, f"Gatekeeper-Nein: {', '.join(scores['blockers'])}")

    if block_path:
        c.showPage()
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, h-2*cm, "Block-Scores")
        c.drawImage(block_path, 2*cm, h-18*cm, width=16*cm, height=18*cm, preserveAspectRatio=True)

    c.showPage()
    c.save()
