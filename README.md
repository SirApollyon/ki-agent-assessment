# ki-agent-assessment

## Schnellstart

1. Projekt in VS Code öffnen.
2. Virtuelle Umgebung aktivieren.
   Windows PowerShell: `.venv\Scripts\Activate.ps1`
3. Abhängigkeiten installieren, falls nötig.
   `.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. App aus dem Projektroot starten.
   `.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py`

## Hinweise

- Ausschließlich die `./.venv`-Umgebung verwenden.
- Die Ordner `.venv-1/` und `.venv-2/` sind ältere Duplikate und sollten nicht genutzt werden.
- Die App erwartet ein Excel-Template im `.xlsx`-Format.
- Für KI-Empfehlungen muss in der `.env` im Projektroot ein `OPENAI_API_KEY` gesetzt sein.
