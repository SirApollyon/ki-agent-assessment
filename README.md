# ki-agent-assessment

## Schnellstart

1. Öffne das Projekt in VS Code.
2. Aktiviere die virtuelle Umgebung:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
3. Installiere die Abhängigkeiten, falls noch nicht geschehen:
   - `.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. Starte die App aus dem Projektroot:
   - `.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py`

## Hinweise

- Nutze ausschließlich die `./.venv`-Umgebung.
- Die Ordner `.venv-1/` und `.venv-2/` sind ältere Duplikate und sollten nicht verwendet werden.
- Die App erwartet ein Excel-Template im `.xlsx`-Format.
