# -*- coding: utf-8 -*-
import os
import sys
import uuid
import streamlit as st
from dotenv import load_dotenv

# --- Pfade / Import-Fix ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.excel_io import load_workbook, read_inputs
from app.core.scoring import compute_scores
from app.core.radar import radar_chart, block_radar_chart
from app.core.report import build_pdf
from app.core.ai_recommendations import generate_recommendations

# --- Env ---
load_dotenv()

UPLOAD_DIR = "data/uploads"
OUTPUT_DIR = "data/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- UI ---
st.set_page_config(page_title="KI-Potenzialanalyse", layout="centered")
st.title("KI-Potenzialanalyse für generative KI-Agenten (KMU)")
st.write("Excel hochladen → Auswertung (Radar + Report) automatisch erhalten.")

with st.expander("Optionen", expanded=True):
    generate_ai = st.checkbox("KI-Empfehlungen generieren", value=True)
    detail_level = st.selectbox("Detailgrad", ["Kurz", "Standard", "Detailliert"], index=1)
    debug_mode = st.checkbox("Debug anzeigen", value=False)

# Key-Check (sofort sichtbar)
api_key_loaded = bool(os.getenv("OPENAI_API_KEY"))
st.caption(f"OPENAI_API_KEY geladen: {'✅ Ja' if api_key_loaded else '❌ Nein'}")
if not api_key_loaded:
    st.caption("Erwarteter Eintrag in .env: OPENAI_API_KEY=dein_api_key")

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
            # 1) Excel lesen
            wb = load_workbook(xlsx_path)
            data = read_inputs(wb)

            # 2) Scores berechnen
            scores = compute_scores(data["items"], data.get("gatekeepers", {}))

            # 3) KI Empfehlungen (optional)
            ai_result = None
            if generate_ai:
                if not api_key_loaded:
                    st.error(
                        "OPENAI_API_KEY ist nicht gesetzt. Trage in der Datei .env im "
                        "Projektverzeichnis z. B. 'OPENAI_API_KEY=dein_api_key' ein "
                        "und starte die App danach neu."
                    )
                    st.info("Die Auswertung läuft weiter, aber ohne KI-Empfehlungen.")
                else:
                    st.info("⏳ Generiere KI-Empfehlungen …")
                    try:
                        ai_result = generate_recommendations(
                            use_case_name=data["use_case_name"],
                            scores=scores,
                            gatekeepers=data.get("gatekeepers", {}),
                            detail_level=detail_level
                        )
                        st.success("✅ KI-Empfehlungen wurden generiert.")
                    except Exception as e:
                        st.error(f"⚠️ KI-Generierung fehlgeschlagen: {e}")
                        ai_result = None
            else:
                st.info("KI-Empfehlungen deaktiviert.")

            # 4) Charts generieren
            radar_path = os.path.join(out_folder, "radar_levels.png")
            block_path = os.path.join(out_folder, "radar_blocks.png")
            radar_chart(scores["level_scores"], radar_path)
            block_radar_chart(scores["block_scores"], block_path)

            # 5) PDF erzeugen (ai_result wird mitgegeben!)
            pdf_path = os.path.join(out_folder, "report.pdf")
            build_pdf(
                report_path=pdf_path,
                use_case_name=data["use_case_name"],
                scores=scores,
                radar_path=radar_path,
                block_path=block_path,
                ai_result=ai_result
            )

            # 6) UI Output
            st.success("Fertig! Report erstellt.")
            col1, col2 = st.columns(2)
            col1.image(radar_path, caption="Radar – Ebenen")
            col2.image(block_path, caption="Radar – Bausteine")

            if isinstance(ai_result, dict):
                st.markdown("### KI-generierte Empfehlungen")
                overall_summary = ai_result.get("overall_summary")
                if overall_summary:
                    st.markdown(f"**Zusammenfassung:** {overall_summary}")

                key_risks = ai_result.get("key_risks") or []
                if key_risks:
                    st.markdown("**Wesentliche Risiken:**")
                    for risk in key_risks:
                        st.markdown(f"- {risk}")

                top_actions = ai_result.get("top_actions") or []
                if top_actions:
                    with st.expander("Top-Maßnahmen anzeigen", expanded=True):
                        for i, action in enumerate(top_actions, start=1):
                            title = action.get("title", "Unbenannte Maßnahme")
                            why = action.get("why", "")
                            how = action.get("how", "")
                            prio = action.get("priority", "")
                            effort = action.get("effort", "")
                            st.markdown(f"**{i}. {title}**  ")
                            st.markdown(f"- Priorität: {prio}  ")
                            st.markdown(f"- Aufwand: {effort}  ")
                            if why:
                                st.markdown(f"- Warum: {why}  ")
                            if how:
                                st.markdown(f"- Wie: {how}  ")
                            st.write("---")

                st.success("✅ KI-Empfehlungen sind im Report enthalten.")
            else:
                if generate_ai:
                    st.warning("⚠️ Es wurden keine KI-Empfehlungen erzeugt. Der Report enthält keine KI-Seite.")
                else:
                    st.info("Die KI-Empfehlungen wurden ausgeschaltet. Der Report enthält keine KI-Seite.")

            if debug_mode:
                st.markdown("### Debug")
                st.write("Assessment ID:", assessment_id)
                st.write("Use Case:", data["use_case_name"])
                st.write("Gatekeepers:", data.get("gatekeepers", {}))
                st.write("Items (first 20):", data["items"][:20])
                st.write("Level Scores:", scores["level_scores"])
                st.write("Block Scores (Auszug):", list(scores["block_scores"].items())[:5])
                st.write("Decision:", scores.get("decision"))
                st.write("AI Result:", ai_result)

            with open(pdf_path, "rb") as f:
                st.download_button("PDF-Report herunterladen", f, file_name=f"report_{assessment_id}.pdf")

        except Exception as e:
            st.error(f"Fehler: {e}")
