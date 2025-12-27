# Solemne II - DataViz Python (Salud, datos.gob.cl)

Este proyecto consume datos públicos del Gobierno de Chile (datos.gob.cl) vía API REST (CKAN, método GET),
los analiza con pandas y los presenta en una aplicación web interactiva con Streamlit.

## Dataset configurado (MINSAL / DEIS)
- Título: **Atenciones de urgencias de causas respiratorias por semana epidemiológica**
- Dataset ID (package): `606ef5bb-11d1-475b-b69f-b980da5757f4`
- Recurso principal (parquet): `ae6c9887-106d-4e98-8875-40bf2b836041`

## Ejecutar localmente
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```
