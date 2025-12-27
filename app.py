import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from ckan_client import package_show, resource_show, download_resource
from analysis import load_parquet_from_bytes, auto_datetime, numeric_cols, object_cols, pick_first_existing

# --- Config del proyecto (dataset real)
PACKAGE_ID = "606ef5bb-11d1-475b-b69f-b980da5757f4"  # MINSAL
RESOURCE_ID = "ae6c9887-106d-4e98-8875-40bf2b836041"  # parquet (urgencias respiratorias semanal)

st.set_page_config(page_title="Solemne II - Salud (DEIS)", layout="wide")
st.title("Solemne II · DataViz Python · Salud (DEIS/MINSAL)")
st.caption("Fuente: datos.gob.cl (Gobierno de Chile) - consumo vía API REST (GET), análisis con pandas, visualización con matplotlib y UI con Streamlit.")

with st.expander("Ver configuración del dataset (IDs y descripción)", expanded=False):
    st.write("**Dataset (package_id):**", PACKAGE_ID)
    st.write("**Recurso (resource_id):**", RESOURCE_ID)

@st.cache_data(show_spinner=False)
def fetch_metadata():
    pkg = package_show(PACKAGE_ID)
    res = resource_show(RESOURCE_ID)
    return pkg, res

@st.cache_data(show_spinner=True)
def fetch_data(download_url: str):
    content = download_resource(download_url)
    df = load_parquet_from_bytes(content)
    df = auto_datetime(df)
    return df

pkg, res = fetch_metadata()
st.subheader(pkg.get("title", "Dataset"))
st.write(pkg.get("notes", ""))

download_url = res.get("url")
st.write("**URL de descarga (GET):**", download_url)

if st.button("Cargar datos desde la API (GET)", type="primary"):
    st.session_state["df"] = fetch_data(download_url)

df = st.session_state.get("df")
if df is None:
    st.info("Presiona **Cargar datos desde la API (GET)** para descargar y analizar el dataset.")
    st.stop()

st.subheader("Vista previa")
st.dataframe(df.head(50), use_container_width=True)
st.write(f"Filas: **{len(df):,}** | Columnas: **{len(df.columns)}**")

# --- Limpieza mínima / nulos
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("### Nulos por columna")
    st.dataframe(df.isna().sum().sort_values(ascending=False).to_frame("nulos"), use_container_width=True)
with col2:
    st.markdown("### Descripción numérica")
    st.dataframe(df.describe(include="number").T, use_container_width=True)

# --- Selección de variables (genérico + sugerencias típicas DEIS)
st.subheader("Exploración interactiva")
num = numeric_cols(df)
cat = object_cols(df)

# Sugerencias típicas (si existen)
year_col = pick_first_existing(df, ["anio", "anio_estadistico", "AÑO", "Anio", "year"])
week_col = pick_first_existing(df, ["semana", "semana_epidemiologica", "Semana", "SE"])
region_col = pick_first_existing(df, ["region", "Region", "REGION"])
cause_col = pick_first_existing(df, ["causa", "Causa", "diagnostico", "Diagnostico"])

left, right = st.columns([1, 1])
with left:
    y = st.selectbox("Variable numérica a analizar (Y)", options=num if num else df.columns.tolist())
with right:
    group_candidates = [c for c in [region_col, cause_col, year_col, week_col] if c is not None]
    group_default = group_candidates[0] if group_candidates else (cat[0] if cat else df.columns[0])
    group_by = st.selectbox("Agrupar por (categoría)", options=df.columns.tolist(), index=list(df.columns).index(group_default))

# Filtros básicos (si hay año/semana)
filters = {}
if year_col and pd.api.types.is_numeric_dtype(df[year_col]):
    yr_min, yr_max = int(df[year_col].min()), int(df[year_col].max())
    yr_range = st.slider("Filtrar por año", min_value=yr_min, max_value=yr_max, value=(yr_min, yr_max))
    filters[year_col] = yr_range

if week_col and pd.api.types.is_numeric_dtype(df[week_col]):
    w_min, w_max = int(df[week_col].min()), int(df[week_col].max())
    w_range = st.slider("Filtrar por semana epidemiológica", min_value=w_min, max_value=w_max, value=(w_min, w_max))
    filters[week_col] = w_range

df_f = df.copy()
for col, (a, b) in filters.items():
    df_f = df_f[(df_f[col] >= a) & (df_f[col] <= b)]

st.write(f"Filas tras filtros: **{len(df_f):,}**")

# --- Gráficos
chart_type = st.selectbox("Tipo de gráfico", ["Barras (Top N)", "Serie temporal (si existe)", "Histograma"])
if chart_type == "Barras (Top N)":
    topn = st.slider("Top N", 5, 30, 10)
    agg = df_f.groupby(group_by)[y].mean(numeric_only=True).sort_values(ascending=False).head(topn)
    fig = plt.figure()
    plt.bar(agg.index.astype(str), agg.values)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel(f"Promedio de {y}")
    plt.title(f"Promedio de {y} por {group_by} (Top {topn})")
    st.pyplot(fig)

elif chart_type == "Serie temporal (si existe)":
    # Preferimos año+semana si existen; si no, intentamos con una fecha
    date_like_cols = [c for c in df_f.columns if pd.api.types.is_datetime64_any_dtype(df_f[c])]
    if year_col and week_col and pd.api.types.is_numeric_dtype(df_f[year_col]) and pd.api.types.is_numeric_dtype(df_f[week_col]):
        tmp = df_f[[year_col, week_col, y]].dropna()
        tmp = tmp.groupby([year_col, week_col])[y].mean().reset_index()
        tmp["t"] = tmp[year_col].astype(int).astype(str) + "-SE" + tmp[week_col].astype(int).astype(str).str.zfill(2)
        fig = plt.figure()
        plt.plot(tmp["t"], tmp[y])
        plt.xticks(rotation=60, ha="right")
        plt.ylabel(y)
        plt.title(f"Evolución de {y} por año y semana epidemiológica")
        st.pyplot(fig)
    elif date_like_cols:
        dcol = st.selectbox("Columna de fecha", date_like_cols)
        tmp = df_f[[dcol, y]].dropna().sort_values(dcol)
        tmp = tmp.set_index(dcol)[y].resample("W").mean()
        fig = plt.figure()
        plt.plot(tmp.index, tmp.values)
        plt.ylabel(y)
        plt.title(f"Promedio semanal de {y}")
        st.pyplot(fig)
    else:
        st.warning("No se encontró una estructura temporal (año/semana o fecha) para graficar serie.")
else:
    bins = st.slider("Bins", 5, 100, 20)
    fig = plt.figure()
    plt.hist(df_f[y].dropna(), bins=bins)
    plt.title(f"Histograma de {y}")
    plt.xlabel(y)
    plt.ylabel("Frecuencia")
    st.pyplot(fig)

st.success("Listo: consumo API (GET) + análisis (pandas) + visualización (matplotlib) + interacción (Streamlit).")
