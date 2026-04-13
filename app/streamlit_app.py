import os
import sys
import uuid
import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.excel_io import load_workbook, read_inputs
from app.core.scoring import compute_scores
from app.core.radar import radar_chart, block_radar_chart
from app.core.report import build_pdf

load_dotenv()

UPLOAD_DIR = "data/uploads"
OUTPUT_DIR = "data/outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="KI-Potenzialanalyse", layout="centered")

st.title("KI-Potenzialanalyse für generative KI-Agenten (KMU)")
st.write("Excel hochladen → Auswertung (Radar + Report) automatisch erhalten.")

uploaded = st.file_uploader("Excel-Template (.xlsx) hochladen", type=["xlsx"])

if uploaded:
    assessment_id = str(uuid.uuid4())[:8]
    out_folder = os.path.join(OUTPUT_DIR, assessment_id)
    os.makedirs(out_folder, exist_ok=True)

    xlsx_path = os.path.join(UPLOAD_DIR, f"{assessment_id}.xlsx")
    with open(xlsx_path, "wb") as f:
        f.write(uploaded.getbuffer())

    if st.button("Auswerten"):
        try:
            wb = load_workbook(xlsx_path)
            data = read_inputs(wb)
            scores = compute_scores(data["items"], data["gatekeepers"])

            radar_path = os.path.join(out_folder, "radar_levels.png")
            block_path = os.path.join(out_folder, "block_scores.png")
            radar_chart(scores["level_scores"], radar_path)
            block_radar_chart(scores["block_scores"], block_path)

            pdf_path = os.path.join(out_folder, "report.pdf")
            build_pdf(pdf_path, data["use_case_name"], scores, radar_path, block_path)

            st.success("Fertig! Report erstellt.")
            col1, col2 = st.columns(2)
            col1.image(radar_path, caption="Radar – Ebenen")
            col2.image(block_path, caption="Radar – Block-Scores")

            st.markdown("### Aktuelle Werte")
            st.write("**Ebenen-Scores**")
            st.write(scores["level_scores"])
            st.write("**Block-Scores**")
            st.write(scores["block_scores"])
            st.write("**Parsed Input Items**")
            st.write(data["items"])
            if data["gatekeepers"]:
                st.write("**Gatekeeper**")
                st.write(data["gatekeepers"])
            if scores.get("unknown_items"):
                st.warning("Unbekannte Codes gefunden: " + ", ".join(f"{c}:{v}" for c,v in scores["unknown_items"]))

            with open(pdf_path, "rb") as f:
                st.download_button("PDF-Report herunterladen", f, file_name=f"report_{assessment_id}.pdf")

        except Exception as e:
            st.error(f"Fehler: {e}")