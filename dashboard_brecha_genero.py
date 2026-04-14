"""
=============================================================================
DASHBOARD ANALÍTICO: BRECHA DE GÉNERO EN BOLIVIA, ECUADOR Y PERÚ
=============================================================================
Herramienta: Streamlit + Plotly
Fuente de datos: Google Drive (CONSOLIDADO.CSV)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import requests
import io
import sys

warnings.filterwarnings("ignore")

# Configuración de la página
st.set_page_config(
    page_title="Brecha de Género | Bolivia · Ecuador · Perú",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constantes
COLOR_HOMBRE   = "#1A6FA8"
COLOR_MUJER    = "#C0392B"
COLOR_NEUTRAL  = "#2C3E50"
COLOR_BG       = "#F4F6F9"
COLOR_ACCENT   = "#27AE60"

COLORES_PAISES = {
    "Bolivia": "#E74C3C",
    "Ecuador": "#F39C12",
    "Perú":    "#2980B9",
}

GENDER_MAP   = {1: "Hombre", 2: "Mujer", "1": "Hombre", "2": "Mujer",
                "M": "Hombre", "F": "Mujer", "HOMBRE": "Hombre", "MUJER": "Mujer"}
AREA_MAP     = {1: "Urbano", 2: "Rural", "1": "Urbano", "2": "Rural",
                "U": "Urbano", "R": "Rural", "URBANO": "Urbano", "RURAL": "Rural"}

EXCHANGE_RATES = {
    "Bolivia": 1 / 6.91,
    "Ecuador": 1.0,
    "Perú":    1 / 3.75,
}

# CSS personalizado
st.markdown("""
<style>
.stApp { background-color: #F4F6F9; }
.main-header {
    background: linear-gradient(135deg, #1A2A4A 0%, #1A6FA8 100%);
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.main-header h1 { color: #FFFFFF; font-size: 2rem; font-weight: 700; margin: 0; }
.main-header p  { color: #B8D4EA; font-size: 1rem; margin: 0.4rem 0 0 0; }
.kpi-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border-left: 5px solid #1A6FA8;
    margin-bottom: 1rem;
}
.kpi-card.red   { border-left-color: #C0392B; }
.kpi-card.green { border-left-color: #27AE60; }
.kpi-card.gold  { border-left-color: #F39C12; }
.kpi-label { font-size: 0.78rem; color: #7F8C8D; font-weight: 600;
             text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: #2C3E50; line-height: 1.2; }
.kpi-sub   { font-size: 0.82rem; color: #95A5A6; margin-top: 0.2rem; }
.section-title {
    font-size: 1.1rem; font-weight: 700; color: #1A2A4A;
    border-bottom: 3px solid #1A6FA8; padding-bottom: 0.4rem;
    margin: 1.5rem 0 1rem 0;
}
section[data-testid="stSidebar"] { background-color: #1A2A4A; }
section[data-testid="stSidebar"] * { color: #ECF0F1 !important; }
.insight-box {
    background: #EBF5FB;
    border-left: 4px solid #1A6FA8;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.5rem 0;
    font-size: 0.88rem;
    color: #1A2A4A;
}
.insight-box.warning { background: #FDEDEC; border-left-color: #C0392B; }
.insight-box.success { background: #EAFAF1; border-left-color: #27AE60; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS DESDE GOOGLE DRIVE
# ─────────────────────────────────────────────────────────────────────────────
GDRIVE_FILE_ID = "1GdoiBHtLbmZzCI81_V094ozqzksaaR3y"

@st.cache_data(show_spinner="Cargando datos desde Google Drive…", ttl=3600)
def cargar_datos() -> pd.DataFrame:
    """
    Descarga el CSV desde Google Drive y lo procesa.
    """
    def download_file_from_google_drive(id):
        URL = "https://docs.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(URL, params={'id': id}, stream=True)
        
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                params = {'id': id, 'confirm': value}
                response = session.get(URL, params=params, stream=True)
                break
        
        return response.content
    
    try:
        file_content = download_file_from_google_drive(GDRIVE_FILE_ID)
        
        # Intentar diferentes codificaciones
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding='latin-1')
            except:
                df = pd.read_csv(io.BytesIO(file_content), encoding='iso-8859-1')
        
        if df.empty:
            st.error("El archivo CSV está vacío")
            st.stop()
            
    except Exception as e:
        st.error(f"❌ No se pudo descargar el archivo desde Google Drive.\n\nError: {str(e)}\n\n"
                 "Verifique que el archivo esté compartido como 'Cualquier persona con el enlace puede ver'.\n\n"
                 "También puede intentar descargar manualmente el archivo y subirlo a la aplicación.")
        
        # Opción alternativa: permitir subir archivo manualmente
        st.info("📁 Como alternativa, puede subir el archivo CSV manualmente:")
        uploaded_file = st.file_uploader("Subir archivo CONSOLIDADO.csv", type=['csv'])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                df = pd.read_csv(uploaded_file, encoding='latin-1')
        else:
            st.stop()
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.upper()
    
    # Mapeo de columnas
    rename_map = {}
    for col in df.columns:
        if "ANIO" in col and "ESTUD" in col:
            rename_map[col] = "ANIOS_ESTUDIO"
        elif "INGRESO" in col and ("LAB" in col or "OCP" in col or "MES" in col):
            rename_map[col] = "INGRESO_LABORAL_OCP_PPAL_MES"
        elif "FACTOR" in col and "EXPAN" in col:
            rename_map[col] = "FACTOR_EXPANSION_ANUAL"
        elif col in ("AREA", "ZONA"):
            rename_map[col] = "AREA"
        elif "ACTIVIDAD" in col or "SECTOR" in col or "RAMA" in col:
            rename_map[col] = "ACTIVIDAD_ECONOMICA"
        elif col in ("SEXO", "GENERO", "GENDER", "SEX"):
            rename_map[col] = "SEXO"
        elif col in ("PAIS", "PAÍS", "COUNTRY"):
            rename_map[col] = "PAIS"
    
    df.rename(columns=rename_map, inplace=True)
    
    # Verificar columnas requeridas
    required = ["ANIOS_ESTUDIO", "INGRESO_LABORAL_OCP_PPAL_MES",
                "FACTOR_EXPANSION_ANUAL", "AREA", "ACTIVIDAD_ECONOMICA",
                "SEXO", "PAIS"]
    
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.warning(f"⚠️ Columnas no encontradas: {missing}")
        st.info(f"Columnas disponibles: {list(df.columns)[:15]}")
        
        # Crear columnas dummy si es necesario
        for col in missing:
            if col == "FACTOR_EXPANSION_ANUAL":
                df[col] = 1.0
            elif col in ["ANIOS_ESTUDIO", "INGRESO_LABORAL_OCP_PPAL_MES"]:
                df[col] = np.nan
            else:
                df[col] = "No Especificado"
    
    # Procesar SEXO
    df["SEXO"] = df["SEXO"].astype(str).str.strip().str.upper()
    df["SEXO"] = df["SEXO"].map(lambda x: GENDER_MAP.get(x, GENDER_MAP.get(x[:1], x)))
    
    # Procesar AREA
    if "AREA" in df.columns:
        df["AREA"] = df["AREA"].astype(str).str.strip().str.upper()
        df["AREA"] = df["AREA"].map(lambda x: AREA_MAP.get(x, AREA_MAP.get(x[:1], "Urbano")))
    
    # Procesar PAIS
    pais_norm = {"BOLIVIA": "Bolivia", "ECUADOR": "Ecuador",
                 "PERU": "Perú", "PERÚ": "Perú"}
    df["PAIS"] = df["PAIS"].astype(str).str.strip().str.upper()
    df["PAIS"] = df["PAIS"].map(lambda x: pais_norm.get(x, x.capitalize()))
    
    # Convertir columnas numéricas
    for col in ["INGRESO_LABORAL_OCP_PPAL_MES", "FACTOR_EXPANSION_ANUAL", "ANIOS_ESTUDIO"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Limpiar valores atípicos
    if "INGRESO_LABORAL_OCP_PPAL_MES" in df.columns:
        df.loc[df["INGRESO_LABORAL_OCP_PPAL_MES"] < 0, "INGRESO_LABORAL_OCP_PPAL_MES"] = np.nan
    
    if "ANIOS_ESTUDIO" in df.columns:
        df.loc[df["ANIOS_ESTUDIO"] < 0, "ANIOS_ESTUDIO"] = np.nan
        df.loc[df["ANIOS_ESTUDIO"] > 30, "ANIOS_ESTUDIO"] = np.nan
    
    if "FACTOR_EXPANSION_ANUAL" in df.columns:
        df.loc[df["FACTOR_EXPANSION_ANUAL"] <= 0, "FACTOR_EXPANSION_ANUAL"] = np.nan
        df["FACTOR_EXPANSION_ANUAL"] = df["FACTOR_EXPANSION_ANUAL"].fillna(1.0)
    
    # Filtrar valores válidos
    df = df.dropna(subset=["SEXO", "PAIS"])
    df = df[df["SEXO"].isin(["Hombre", "Mujer"])]
    df = df[df["PAIS"].isin(["Bolivia", "Ecuador", "Perú"])]
    
    # Calcular ingreso en USD
    if "INGRESO_LABORAL_OCP_PPAL_MES" in df.columns:
        df["INGRESO_USD"] = df.apply(
            lambda row: row["INGRESO_LABORAL_OCP_PPAL_MES"] * EXCHANGE_RATES.get(row["PAIS"], 1.0)
            if pd.notna(row["INGRESO_LABORAL_OCP_PPAL_MES"]) else np.nan,
            axis=1
        )
        
        # Eliminar outliers extremos
        if len(df) > 0:
            q995 = df["INGRESO_USD"].quantile(0.995)
            df.loc[df["INGRESO_USD"] > q995, "INGRESO_USD"] = np.nan
    
    # Procesar actividad económica
    if "ACTIVIDAD_ECONOMICA" in df.columns:
        df["ACTIVIDAD_ECONOMICA"] = (df["ACTIVIDAD_ECONOMICA"]
            .astype(str).str.strip().str.title()
            .replace({"Nan": "No Especificado", "None": "No Especificado", "": "No Especificado"}))
    
    return df


def ingreso_ponderado(grupo):
    if "INGRESO_USD" not in grupo.columns or "FACTOR_EXPANSION_ANUAL" not in grupo.columns:
        return np.nan
    mask = grupo["INGRESO_USD"].notna()
    if mask.sum() == 0:
        return np.nan
    g = grupo[mask]
    return np.average(g["INGRESO_USD"], weights=g["FACTOR_EXPANSION_ANUAL"])


def estudio_ponderado(grupo):
    if "ANIOS_ESTUDIO" not in grupo.columns:
        return np.nan
    mask = grupo["ANIOS_ESTUDIO"].notna()
    if mask.sum() == 0:
        return np.nan
    g = grupo[mask]
    return np.average(g["ANIOS_ESTUDIO"], weights=g["FACTOR_EXPANSION_ANUAL"])


def brecha_salarial(ingreso_h, ingreso_m):
    if ingreso_h and ingreso_h > 0 and not np.isnan(ingreso_h):
        return (ingreso_h - ingreso_m) / ingreso_h * 100
    return np.nan


def tarjeta_kpi(label, valor, sub="", color=""):
    clase = f"kpi-card {color}"
    return f"""
    <div class="{clase}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{valor}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""


def layout_base():
    return dict(
        template="plotly_white",
        font=dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50"),
        title_font=dict(size=14, color="#1A2A4A", family="Inter, Arial, sans-serif"),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#DEE2E6", borderwidth=1,
        ),
        margin=dict(l=40, r=40, t=70, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12),
    )


def grafico_barras_ingresos(df_filtrado):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    datos = (df_filtrado.dropna(subset=["INGRESO_USD"])
             .groupby(["PAIS", "SEXO"])
             .apply(ingreso_ponderado)
             .reset_index(name="INGRESO_USD"))
    
    if datos.empty:
        return go.Figure()
    
    fig = px.bar(
        datos, x="PAIS", y="INGRESO_USD", color="SEXO",
        barmode="group",
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER},
        text=datos["INGRESO_USD"].apply(lambda v: f"${v:,.0f}"),
        labels={"INGRESO_USD": "Ingreso mensual (USD)", "PAIS": "País", "SEXO": "Sexo"},
        title="Ingreso Mensual Promedio (USD) por País y Sexo",
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(**layout_base())
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig


def grafico_brecha_paises(df_filtrado):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    rows = []
    for pais, g in df_filtrado.dropna(subset=["INGRESO_USD"]).groupby("PAIS"):
        ih = ingreso_ponderado(g[g["SEXO"] == "Hombre"])
        im = ingreso_ponderado(g[g["SEXO"] == "Mujer"])
        b  = brecha_salarial(ih, im)
        if not np.isnan(b):
            rows.append({"PAIS": pais, "BRECHA": b})
    
    if not rows:
        return go.Figure()
    
    datos = pd.DataFrame(rows).sort_values("BRECHA", ascending=True)
    colors = [COLOR_HOMBRE if v > 0 else COLOR_MUJER for v in datos["BRECHA"]]
    fig = go.Figure(go.Bar(
        x=datos["BRECHA"], y=datos["PAIS"],
        orientation="h",
        marker_color=colors,
        text=datos["BRECHA"].apply(lambda v: f"{v:+.1f}%"),
        textposition="outside",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#95A5A6")
    fig.update_layout(
        title="Brecha Salarial de Género (%) por País<br>"
              "<sup>Positivo = hombres ganan más | Negativo = mujeres ganan más</sup>",
        xaxis_title="Brecha salarial (%)",
        yaxis_title="País",
        **layout_base()
    )
    return fig


def boxplot_ingresos(df_filtrado):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    df_bp = df_filtrado.dropna(subset=["INGRESO_USD"])
    if df_bp.empty:
        return go.Figure()
    
    fig = px.box(
        df_bp, x="PAIS", y="INGRESO_USD", color="SEXO",
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER},
        labels={"INGRESO_USD": "Ingreso mensual (USD)", "PAIS": "País", "SEXO": "Sexo"},
        title="Distribución del Ingreso Mensual (USD) por País y Sexo",
        points=False,
    )
    fig.update_layout(**layout_base())
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig


def grafico_educacion(df_filtrado):
    if "ANIOS_ESTUDIO" not in df_filtrado.columns:
        return go.Figure()
    
    datos = (df_filtrado.dropna(subset=["ANIOS_ESTUDIO"])
             .groupby(["PAIS", "SEXO"])
             .apply(estudio_ponderado)
             .reset_index(name="ANIOS_ESTUDIO"))
    
    if datos.empty:
        return go.Figure()
    
    fig = px.bar(
        datos, x="PAIS", y="ANIOS_ESTUDIO", color="SEXO",
        barmode="group",
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER},
        text=datos["ANIOS_ESTUDIO"].apply(lambda v: f"{v:.1f}"),
        labels={"ANIOS_ESTUDIO": "Años de estudio (promedio)", "PAIS": "País", "SEXO": "Sexo"},
        title="Años de Estudio Promedio por País y Sexo",
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(**layout_base())
    return fig


def grafico_participacion(df_filtrado):
    datos = (df_filtrado.groupby("SEXO")["FACTOR_EXPANSION_ANUAL"]
             .sum().reset_index())
    total = datos["FACTOR_EXPANSION_ANUAL"].sum()
    if total == 0:
        return go.Figure()
    
    datos["PCT"] = datos["FACTOR_EXPANSION_ANUAL"] / total * 100
    fig = px.pie(
        datos, names="SEXO", values="PCT",
        color="SEXO",
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER},
        hole=0.45,
        title="Participación Laboral por Sexo (%)",
    )
    fig.update_traces(texttemplate="%{label}<br><b>%{value:.1f}%</b>", textfont_size=13)
    fig.update_layout(**layout_base())
    return fig


def grafico_area_urbano_rural(df_filtrado):
    if "INGRESO_USD" not in df_filtrado.columns or "AREA" not in df_filtrado.columns:
        return go.Figure()
    
    df_area = df_filtrado[df_filtrado["AREA"].isin(["Urbano", "Rural"])]
    if df_area.empty:
        return go.Figure()
    
    datos = (df_area.dropna(subset=["INGRESO_USD"])
             .groupby(["AREA", "SEXO"])
             .apply(ingreso_ponderado)
             .reset_index(name="INGRESO_USD"))
    
    if datos.empty:
        return go.Figure()
    
    fig = px.bar(
        datos, x="AREA", y="INGRESO_USD", color="SEXO",
        barmode="group",
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER},
        text=datos["INGRESO_USD"].apply(lambda v: f"${v:,.0f}"),
        labels={"INGRESO_USD": "Ingreso mensual (USD)", "AREA": "Área", "SEXO": "Sexo"},
        title="Ingreso Mensual Promedio (USD) por Área y Sexo",
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(**layout_base())
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig


def grafico_brecha_por_sector(df_filtrado, top_n=12):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    rows = []
    df_ing = df_filtrado.dropna(subset=["INGRESO_USD"])
    
    for sector, g in df_ing.groupby("ACTIVIDAD_ECONOMICA"):
        if sector in ("No Especificado", "nan", "Nan", "None"):
            continue
        ih = ingreso_ponderado(g[g["SEXO"] == "Hombre"])
        im = ingreso_ponderado(g[g["SEXO"] == "Mujer"])
        if pd.isna(ih) or pd.isna(im) or ih == 0:
            continue
        n  = g["FACTOR_EXPANSION_ANUAL"].sum()
        rows.append({"Sector": sector, "BRECHA": brecha_salarial(ih, im), "N": n})
    
    if not rows:
        return go.Figure()
    
    datos = (pd.DataFrame(rows).nlargest(top_n, "N").sort_values("BRECHA", ascending=True))
    colors = [COLOR_HOMBRE if v > 0 else COLOR_MUJER for v in datos["BRECHA"]]
    fig = go.Figure(go.Bar(
        x=datos["BRECHA"], y=datos["Sector"],
        orientation="h",
        marker_color=colors,
        text=datos["BRECHA"].apply(lambda v: f"{v:+.1f}%"),
        textposition="outside",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#95A5A6")
    fig.update_layout(
        title=f"Brecha Salarial (%) por Actividad Económica — Top {top_n} sectores",
        xaxis_title="Brecha salarial (%)",
        yaxis_title="",
        height=500,
        **layout_base()
    )
    return fig


def grafico_ingreso_sector(df_filtrado, top_n=10):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    df_ing = df_filtrado.dropna(subset=["INGRESO_USD"])
    if df_ing.empty:
        return go.Figure()
    
    top_sectores = (df_ing.groupby("ACTIVIDAD_ECONOMICA")["FACTOR_EXPANSION_ANUAL"]
                    .sum().nlargest(top_n).index.tolist())
    
    datos = (df_ing[df_ing["ACTIVIDAD_ECONOMICA"].isin(top_sectores)]
             .groupby(["ACTIVIDAD_ECONOMICA", "SEXO"])
             .apply(ingreso_ponderado)
             .reset_index(name="INGRESO_USD"))
    
    if datos.empty:
        return go.Figure()
    
    fig = px.bar(
        datos, x="ACTIVIDAD_ECONOMICA", y="INGRESO_USD", color="SEXO",
        barmode="group",
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER},
        labels={"INGRESO_USD": "Ingreso mensual (USD)",
                "ACTIVIDAD_ECONOMICA": "Actividad económica", "SEXO": "Sexo"},
        title=f"Ingreso Mensual (USD) por Actividad Económica — Top {top_n} sectores",
    )
    fig.update_layout(height=480, xaxis_tickangle=-35, **layout_base())
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig


def grafico_radar_paises(df_filtrado):
    indicadores = []
    for pais, g in df_filtrado.groupby("PAIS"):
        ih = ingreso_ponderado(g[g["SEXO"] == "Hombre"])
        im = ingreso_ponderado(g[g["SEXO"] == "Mujer"])
        eh = estudio_ponderado(g[g["SEXO"] == "Hombre"])
        em = estudio_ponderado(g[g["SEXO"] == "Mujer"])
        part_m = (g[g["SEXO"] == "Mujer"]["FACTOR_EXPANSION_ANUAL"].sum() /
                  g["FACTOR_EXPANSION_ANUAL"].sum() * 100) if not g.empty else 0
        brecha = abs(brecha_salarial(ih, im)) if (ih and im and not np.isnan(ih) and not np.isnan(im)) else np.nan
        
        if not np.isnan(ih) and not np.isnan(im):
            indicadores.append({
                "PAIS": pais, "Ingreso H (norm)": ih, "Ingreso M (norm)": im,
                "Estudio H": eh, "Estudio M": em,
                "Part. Mujer (%)": part_m, "Brecha (%)": brecha,
            })
    
    if not indicadores:
        return go.Figure()
    
    df_r = pd.DataFrame(indicadores).set_index("PAIS")
    df_norm = df_r.copy()
    
    for col in df_norm.columns:
        mn, mx = df_norm[col].min(), df_norm[col].max()
        if mx > mn:
            df_norm[col] = (df_norm[col] - mn) / (mx - mn) * 100
        else:
            df_norm[col] = 50
    
    cats = list(df_norm.columns)
    fig = go.Figure()
    
    for pais in df_norm.index:
        vals = df_norm.loc[pais].tolist()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", name=pais,
            line_color=COLORES_PAISES.get(pais, "#888"), opacity=0.7,
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Comparación Multi-Indicador entre Países (normalizado 0–100)",
        **layout_base()
    )
    return fig


def grafico_burbuja_sectores(df_filtrado, top_n=15):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    rows = []
    df_ing = df_filtrado.dropna(subset=["INGRESO_USD"])
    
    for sector, g in df_ing.groupby("ACTIVIDAD_ECONOMICA"):
        if sector in ("No Especificado", "nan", "Nan", "None"):
            continue
        ih  = ingreso_ponderado(g[g["SEXO"] == "Hombre"])
        im  = ingreso_ponderado(g[g["SEXO"] == "Mujer"])
        if pd.isna(ih) or pd.isna(im) or ih == 0 or im == 0:
            continue
        masa = g["FACTOR_EXPANSION_ANUAL"].sum()
        b    = brecha_salarial(ih, im)
        rows.append({"Sector": sector, "Ingreso H": ih, "Ingreso M": im, "Masa": masa, "Brecha": b})
    
    if not rows:
        return go.Figure()
    
    datos = pd.DataFrame(rows).nlargest(top_n, "Masa").reset_index(drop=True)
    masa_min, masa_max = datos["Masa"].min(), datos["Masa"].max()
    
    if masa_max > masa_min:
        datos["Tamaño"] = 15 + 55 * (datos["Masa"] - masa_min) / (masa_max - masa_min)
    else:
        datos["Tamaño"] = 35
    
    colorscale = [[0.0, "#27AE60"], [0.4, "#F39C12"], [1.0, "#C0392B"]]
    max_val = max(datos["Ingreso H"].max(), datos["Ingreso M"].max()) * 1.1
    min_val = min(datos["Ingreso H"].min(), datos["Ingreso M"].min()) * 0.9
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[min_val, max_val], y=[min_val, max_val],
        mode="lines", line=dict(dash="dash", color="#BDC3C7", width=1.5),
        name="Paridad salarial (H = M)", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=datos["Ingreso H"], y=datos["Ingreso M"],
        mode="markers+text",
        marker=dict(
            size=datos["Tamaño"], color=datos["Brecha"],
            colorscale=colorscale,
            colorbar=dict(title="Brecha<br>salarial (%)", ticksuffix="%", thickness=14, len=0.7),
            line=dict(color="white", width=1.5), opacity=0.85,
            cmin=datos["Brecha"].min(), cmax=datos["Brecha"].max(),
        ),
        text=datos["Sector"], textposition="top center",
        textfont=dict(size=9, color="#2C3E50"),
        customdata=datos[["Brecha", "Masa"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>Ingreso hombres: $%{x:,.0f} USD<br>"
            "Ingreso mujeres: $%{y:,.0f} USD<br>Brecha salarial: %{customdata[0]:.1f}%<br>"
            "Trabajadores (expansión): %{customdata[1]:,.0f}<extra></extra>"
        ),
        name="Sectores económicos",
    ))
    fig.update_layout(
        title="Mapa de Brechas por Sector: Ingreso Hombres vs. Mujeres (USD)",
        xaxis=dict(title="Ingreso mensual promedio — Hombres (USD)", tickprefix="$", tickformat=",.0f"),
        yaxis=dict(title="Ingreso mensual promedio — Mujeres (USD)", tickprefix="$", tickformat=",.0f"),
        height=580, **layout_base(),
    )
    return fig


def grafico_violin_ingresos(df_filtrado):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    df_vio = df_filtrado.dropna(subset=["INGRESO_USD"])
    if df_vio.empty:
        return go.Figure()
    
    fig = go.Figure()
    paises = sorted(df_vio["PAIS"].unique())
    
    for i, pais in enumerate(paises):
        for sexo, color in [("Hombre", COLOR_HOMBRE), ("Mujer", COLOR_MUJER)]:
            datos_sexo = df_vio[(df_vio["PAIS"] == pais) & (df_vio["SEXO"] == sexo)]["INGRESO_USD"]
            if len(datos_sexo) < 10:
                continue
            muestra = datos_sexo.sample(min(len(datos_sexo), 2000), random_state=42)
            fig.add_trace(go.Violin(
                x=[pais] * len(muestra), y=muestra, name=sexo,
                legendgroup=sexo, showlegend=(i == 0),
                side="negative" if sexo == "Hombre" else "positive",
                line_color=color, fillcolor=color, opacity=0.55,
                meanline_visible=True, meanline=dict(color=color, width=2),
                points=False, bandwidth=30,
            ))
    
    fig.update_layout(
        title="Distribución Completa del Ingreso Mensual (USD) por País y Sexo",
        yaxis=dict(title="Ingreso mensual (USD)", tickprefix="$", tickformat=",.0f"),
        xaxis_title="País", violingap=0.05, violinmode="overlay",
        height=500, **layout_base(),
    )
    return fig


def grafico_heatmap_brecha(df_filtrado, top_n=12):
    if "INGRESO_USD" not in df_filtrado.columns:
        return go.Figure()
    
    df_ing = df_filtrado.dropna(subset=["INGRESO_USD"])
    rows = []
    
    for (pais, sector), g in df_ing.groupby(["PAIS", "ACTIVIDAD_ECONOMICA"]):
        if sector in ("No Especificado", "nan", "Nan", "None"):
            continue
        ih = ingreso_ponderado(g[g["SEXO"] == "Hombre"])
        im = ingreso_ponderado(g[g["SEXO"] == "Mujer"])
        if pd.isna(ih) or pd.isna(im) or ih == 0:
            continue
        n = g["FACTOR_EXPANSION_ANUAL"].sum()
        rows.append({"PAIS": pais, "Sector": sector, "Brecha": brecha_salarial(ih, im), "N": n})
    
    if not rows:
        return go.Figure()
    
    df_heat = pd.DataFrame(rows)
    top_sectores = df_heat.groupby("Sector")["N"].sum().nlargest(top_n).index.tolist()
    df_heat = df_heat[df_heat["Sector"].isin(top_sectores)]
    pivot = df_heat.pivot_table(index="Sector", columns="PAIS", values="Brecha", aggfunc="mean")
    pivot["_media"] = pivot.mean(axis=1)
    pivot = pivot.sort_values("_media", ascending=False).drop(columns="_media")
    
    z_vals   = pivot.values.tolist()
    y_labels = list(pivot.index)
    x_labels = list(pivot.columns)
    text_vals = [[f"{v:+.1f}%" if not np.isnan(v) else "N/D" for v in fila] for fila in z_vals]
    
    fig = go.Figure(go.Heatmap(
        z=z_vals, x=x_labels, y=y_labels,
        text=text_vals, texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        colorscale=[[0.0,"#1A6FA8"],[0.35,"#ECF0F1"],[0.65,"#F39C12"],[1.0,"#C0392B"]],
        colorbar=dict(title="Brecha<br>salarial (%)", ticksuffix="%", thickness=14),
        zmid=0,
    ))
    fig.update_layout(
        title=f"Mapa de Calor: Brecha Salarial (%) por País y Sector Económico — Top {top_n}",
        xaxis=dict(title="País"), yaxis=dict(autorange="reversed"),
        height=max(380, 30 * len(y_labels) + 120), **layout_base(),
    )
    return fig


def grafico_waffle_participacion(df_filtrado):
    paises = sorted(df_filtrado["PAIS"].unique())
    if not paises:
        return go.Figure()
    
    fig = make_subplots(rows=1, cols=len(paises), subplot_titles=paises, horizontal_spacing=0.06)
    
    for col_idx, pais in enumerate(paises, start=1):
        g = df_filtrado[df_filtrado["PAIS"] == pais]
        total = g["FACTOR_EXPANSION_ANUAL"].sum()
        if total == 0:
            continue
        
        pct_m = g[g["SEXO"] == "Mujer"]["FACTOR_EXPANSION_ANUAL"].sum() / total
        pct_h = 1 - pct_m
        n_mujer = round(pct_m * 100)
        xs, ys, colores = [], [], []
        count = 0
        
        for row in range(10):
            for c in range(10):
                xs.append(c)
                ys.append(row)
                colores.append(COLOR_MUJER if count < n_mujer else COLOR_HOMBRE)
                count += 1
        
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(symbol="square", size=22, color=colores, line=dict(color="white", width=2)),
            showlegend=(col_idx == 1), legendgroup="waffle", name="",
        ), row=1, col=col_idx)
        
        fig.add_annotation(
            text=f"<b>♀ {pct_m*100:.1f}%</b>", x=4.5, y=-1.5,
            xref=f"x{col_idx}", yref=f"y{col_idx}", showarrow=False,
            font=dict(size=12, color=COLOR_MUJER),
        )
        fig.add_annotation(
            text=f"<b>♂ {pct_h*100:.1f}%</b>", x=4.5, y=-2.5,
            xref=f"x{col_idx}", yref=f"y{col_idx}", showarrow=False,
            font=dict(size=12, color=COLOR_HOMBRE),
        )
    
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x")
    fig.update_layout(
        title="Waffle Chart: Composición de la Fuerza Laboral por Sexo y País",
        height=420, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50"),
        margin=dict(l=20, r=20, t=90, b=60),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# APP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ Brecha de Género en el Mercado Laboral</h1>
        <p>Bolivia · Ecuador · Perú &nbsp;|&nbsp; Análisis de indicadores de desigualdad de género en ingresos y educación</p>
    </div>""", unsafe_allow_html=True)

    df = cargar_datos()

    with st.sidebar:
        st.markdown("## 🔍 Filtros")
        st.markdown("---")
        
        paises_disp = sorted(df["PAIS"].unique())
        paises_sel  = st.multiselect("🌎 País", paises_disp, default=paises_disp)
        
        sexos_disp  = sorted(df["SEXO"].unique())
        sexos_sel   = st.multiselect("👥 Sexo", sexos_disp, default=sexos_disp)
        
        areas_disp = []
        if "AREA" in df.columns:
            areas_disp = [a for a in ["Urbano", "Rural"] if a in df["AREA"].unique()]
        areas_sel   = st.multiselect("🏙️ Área", areas_disp, default=areas_disp)
        
        if "ACTIVIDAD_ECONOMICA" in df.columns:
            acts_disp = sorted([a for a in df["ACTIVIDAD_ECONOMICA"].unique()
                               if a not in ("No Especificado", "nan", "Nan", "None")])
        else:
            acts_disp = []
        acts_sel    = st.multiselect("🏭 Actividad económica", acts_disp, default=acts_disp[:5] if acts_disp else [])
        
        st.markdown("---")
        st.markdown("### 📌 Notas metodológicas")
        st.markdown("""
        - Ingresos convertidos a **USD** (tipos de cambio 2023–2024)
        - Promedios **ponderados** por Factor de Expansión Anual
        - Outliers eliminados (top 0.5%)
        - Brecha = (H − M) / H × 100
        - Datos cargados desde **Google Drive**
        """)

    # Aplicar filtros
    df_f = df[df["PAIS"].isin(paises_sel) & df["SEXO"].isin(sexos_sel)]
    
    if areas_sel:
        df_f = df_f[df_f["AREA"].isin(areas_sel)]
    
    if acts_sel:
        df_f = df_f[df_f["ACTIVIDAD_ECONOMICA"].isin(acts_sel)]

    if df_f.empty:
        st.warning("⚠️ No hay datos para los filtros seleccionados.")
        st.stop()

    # KPIs
    st.markdown('<div class="section-title">📊 Indicadores Clave (KPIs)</div>', unsafe_allow_html=True)
    
    ih_global = ingreso_ponderado(df_f[df_f["SEXO"] == "Hombre"])
    im_global = ingreso_ponderado(df_f[df_f["SEXO"] == "Mujer"])
    eh_global = estudio_ponderado(df_f[df_f["SEXO"] == "Hombre"])
    em_global = estudio_ponderado(df_f[df_f["SEXO"] == "Mujer"])
    brecha_g  = brecha_salarial(ih_global, im_global)
    
    part_m = (df_f[df_f["SEXO"] == "Mujer"]["FACTOR_EXPANSION_ANUAL"].sum() /
              df_f["FACTOR_EXPANSION_ANUAL"].sum() * 100) if not df_f.empty else 0
    part_h = 100 - part_m

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        st.markdown(tarjeta_kpi("Ingreso Promedio — Hombres",
            f"${ih_global:,.0f}" if not np.isnan(ih_global) else "N/D", "USD / mes", "blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(tarjeta_kpi("Ingreso Promedio — Mujeres",
            f"${im_global:,.0f}" if not np.isnan(im_global) else "N/D", "USD / mes", "red"), unsafe_allow_html=True)
    with c3:
        st.markdown(tarjeta_kpi("Brecha Salarial de Género",
            f"{brecha_g:+.1f}%" if not np.isnan(brecha_g) else "N/D",
            "Hombres vs Mujeres", "gold" if brecha_g > 10 else "green"), unsafe_allow_html=True)
    with c4:
        st.markdown(tarjeta_kpi("Años de Estudio — Hombres",
            f"{eh_global:.1f}" if not np.isnan(eh_global) else "N/D", "promedio ponderado"), unsafe_allow_html=True)
    with c5:
        st.markdown(tarjeta_kpi("Años de Estudio — Mujeres",
            f"{em_global:.1f}" if not np.isnan(em_global) else "N/D", "promedio ponderado", "red"), unsafe_allow_html=True)
    with c6:
        st.markdown(tarjeta_kpi("Participación Laboral",
            f"H {part_h:.1f}% · M {part_m:.1f}%", "del total de trabajadores"), unsafe_allow_html=True)

    if not np.isnan(brecha_g):
        if brecha_g > 20:
            st.markdown(f'<div class="insight-box warning">⚠️ <b>Alta brecha salarial:</b> '
                        f'Los hombres ganan en promedio un <b>{brecha_g:.1f}%</b> más que las mujeres.</div>',
                        unsafe_allow_html=True)
        elif brecha_g > 0:
            st.markdown(f'<div class="insight-box">📌 <b>Brecha salarial moderada:</b> '
                        f'Los hombres ganan un <b>{brecha_g:.1f}%</b> más que las mujeres en promedio.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="insight-box success">✅ <b>Sin brecha adversa para mujeres:</b> '
                        f'En la selección actual, las mujeres tienen un ingreso igual o superior.</div>',
                        unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos principales
    st.markdown('<div class="section-title">💰 Ingresos por País y Sexo</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: 
        fig1 = grafico_barras_ingresos(df_f)
        if fig1.data: st.plotly_chart(fig1, use_container_width=True)
    with col2: 
        fig2 = grafico_brecha_paises(df_f)
        if fig2.data: st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-title">📈 Distribución del Ingreso y Educación</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3: 
        fig3 = boxplot_ingresos(df_f)
        if fig3.data: st.plotly_chart(fig3, use_container_width=True)
    with col4: 
        fig4 = grafico_educacion(df_f)
        if fig4.data: st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">🏙️ Área Geográfica y Participación Laboral</div>', unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5: 
        fig5 = grafico_area_urbano_rural(df_f)
        if fig5.data: st.plotly_chart(fig5, use_container_width=True)
    with col6: 
        fig6 = grafico_participacion(df_f)
        if fig6.data: st.plotly_chart(fig6, use_container_width=True)

    st.markdown('<div class="section-title">🏭 Análisis por Actividad Económica</div>', unsafe_allow_html=True)
    fig7 = grafico_ingreso_sector(df_f)
    if fig7.data: st.plotly_chart(fig7, use_container_width=True)
    
    fig8 = grafico_brecha_por_sector(df_f)
    if fig8.data: st.plotly_chart(fig8, use_container_width=True)

    st.markdown('<div class="section-title">🫧 Mapa de Brechas por Sector Económico</div>', unsafe_allow_html=True)
    fig9 = grafico_burbuja_sectores(df_f)
    if fig9.data: st.plotly_chart(fig9, use_container_width=True)

    st.markdown('<div class="section-title">🎻 Distribución Real del Ingreso — Gráfico de Violín</div>', unsafe_allow_html=True)
    fig10 = grafico_violin_ingresos(df_f)
    if fig10.data: st.plotly_chart(fig10, use_container_width=True)

    st.markdown('<div class="section-title">🌡️ Mapa de Calor — Brecha Salarial por País y Sector</div>', unsafe_allow_html=True)
    fig11 = grafico_heatmap_brecha(df_f)
    if fig11.data: st.plotly_chart(fig11, use_container_width=True)

    st.markdown('<div class="section-title">🧇 Waffle Chart — Composición de la Fuerza Laboral</div>', unsafe_allow_html=True)
    fig12 = grafico_waffle_participacion(df_f)
    if fig12.data: st.plotly_chart(fig12, use_container_width=True)

    st.markdown('<div class="section-title">🕸️ Comparación Multi-Indicador entre Países</div>', unsafe_allow_html=True)
    fig13 = grafico_radar_paises(df_f)
    if fig13.data: st.plotly_chart(fig13, use_container_width=True)

    st.markdown('<div class="section-title">📋 Tabla Resumen por País y Sexo</div>', unsafe_allow_html=True)
    resumen_rows = []
    for pais in sorted(df_f["PAIS"].unique()):
        for sexo in ["Hombre", "Mujer"]:
            g = df_f[(df_f["PAIS"] == pais) & (df_f["SEXO"] == sexo)]
            if g.empty: 
                continue
            resumen_rows.append({
                "País": pais, "Sexo": sexo,
                "Ingreso promedio (USD)": f"${ingreso_ponderado(g):,.2f}" if not np.isnan(ingreso_ponderado(g)) else "N/D",
                "Años de estudio": f"{estudio_ponderado(g):.2f}" if not np.isnan(estudio_ponderado(g)) else "N/D",
                "Participación (%)": f"{g['FACTOR_EXPANSION_ANUAL'].sum() / df_f['FACTOR_EXPANSION_ANUAL'].sum() * 100:.1f}%",
                "N observaciones": f"{len(g):,}",
            })
    
    if resumen_rows:
        st.dataframe(pd.DataFrame(resumen_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown(
        "<center style='color:#95A5A6; font-size:0.82rem;'>"
        "Dashboard de Análisis de Brecha de Género · Bolivia, Ecuador y Perú · "
        "Datos cargados desde Google Drive · Ingresos en USD"
        "</center>", unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
