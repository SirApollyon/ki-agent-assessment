# -*- coding: utf-8 -*-
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.ai_recommendations import generate_recommendations
from app.core.excel_io import load_workbook, read_inputs
from app.core.radar import block_radar_chart, radar_chart
from app.core.report import build_pdf
from app.core.scoring import compute_scores

UPLOAD_DIR = ROOT_DIR / "data" / "uploads"
OUTPUT_DIR = ROOT_DIR / "data" / "outputs"


def _ensure_output_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _is_api_key_loaded() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _render_ai_result(ai_result: dict[str, Any] | None, generate_ai: bool) -> None:
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
                for index, action in enumerate(top_actions, start=1):
                    st.markdown(f"**{index}. {action.get('title', 'Unbenannte Maßnahme')}**")
                    st.markdown(f"- Priorität: {action.get('priority', '')}")
                    st.markdown(f"- Aufwand: {action.get('effort', '')}")
                    if action.get("why"):
                        st.markdown(f"- Warum: {action['why']}")
                    if action.get("how"):
                        st.markdown(f"- Wie: {action['how']}")
                    st.write("---")

        st.success("✅ KI-Empfehlungen sind im Report enthalten.")
        return

    if generate_ai:
        st.warning("⚠️ Es wurden keine KI-Empfehlungen erzeugt. Der Report enthält keine KI-Seite.")
    else:
        st.info("Die KI-Empfehlungen wurden ausgeschaltet. Der Report enthält keine KI-Seite.")


def _render_debug(assessment_id: str, data: dict[str, Any], scores: dict[str, Any], ai_result: dict[str, Any] | None) -> None:
    st.markdown("### Debug")
    st.write("Assessment ID:", assessment_id)
    st.write("Use Case:", data["use_case_name"])
    st.write("Gatekeepers:", data.get("gatekeepers", {}))
    st.write("Items (first 20):", data["items"][:20])
    st.write("Level Scores:", scores["level_scores"])
    st.write("Block Scores (Auszug):", list(scores["block_scores"].items())[:5])
    st.write("Decision:", scores.get("decision"))
    st.write("AI Result:", ai_result)


def _generate_ai_result(
    generate_ai: bool,
    api_key_loaded: bool,
    data: dict[str, Any],
    scores: dict[str, Any],
    detail_level: str,
) -> dict[str, Any] | None:
    if not generate_ai:
        st.info("KI-Empfehlungen deaktiviert.")
        return None

    if not api_key_loaded:
        st.error(
            "OPENAI_API_KEY ist nicht gesetzt. Trage in der Datei .env im Projektverzeichnis "
            "zum Beispiel 'OPENAI_API_KEY=dein_api_key' ein und starte die App danach neu."
        )
        st.info("Die Auswertung läuft weiter, aber ohne KI-Empfehlungen.")
        return None

    st.info("⏳ Generiere KI-Empfehlungen …")
    try:
        ai_result = generate_recommendations(
            use_case_name=data["use_case_name"],
            scores=scores,
            gatekeepers=data.get("gatekeepers", {}),
            detail_level=detail_level,
        )
        st.success("✅ KI-Empfehlungen wurden generiert.")
        return ai_result
    except Exception as error:
        st.error(f"⚠️ KI-Generierung fehlgeschlagen: {error}")
        return None


def main() -> None:
    load_dotenv()
    _ensure_output_dirs()

    st.set_page_config(page_title="KI-Potenzialanalyse", layout="centered")
    st.title("KI-Potenzialanalyse für generative KI-Agenten (KMU)")
    st.write("Excel hochladen → Auswertung mit Radar und Report automatisch erhalten.")

    with st.expander("Optionen", expanded=True):
        generate_ai = st.checkbox("KI-Empfehlungen generieren", value=True)
        detail_level = st.selectbox("Detailgrad", ["Kurz", "Standard", "Detailliert"], index=1)
        debug_mode = st.checkbox("Debug anzeigen", value=False)

    api_key_loaded = _is_api_key_loaded()
    st.caption(f"OPENAI_API_KEY geladen: {'✅ Ja' if api_key_loaded else '❌ Nein'}")
    if not api_key_loaded:
        st.caption("Erwarteter Eintrag in .env: OPENAI_API_KEY=dein_api_key")

    uploaded_file = st.file_uploader("Excel-Template (.xlsx) hochladen", type=["xlsx"])
    if not uploaded_file:
        return

    assessment_id = str(uuid.uuid4())[:8]
    output_dir = OUTPUT_DIR / assessment_id
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = UPLOAD_DIR / f"{assessment_id}.xlsx"
    workbook_path.write_bytes(uploaded_file.getbuffer())

    if not st.button("Auswerten"):
        return

    try:
        workbook = load_workbook(str(workbook_path))
        data = read_inputs(workbook)
        scores = compute_scores(data["items"], data.get("gatekeepers", {}))
        ai_result = _generate_ai_result(generate_ai, api_key_loaded, data, scores, detail_level)

        radar_path = output_dir / "radar_levels.png"
        block_path = output_dir / "radar_blocks.png"
        radar_chart(scores["level_scores"], str(radar_path))
        block_radar_chart(scores["block_scores"], str(block_path))

        pdf_path = output_dir / "report.pdf"
        build_pdf(
            report_path=str(pdf_path),
            use_case_name=data["use_case_name"],
            scores=scores,
            radar_path=str(radar_path),
            block_path=str(block_path),
            ai_result=ai_result,
        )

        st.success("Fertig! Report erstellt.")
        left_column, right_column = st.columns(2)
        left_column.image(str(radar_path), caption="Radar – Ebenen")
        right_column.image(str(block_path), caption="Radar – Bausteine")

        _render_ai_result(ai_result, generate_ai)

        if debug_mode:
            _render_debug(assessment_id, data, scores, ai_result)

        with pdf_path.open("rb") as pdf_file:
            st.download_button(
                "PDF-Report herunterladen",
                pdf_file,
                file_name=f"report_{assessment_id}.pdf",
            )
    except Exception as error:
        st.error(f"Fehler: {error}")


if __name__ == "__main__":
    main()
