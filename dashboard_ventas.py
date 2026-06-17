import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import io

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE PÁGINA
#  CRÍTICO: set_page_config SIEMPRE como primera instrucción de Streamlit.
#  sidebar_state="collapsed" porque los filtros están en el área principal.
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Ejecutivo de Ventas 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  PALETA DE COLORES — ALTO CONTRASTE
#  Fondo blanco/gris muy claro, textos oscuros,
#  acento azul marino para elementos interactivos.
# ─────────────────────────────────────────────
COLORS = {
    "bg":         "#F4F6F9",
    "card":       "#FFFFFF",
    "border":     "#D9DEE6",
    "text_dark":  "#0D1B2A",   # casi negro — legible sobre cualquier fondo claro
    "text_mid":   "#3A4A5C",
    "text_light": "#6B7C93",
    "accent":     "#1B2A4A",   # azul marino oscuro para sidebar
    "sidebar_txt":"#E8EDF5",
    "sidebar_sub":"#9AAEC8",
    "gray1":      "#EDF0F4",
    "gray2":      "#BFC9D6",
    "gray3":      "#7A8FA6",
    "gray4":      "#3A5068",
    "gray5":      "#1B2A4A",
    "pos":        "#0D6E3B",   # verde oscuro — legible
    "neg":        "#B91C1C",   # rojo oscuro — legible
    "warn":       "#92620A",   # ámbar oscuro — legible
    "highlight":  "#1B3A6B",
}

GRAY_SCALE = [
    "#1B2A4A", "#2E4068", "#3A5580", "#4A6D9A", "#6188B3",
    "#7EA3C8", "#9CBCDB", "#BAD3EA", "#D6E7F5", "#EDF4FC"
]

MES_ORDER = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
    "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

CITY_COORDS = {
    "MANAGUA":       (12.1364, -86.2514), "LEON":          (12.4379, -86.8780),
    "GRANADA":       (11.9299, -85.9560), "MASAYA":         (11.9741, -86.0942),
    "MATAGALPA":     (12.9256, -85.9164), "CHINANDEGA":     (12.6296, -87.1265),
    "ESTELI":        (13.0937, -86.3537), "RIVAS":          (11.4384, -85.8413),
    "JINOTEGA":      (13.0921, -86.0004), "NUEVA SEGOVIA":  (13.7587, -86.2398),
    "CARAZO":        (11.8460, -86.1825), "BOACO":          (12.4715, -85.6671),
    "CHONTALES":     (12.0727, -85.2307), "RIO SAN JUAN":   (11.0438, -84.7119),
    "RAAS":          (12.0070, -83.7650), "RACCN":          (14.0100, -83.3800),
    "BLUEFIELDS":    (12.0140, -83.7700), "OCOTAL":         (13.6306, -86.4733),
    "JUIGALPA":      (12.1022, -85.3724), "TIPITAPA":       (12.1950, -86.0969),
}

# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────
def hex_to_rgba(hex_color, alpha=0.15):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def fmt_usd(v):
    if pd.isna(v): return "$0"
    v = float(v)
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.2f}M"
    elif abs(v) >= 1_000:   return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

def fmt_pct(v):
    if pd.isna(v): return "0.0%"
    return f"{float(v)*100:.1f}%"

def cumpl_color(pct):
    if pct >= 90:  return COLORS["pos"]
    elif pct >= 60: return COLORS["warn"]
    return COLORS["neg"]

def kpi_card(label, value, delta_text="", delta_pos=True, sub=""):
    delta_cls = "kpi-delta-pos" if delta_pos else "kpi-delta-neg"
    delta_icon = "▲" if delta_pos else "▼"
    delta_html = f'<div class="{delta_cls}">{delta_icon} {delta_text}</div>' if delta_text else ""
    sub_html   = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
      {sub_html}
    </div>"""

def cumpl_card(label, venta, meta, pct):
    color  = cumpl_color(pct)
    bar_w  = min(pct, 100)
    signo  = "+" if pct >= 100 else ""
    return f"""
    <div class="cumpl-card">
      <div class="cumpl-label">{label}</div>
      <div class="cumpl-values">
        <span>Real: <b>{fmt_usd(venta)}</b></span>
        <span style="color:{COLORS['text_light']}">Meta: {fmt_usd(meta)}</span>
      </div>
      <div class="cumpl-bar-bg">
        <div class="cumpl-bar-fill" style="width:{bar_w}%;background:{color};"></div>
      </div>
      <div class="cumpl-pct" style="color:{color};">{signo}{pct:.1f}%</div>
    </div>"""

def chart_layout(fig, title="", height=380):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=COLORS["text_dark"], family="Inter"), x=0, xanchor="left"),
        plot_bgcolor=COLORS["card"],
        paper_bgcolor=COLORS["card"],
        font=dict(family="Inter", color=COLORS["text_mid"], size=11),
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=10)),
        xaxis=dict(gridcolor=COLORS["gray1"], linecolor=COLORS["border"], tickfont=dict(size=10)),
        yaxis=dict(gridcolor=COLORS["gray1"], linecolor=COLORS["border"], tickfont=dict(size=10)),
    )
    return fig

# ─────────────────────────────────────────────
#  ESTILOS CSS — ALTO CONTRASTE, TEXTO LEGIBLE
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {COLORS['bg']};
    color: {COLORS['text_dark']};
  }}
  .stApp {{ background-color: {COLORS['bg']}; }}

  /* Sidebar eliminado — filtros en área principal */

  /* ── KPI Cards ── */
  .kpi-card {{
    background: {COLORS['card']};
    border-radius: 10px;
    padding: 16px 18px;
    border: 1px solid {COLORS['border']};
    height: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .kpi-label {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {COLORS['text_light']};
    font-weight: 600;
  }}
  .kpi-value {{
    font-size: 1.55rem;
    font-weight: 700;
    color: {COLORS['text_dark']};
    margin-top: 5px;
    line-height: 1.2;
  }}
  .kpi-delta-pos {{ color: {COLORS['pos']}; font-size: 0.82rem; font-weight: 500; margin-top: 4px; }}
  .kpi-delta-neg {{ color: {COLORS['neg']}; font-size: 0.82rem; font-weight: 500; margin-top: 4px; }}
  .kpi-sub {{ font-size: 0.76rem; color: {COLORS['text_mid']}; margin-top: 6px; }}

  /* ── Cumplimiento Cards ── */
  .cumpl-card {{
    background: {COLORS['card']};
    border-radius: 10px;
    padding: 14px 16px;
    border: 1px solid {COLORS['border']};
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .cumpl-label  {{ font-size: 0.80rem; font-weight: 700; color: {COLORS['text_dark']}; margin-bottom: 7px; }}
  .cumpl-values {{
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem;
    color: {COLORS['text_mid']};
    margin-bottom: 7px;
  }}
  .cumpl-bar-bg   {{ background: {COLORS['gray1']}; border-radius: 4px; height: 9px; margin-bottom: 5px; }}
  .cumpl-bar-fill {{ height: 9px; border-radius: 4px; transition: width 0.3s; }}
  .cumpl-pct      {{ font-size: 1.05rem; font-weight: 700; text-align: right; }}

  /* ── Section Headers ── */
  .section-header {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {COLORS['text_light']};
    border-bottom: 2px solid {COLORS['border']};
    padding-bottom: 8px;
    margin-bottom: 18px;
    margin-top: 28px;
  }}

  /* ── Page title ── */
  .page-title    {{ font-size: 1.85rem; font-weight: 700; color: {COLORS['text_dark']}; letter-spacing: -0.02em; }}
  .page-subtitle {{ font-size: 0.87rem; color: {COLORS['text_mid']}; margin-top: 3px; }}

  /* ── Welcome screen (no archivo cargado) ── */
  .welcome-box {{
    background: {COLORS['card']};
    border: 2px dashed {COLORS['border']};
    border-radius: 16px;
    padding: 60px 40px;
    text-align: center;
    max-width: 600px;
    margin: 80px auto;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  }}
  .welcome-icon  {{ font-size: 3.5rem; margin-bottom: 16px; }}
  .welcome-title {{ font-size: 1.6rem; font-weight: 700; color: {COLORS['text_dark']}; margin-bottom: 10px; }}
  .welcome-body  {{ font-size: 0.95rem; color: {COLORS['text_mid']}; line-height: 1.6; }}
  .welcome-arrow {{ font-size: 1rem; color: {COLORS['accent']}; margin-top: 18px; font-weight: 600; }}

  /* ── Misc ── */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

  [data-testid="stFileUploader"] *, [data-testid="stFileUploaderDropzone"] * {{
    color: {COLORS['text_dark']} !important;
  }}

  .insight-box {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-left: 4px solid {COLORS['gray5']};
    border-radius: 8px;
    padding: 13px 18px;
    margin-bottom: 10px;
    font-size: 0.88rem;
    color: {COLORS['text_dark']};
    line-height: 1.5;
  }}

  div[data-testid="stDataFrame"] th {{
    color: {COLORS['text_dark']} !important;
    background-color: {COLORS['gray1']} !important;
    font-size: 0.80rem !important;
  }}
  div[data-testid="stDataFrame"] td {{
    color: {COLORS['text_dark']} !important;
    font-size: 0.83rem !important;
  }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
#  CARGA DE ARCHIVO — En área principal, siempre visible
#  ¡IMPORTANTE! El file_uploader está en el cuerpo principal,
#  NO en el sidebar. Esto garantiza que el usuario siempre
#  pueda ver y usar el uploader independientemente del estado
#  del sidebar en cualquier navegador o plataforma.
# ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "hidden_uploader",
    type=["xlsx", "xls"],
    label_visibility="collapsed",
    key="main_uploader",
)

if uploaded_file is None:
    # ── Pantalla de bienvenida con uploader integrado ──────────────
    st.markdown(f"""
    <div style="
        display:flex; flex-direction:column; align-items:center;
        justify-content:center; min-height:80vh; padding:20px;
    ">
      <div style="
          background:{COLORS['card']}; border:2px dashed {COLORS['border']};
          border-radius:20px; padding:50px 48px 40px; text-align:center;
          max-width:580px; width:100%;
          box-shadow:0 8px 32px rgba(0,0,0,0.07);
      ">
        <div style="font-size:3.5rem; margin-bottom:16px;">📊</div>
        <div style="font-size:1.7rem; font-weight:700; color:{COLORS['text_dark']};
             margin-bottom:12px; letter-spacing:-0.02em;">
          Dashboard Ejecutivo de Ventas
        </div>
        <div style="font-size:0.97rem; color:{COLORS['text_mid']}; line-height:1.7;
             margin-bottom:32px;">
          Sube tu archivo <strong>Excel de ventas</strong> para comenzar.<br>
          Debe contener una hoja <code style="background:{COLORS['gray1']};
          padding:2px 6px; border-radius:4px;">BD</code> con registros de venta
          y opcionalmente una hoja <code style="background:{COLORS['gray1']};
          padding:2px 6px; border-radius:4px;">META</code> con metas por ejecutivo.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
#  CARGA Y LIMPIEZA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data
def load_data(file_bytes):
    try:
        file_buffer = io.BytesIO(file_bytes)
        xls = pd.read_excel(file_buffer, sheet_name=None)
    except Exception as e:
        return None, pd.DataFrame(), None, f"No se pudo leer el archivo Excel: {e}"

    try:
        # ── Hoja BD ──────────────────────────────────────────────────────────
        sheet_ventas = next(
            (s for s in xls.keys() if "BD" in s.upper()),
            next((s for s in xls.keys() if "VENTA" in s.upper()), list(xls.keys())[0])
        )
        df = xls[sheet_ventas].copy()
        df.columns = df.columns.astype(str).str.strip().str.upper()

        # Homologar columna EJECUTIVO (varios typos posibles)
        col_ejec_bd = next((c for c in df.columns if "EJECUT" in c), None)
        if col_ejec_bd and col_ejec_bd != "EJECUTVO":
            df.rename(columns={col_ejec_bd: "EJECUTVO"}, inplace=True)

        # Limpiar strings
        str_cols = ["TIPO DE VENTA", "ZONA", "CIUDAD", "SEGMENTO", "MARCA",
                    "TIPO DE PRODUCTO", "EJECUTVO", "MES"]
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype(object).fillna("SIN DATO").astype(str).str.strip().str.upper()
        for col in ["TIPO DE PRODUCTO", "CIUDAD", "MARCA"]:
            if col in df.columns:
                df[col] = df[col].str.replace(r"\s+", " ", regex=True).str.strip()

        # Ordenar por mes
        if "MES" in df.columns:
            df["MES_NUM"] = df["MES"].map(MES_ORDER).fillna(99).astype(int)
            df = df.sort_values("MES_NUM")

        # Columnas derivadas
        if "TOTAL VENTA" in df.columns and "UTILIDAD TOTAL $" in df.columns:
            df["MARGEN_%"] = np.where(df["TOTAL VENTA"] > 0,
                                      df["UTILIDAD TOTAL $"] / df["TOTAL VENTA"], 0)
        else:
            df["MARGEN_%"] = 0

        df["COSTO_TOTAL"]     = df["COSTO BODEGA TOTAL"].fillna(0) if "COSTO BODEGA TOTAL" in df.columns else 0
        df["TIENE_DESCUENTO"] = df["TOTAL DESCUENTO"] > 0 if "TOTAL DESCUENTO" in df.columns else False

        col_fact = next((c for c in df.columns if "FACTUR" in c and "INGRESO" not in c), None)
        df["FACTURA_KEY"] = (df[col_fact].fillna(pd.Series(df.index.astype(str), index=df.index))
                             if col_fact else df.index.astype(str))

        # ── Hoja META ────────────────────────────────────────────────────────
        sheet_metas = None
        for s in xls.keys():
            if "META" in s.upper():
                candidate = xls[s].copy()
                candidate.columns = candidate.columns.astype(str).str.strip().str.upper()
                if not candidate.empty and any("META" in c for c in candidate.columns):
                    sheet_metas = s
                    break

        df_metas = pd.DataFrame()
        raw_meta_out = pd.DataFrame()
        if sheet_metas:
            raw = xls[sheet_metas].copy()
            raw.columns = raw.columns.astype(str).str.strip().str.upper()

            # Homologar EJECUTIVO → EJECUTVO
            col_ejec_m = next((c for c in raw.columns if "EJECUT" in c), None)
            if col_ejec_m:
                raw.rename(columns={col_ejec_m: "EJECUTVO"}, inplace=True)

            # Detectar columna META
            col_meta_val = next(
                (c for c in raw.columns if "META" in c and c not in ["MARCA", "EJECUTVO", "SEGMENTO"]),
                None
            )
            if col_meta_val:
                raw.rename(columns={col_meta_val: "META_TOTAL"}, inplace=True)

            # Limpiar strings en metas
            for col in ["SEGMENTO", "MARCA", "EJECUTVO", "MES"]:
                if col in raw.columns:
                    raw[col] = raw[col].astype(object).fillna("SIN DATO").astype(str).str.strip().str.upper()

            if "META_TOTAL" in raw.columns:
                # Meta anual por ejecutivo (suma todas marcas/segmentos)
                meta_ejec = (raw.dropna(subset=["META_TOTAL"])
                               .groupby("EJECUTVO", as_index=False)["META_TOTAL"]
                               .sum()
                               .rename(columns={"META_TOTAL": "META_ANUAL"}))
                meta_ejec["META_MENSUAL"] = meta_ejec["META_ANUAL"] / 12
                df_metas = meta_ejec.copy()

                # También guardar metas por segmento y marca si existen
                if "SEGMENTO" in raw.columns:
                    raw._meta_por_segmento = (raw.dropna(subset=["META_TOTAL"])
                                               .groupby("SEGMENTO", as_index=False)["META_TOTAL"]
                                               .sum()
                                               .rename(columns={"META_TOTAL": "META_ANUAL_SEG"}))
                if "MARCA" in raw.columns:
                    raw._meta_por_marca = (raw.dropna(subset=["META_TOTAL"])
                                            .groupby("MARCA", as_index=False)["META_TOTAL"]
                                            .sum()
                                            .rename(columns={"META_TOTAL": "META_ANUAL_MCA"}))

                # raw_meta se retorna como 4to valor para evitar pérdida por caché
                raw_meta_out = raw

        return df, df_metas, sheet_metas, raw_meta_out, None

    except Exception as e:
        return None, pd.DataFrame(), None, pd.DataFrame(), f"Error al procesar los datos: {e}"


# ── Cargar datos con manejo de error ─────────────────────────────────────────
result = load_data(uploaded_file.getvalue())
df, df_metas, sheet_metas_nombre, raw_meta, load_error = result

if load_error or df is None:
    st.error(f"⚠️ {load_error or 'Error desconocido al cargar el archivo.'}")
    st.info("Revisa que tu Excel contenga una hoja con registros de ventas y el formato correcto.")
    st.stop()

# Verificar columnas críticas
REQUIRED_COLS = {"TOTAL VENTA", "MES", "EJECUTVO", "ZONA", "SEGMENTO", "MARCA"}
missing_cols = REQUIRED_COLS - set(df.columns)
if missing_cols:
    st.warning(f"⚠️ Faltan las siguientes columnas esperadas: **{', '.join(sorted(missing_cols))}**. "
               "Algunas secciones del dashboard pueden no funcionar correctamente.")

# ─────────────────────────────────────────────
#  FILTROS — En área principal, siempre visibles
#  Barra horizontal compacta + expander para más.
# ─────────────────────────────────────────────
meses_disp = (sorted(df["MES"].unique(), key=lambda x: MES_ORDER.get(x, 99))
              if "MES" in df.columns else [])

with st.expander("🔽  Filtros — haz clic para filtrar los datos", expanded=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_mes  = st.multiselect("Mes",      meses_disp,                             default=meses_disp,                             key="f_mes")
        sel_zona = st.multiselect("Zona",     sorted(df["ZONA"].unique()),             default=sorted(df["ZONA"].unique()),             key="f_zona") if "ZONA" in df.columns else []
    with fc2:
        sel_seg   = st.multiselect("Segmento",     sorted(df["SEGMENTO"].unique()),           default=sorted(df["SEGMENTO"].unique()),           key="f_seg")   if "SEGMENTO"         in df.columns else []
        sel_marca = st.multiselect("Marca",         sorted(df["MARCA"].unique()),              default=sorted(df["MARCA"].unique()),              key="f_marca") if "MARCA"            in df.columns else []
    with fc3:
        sel_prod  = st.multiselect("Tipo Producto", sorted(df["TIPO DE PRODUCTO"].unique()),   default=sorted(df["TIPO DE PRODUCTO"].unique()),   key="f_prod")  if "TIPO DE PRODUCTO" in df.columns else []
        sel_ejec  = st.multiselect("Ejecutivo",     sorted(df["EJECUTVO"].unique()),           default=sorted(df["EJECUTVO"].unique()),           key="f_ejec")  if "EJECUTVO"         in df.columns else []

# ─────────────────────────────────────────────
#  FILTRAR DATOS
# ─────────────────────────────────────────────
mask = pd.Series(True, index=df.index)
if sel_mes:   mask &= df["MES"].isin(sel_mes)
if sel_zona:  mask &= df["ZONA"].isin(sel_zona)
if sel_seg:   mask &= df["SEGMENTO"].isin(sel_seg)
if sel_marca: mask &= df["MARCA"].isin(sel_marca)
if sel_prod and "TIPO DE PRODUCTO" in df.columns: mask &= df["TIPO DE PRODUCTO"].isin(sel_prod)
if sel_ejec:  mask &= df["EJECUTVO"].isin(sel_ejec)
dff = df[mask].copy()

dff_metas = pd.DataFrame()
if not df_metas.empty:
    mask_m = pd.Series(True, index=df_metas.index)
    if sel_ejec:
        mask_m &= df_metas["EJECUTVO"].isin(sel_ejec)
    dff_metas = df_metas[mask_m].copy()

# ─────────────────────────────────────────────
#  KPIs PRINCIPALES
# ─────────────────────────────────────────────
def safe_sum(frame, col):
    return frame[col].sum() if col in frame.columns else 0

def safe_nunique(frame, col):
    return frame[col].nunique() if col in frame.columns else 0

total_venta     = safe_sum(dff, "TOTAL VENTA")
total_utilidad  = safe_sum(dff, "UTILIDAD TOTAL $")
total_descuento = safe_sum(dff, "TOTAL DESCUENTO")
total_costo     = safe_sum(dff, "COSTO_TOTAL")
total_pares     = safe_sum(dff, "PARES")
total_transacc  = safe_nunique(dff, "FACTURA_KEY")
margen_global   = total_utilidad / total_venta if total_venta > 0 else 0
ticket_prom     = total_venta / total_transacc if total_transacc > 0 else 0
subtotal_sum    = safe_sum(dff, "SUBTOTAL")
descuento_rate  = total_descuento / subtotal_sum if subtotal_sum > 0 else 0
efect_desc      = dff["TIENE_DESCUENTO"].mean() if "TIENE_DESCUENTO" in dff.columns else 0

n_meses_sel      = len(sel_mes) if sel_mes else 12
total_meta_anual = dff_metas["META_ANUAL"].sum() if not dff_metas.empty and "META_ANUAL" in dff_metas.columns else 0
meta_prorrata    = total_meta_anual * n_meses_sel / 12
cumplimiento_pct = total_venta / meta_prorrata * 100 if meta_prorrata > 0 else 0

best_mes = "—"
if "MES" in dff.columns and "UTILIDAD TOTAL $" in dff.columns and not dff.empty:
    mes_util = dff.groupby("MES")["UTILIDAD TOTAL $"].sum()
    if not mes_util.empty:
        best_mes = mes_util.idxmax()

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
col_title, col_info = st.columns([3, 1])
with col_title:
    meses_str = " – ".join([m.capitalize() for m in (sel_mes if sel_mes else meses_disp)]) or "Todos los meses"
    st.markdown(f"""
    <div class="page-title">Dashboard Ejecutivo de Ventas</div>
    <div class="page-subtitle">{meses_str} 2026 &nbsp;·&nbsp; Actualización mensual automática</div>
    """, unsafe_allow_html=True)
with col_info:
    st.markdown(f"""
    <div style='text-align:right; padding-top:8px'>
      <div style='font-size:0.72rem;color:{COLORS["text_light"]};letter-spacing:0.06em;'>REGISTROS ACTIVOS</div>
      <div style='font-size:1.45rem;font-weight:700;color:{COLORS["text_dark"]};'>{len(dff):,}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SECCIÓN: RENDIMIENTO GLOBAL VS METAS
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>RENDIMIENTO GLOBAL VS METAS</div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    if meta_prorrata > 0:
        desviacion = cumplimiento_pct - 100
        signo = "+" if desviacion >= 0 else ""
        delta_str = f"{signo}{desviacion:.1f}% vs Meta ({cumplimiento_pct:.1f}% lograda)"
        delta_ok  = desviacion >= 0
    else:
        delta_str = "Sin meta asignada"
        delta_ok  = True
    st.metric("Venta Real (período)", fmt_usd(total_venta), delta=delta_str)
with col2:
    if meta_prorrata > 0:
        falta    = meta_prorrata - total_venta
        sub_meta = f"Falta {fmt_usd(max(falta,0))} para meta" if falta > 0 else "✅ Meta superada"
        st.metric("Meta Período (prorrata)", fmt_usd(meta_prorrata), delta=sub_meta)
    else:
        st.metric("Meta Anual Total", "N/A" if total_meta_anual == 0 else fmt_usd(total_meta_anual))
with col3:
    st.metric("Margen Global", f"{margen_global*100:.1f}%", delta=f"Mejor mes: {best_mes.title()}")
with col4:
    st.metric("Utilidad Bruta", fmt_usd(total_utilidad))

# ─────────────────────────────────────────────
#  SECCIÓN: KPIs OPERATIVOS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">INDICADORES CLAVE DE RENDIMIENTO</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(kpi_card("Venta Total", fmt_usd(total_venta), sub=f"{total_transacc:,} facturas"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("Utilidad Bruta", fmt_usd(total_utilidad), sub=f"Margen: {fmt_pct(margen_global)}"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("Margen %", fmt_pct(margen_global),
                delta_text=f"Mejor mes: {best_mes.title()}", delta_pos=(margen_global > 0.25),
                sub="Meta sugerida > 25%"), unsafe_allow_html=True)
with c4:
    st.markdown(kpi_card("Ticket Promedio", fmt_usd(ticket_prom), sub=f"{total_pares:,.0f} unidades vendidas"), unsafe_allow_html=True)
with c5:
    st.markdown(kpi_card("Total Descuentos", fmt_usd(total_descuento),
                delta_text=fmt_pct(descuento_rate) + " sobre subtotal", delta_pos=False,
                sub=f"{efect_desc*100:.1f}% transacc. con dcto."), unsafe_allow_html=True)
with c6:
    costo_venta_pct = total_costo / total_venta if total_venta > 0 else 0
    st.markdown(kpi_card("Costo Total", fmt_usd(total_costo), sub=f"Costo/Venta: {fmt_pct(costo_venta_pct)}"), unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS PRINCIPALES — inmediatamente tras KPIs
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "  📈 Tendencias  ", "  💰 Rentabilidad  ", "  🗺️ Mapa  ",
    "  👤 Ejecutivos  ", "  🏷️ Marcas  ", "  📊 Variaciones  "
])

# ═══════════════════════════════════════════════════════════
#  SECCIÓN: CUMPLIMIENTO JERÁRQUICO  (fuera de tabs, debajo)
#  Orden: 1. Por Ejecutivo → 2. Por Segmento → 3. Por Marca
# ═══════════════════════════════════════════════════════════
st.markdown("<div class='section-header'>CUMPLIMIENTO VS META — ANÁLISIS JERÁRQUICO</div>", unsafe_allow_html=True)

has_metas = not dff_metas.empty and "META_ANUAL" in dff_metas.columns

if has_metas:

    # ── 1. POR EJECUTIVO ────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-size:0.90rem; font-weight:700; color:{COLORS["text_dark"]};
         margin-bottom:12px; margin-top:6px;
         display:flex; align-items:center; gap:10px;'>
      <span style='background:{COLORS["accent"]};color:#FFF;
             border-radius:50%; width:26px;height:26px;
             display:inline-flex;align-items:center;justify-content:center;
             font-size:0.78rem;font-weight:700;'>1</span>
      Cumplimiento por Ejecutivo
    </div>
    """, unsafe_allow_html=True)

    try:
        ventas_ejec = dff.groupby("EJECUTVO")["TOTAL VENTA"].sum().reset_index()
        ventas_ejec.columns = ["EJECUTVO", "VENTA_REAL"]
        df_comp = pd.merge(ventas_ejec, dff_metas[["EJECUTVO", "META_ANUAL", "META_MENSUAL"]],
                           on="EJECUTVO", how="outer").fillna(0)
        df_comp["META_PERIODO"] = df_comp["META_ANUAL"] * n_meses_sel / 12
        df_comp["CUMPL_%"]      = np.where(df_comp["META_PERIODO"] > 0,
                                           df_comp["VENTA_REAL"] / df_comp["META_PERIODO"] * 100, 0)
        df_comp = df_comp.sort_values("CUMPL_%", ascending=False)
        df_comp["EJECUTIVO_L"] = df_comp["EJECUTVO"].str.title()

        for batch_start in range(0, len(df_comp), 4):
            batch = df_comp.iloc[batch_start:batch_start+4]
            cols_c = st.columns(min(len(batch), 4))
            for idx, (_, row) in enumerate(batch.iterrows()):
                with cols_c[idx]:
                    st.markdown(cumpl_card(row["EJECUTIVO_L"], row["VENTA_REAL"],
                                           row["META_PERIODO"], row["CUMPL_%"]),
                                unsafe_allow_html=True)

        # Gráfico + Gauge en 2 columnas
        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=df_comp["EJECUTIVO_L"], y=df_comp["VENTA_REAL"], name="Venta Real",
                marker_color=COLORS["gray4"],
                text=[fmt_usd(v) for v in df_comp["VENTA_REAL"]],
                textposition="outside", textfont=dict(size=9),
            ))
            fig_comp.add_trace(go.Bar(
                x=df_comp["EJECUTIVO_L"], y=df_comp["META_PERIODO"], name=f"Meta ({n_meses_sel}m)",
                marker_color=COLORS["gray2"],
                text=[fmt_usd(v) for v in df_comp["META_PERIODO"]],
                textposition="outside", textfont=dict(size=9),
            ))
            chart_layout(fig_comp, "Venta Real vs Meta por Ejecutivo", height=350)
            fig_comp.update_layout(barmode="group", xaxis_tickangle=-25, legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig_comp, use_container_width=True)

        with col_g2:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=round(cumplimiento_pct, 1),
                delta={"reference": 100, "suffix": "%", "valueformat": ".1f"},
                title={"text": "Cumplimiento Global<br><span style='font-size:0.8rem'>vs Meta Período</span>",
                       "font": {"size": 14}},
                number={"suffix": "%", "font": {"size": 32}},
                gauge={
                    "axis": {"range": [0, 150], "tickwidth": 1},
                    "bar":  {"color": COLORS["gray4"], "thickness": 0.3},
                    "bgcolor": COLORS["card"],
                    "borderwidth": 1, "bordercolor": COLORS["border"],
                    "steps": [
                        {"range": [0,   60],  "color": "#FFE5E5"},
                        {"range": [60,  90],  "color": "#FFF3CD"},
                        {"range": [90,  110], "color": "#E5FFE5"},
                        {"range": [110, 150], "color": "#D0F0D0"},
                    ],
                    "threshold": {"line": {"color": COLORS["gray5"], "width": 3},
                                  "thickness": 0.8, "value": 100},
                }
            ))
            fig_gauge.update_layout(paper_bgcolor=COLORS["card"], height=350,
                                    margin=dict(l=20, r=20, t=60, b=20),
                                    font=dict(family="Inter", color=COLORS["text_mid"]))
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Tabla resumen
        st.markdown("<div class='section-header'>TABLA RESUMEN — EJECUTIVOS</div>", unsafe_allow_html=True)
        tbl_comp = df_comp[["EJECUTIVO_L", "VENTA_REAL", "META_PERIODO", "META_ANUAL", "CUMPL_%"]].copy()
        tbl_comp["Δ vs Meta"] = (tbl_comp["VENTA_REAL"] - tbl_comp["META_PERIODO"]).apply(
            lambda v: f"+{fmt_usd(v)}" if v >= 0 else f"-{fmt_usd(abs(v))}")
        tbl_comp["VENTA_REAL"]   = tbl_comp["VENTA_REAL"].apply(fmt_usd)
        tbl_comp["META_PERIODO"] = tbl_comp["META_PERIODO"].apply(fmt_usd)
        tbl_comp["META_ANUAL"]   = tbl_comp["META_ANUAL"].apply(fmt_usd)
        tbl_comp["CUMPL_%"]      = tbl_comp["CUMPL_%"].apply(lambda v: f"{v:.1f}%")
        tbl_comp.columns = ["Ejecutivo", "Venta Real", f"Meta {n_meses_sel}m", "Meta Anual", "Cumpl. %", "Δ vs Meta"]
        st.dataframe(tbl_comp, use_container_width=True, hide_index=True)

    except Exception as e:
        st.warning(f"⚠️ No se pudo calcular el cumplimiento por ejecutivo: {e}")

    # ── 2. POR SEGMENTO ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-size:0.90rem; font-weight:700; color:{COLORS["text_dark"]};
         margin-bottom:12px; margin-top:24px;
         display:flex; align-items:center; gap:10px;'>
      <span style='background:{COLORS["gray4"]};color:#FFF;
             border-radius:50%; width:26px;height:26px;
             display:inline-flex;align-items:center;justify-content:center;
             font-size:0.78rem;font-weight:700;'>2</span>
      Cumplimiento por Segmento
    </div>
    """, unsafe_allow_html=True)

    try:
        if "SEGMENTO" in dff.columns:
            ventas_seg = dff.groupby("SEGMENTO")["TOTAL VENTA"].sum().reset_index()
            ventas_seg.columns = ["SEGMENTO", "VENTA_REAL"]

            # Obtener meta por segmento desde el raw_meta si existe
            # raw_meta passed directly from load_data (no longer an attribute)
            if raw_meta is not None and "SEGMENTO" in raw_meta.columns and "META_TOTAL" in raw_meta.columns:
                meta_seg_raw = (raw_meta.dropna(subset=["META_TOTAL"])
                                 .groupby("SEGMENTO", as_index=False)["META_TOTAL"]
                                 .sum()
                                 .rename(columns={"META_TOTAL": "META_ANUAL_SEG"}))
                df_seg_comp = pd.merge(ventas_seg, meta_seg_raw, on="SEGMENTO", how="left").fillna(0)
            else:
                # Sin metas por segmento: usamos la meta global distribuida proporcionalmente
                total_venta_segs = ventas_seg["VENTA_REAL"].sum()
                df_seg_comp = ventas_seg.copy()
                df_seg_comp["META_ANUAL_SEG"] = (
                    df_seg_comp["VENTA_REAL"] / total_venta_segs * total_meta_anual
                    if total_venta_segs > 0 else 0
                )

            df_seg_comp["META_PERIODO_SEG"] = df_seg_comp["META_ANUAL_SEG"] * n_meses_sel / 12
            df_seg_comp["CUMPL_%"] = np.where(
                df_seg_comp["META_PERIODO_SEG"] > 0,
                df_seg_comp["VENTA_REAL"] / df_seg_comp["META_PERIODO_SEG"] * 100, 0
            )
            df_seg_comp = df_seg_comp.sort_values("CUMPL_%", ascending=False)
            df_seg_comp["SEG_L"] = df_seg_comp["SEGMENTO"].str.title()

            cols_seg = st.columns(min(len(df_seg_comp), 4))
            for idx, (_, row) in enumerate(df_seg_comp.iterrows()):
                with cols_seg[idx % 4]:
                    st.markdown(cumpl_card(row["SEG_L"], row["VENTA_REAL"],
                                           row["META_PERIODO_SEG"], row["CUMPL_%"]),
                                unsafe_allow_html=True)

            # Gráfico barras horizontales
            fig_seg = go.Figure()
            fig_seg.add_trace(go.Bar(
                y=df_seg_comp["SEG_L"], x=df_seg_comp["VENTA_REAL"],
                name="Venta Real", orientation="h",
                marker_color=COLORS["gray4"],
                text=[fmt_usd(v) for v in df_seg_comp["VENTA_REAL"]],
                textposition="outside", textfont=dict(size=10),
            ))
            fig_seg.add_trace(go.Bar(
                y=df_seg_comp["SEG_L"], x=df_seg_comp["META_PERIODO_SEG"],
                name=f"Meta ({n_meses_sel}m)", orientation="h",
                marker_color=COLORS["gray2"],
                text=[fmt_usd(v) for v in df_seg_comp["META_PERIODO_SEG"]],
                textposition="outside", textfont=dict(size=10),
            ))
            chart_layout(fig_seg, "Venta Real vs Meta por Segmento", height=max(280, len(df_seg_comp)*70))
            fig_seg.update_layout(barmode="group", legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_seg, use_container_width=True)
        else:
            st.info("La columna SEGMENTO no está disponible en los datos.")

    except Exception as e:
        st.warning(f"⚠️ No se pudo calcular el cumplimiento por segmento: {e}")

    # ── 3. POR MARCA ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-size:0.90rem; font-weight:700; color:{COLORS["text_dark"]};
         margin-bottom:12px; margin-top:24px;
         display:flex; align-items:center; gap:10px;'>
      <span style='background:{COLORS["gray3"]};color:#FFF;
             border-radius:50%; width:26px;height:26px;
             display:inline-flex;align-items:center;justify-content:center;
             font-size:0.78rem;font-weight:700;'>3</span>
      Cumplimiento por Marca
    </div>
    """, unsafe_allow_html=True)

    try:
        if "MARCA" in dff.columns:
            ventas_mca = dff.groupby("MARCA")["TOTAL VENTA"].sum().reset_index()
            ventas_mca.columns = ["MARCA", "VENTA_REAL"]

            # raw_meta passed directly from load_data (no longer an attribute)
            if raw_meta is not None and "MARCA" in raw_meta.columns and "META_TOTAL" in raw_meta.columns:
                meta_mca_raw = (raw_meta.dropna(subset=["META_TOTAL"])
                                 .groupby("MARCA", as_index=False)["META_TOTAL"]
                                 .sum()
                                 .rename(columns={"META_TOTAL": "META_ANUAL_MCA"}))
                df_mca_comp = pd.merge(ventas_mca, meta_mca_raw, on="MARCA", how="left").fillna(0)
            else:
                total_venta_mca = ventas_mca["VENTA_REAL"].sum()
                df_mca_comp = ventas_mca.copy()
                df_mca_comp["META_ANUAL_MCA"] = (
                    df_mca_comp["VENTA_REAL"] / total_venta_mca * total_meta_anual
                    if total_venta_mca > 0 else 0
                )

            df_mca_comp["META_PERIODO_MCA"] = df_mca_comp["META_ANUAL_MCA"] * n_meses_sel / 12
            df_mca_comp["CUMPL_%"] = np.where(
                df_mca_comp["META_PERIODO_MCA"] > 0,
                df_mca_comp["VENTA_REAL"] / df_mca_comp["META_PERIODO_MCA"] * 100, 0
            )
            df_mca_comp = df_mca_comp.sort_values("CUMPL_%", ascending=False)
            df_mca_comp["MARCA_L"] = df_mca_comp["MARCA"].str.title()

            top_n_mca = st.slider("Marcas a mostrar en cumplimiento:", 5,
                                   min(30, len(df_mca_comp)), min(15, len(df_mca_comp)),
                                   key="slider_cumpl_marca")
            df_mca_top = df_mca_comp.head(top_n_mca)

            fig_mca = go.Figure()
            fig_mca.add_trace(go.Bar(
                y=df_mca_top["MARCA_L"], x=df_mca_top["VENTA_REAL"],
                name="Venta Real", orientation="h",
                marker_color=COLORS["gray4"],
                text=[fmt_usd(v) for v in df_mca_top["VENTA_REAL"]],
                textposition="outside", textfont=dict(size=9),
            ))
            fig_mca.add_trace(go.Bar(
                y=df_mca_top["MARCA_L"], x=df_mca_top["META_PERIODO_MCA"],
                name=f"Meta ({n_meses_sel}m)", orientation="h",
                marker_color=COLORS["gray2"],
                text=[fmt_usd(v) for v in df_mca_top["META_PERIODO_MCA"]],
                textposition="outside", textfont=dict(size=9),
            ))
            chart_layout(fig_mca, f"Top {top_n_mca} Marcas — Venta Real vs Meta", height=max(300, top_n_mca*55))
            fig_mca.update_layout(barmode="group", yaxis=dict(autorange="reversed"),
                                   legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_mca, use_container_width=True)

            # Tabla resumen marcas
            st.markdown("<div class='section-header'>TABLA RESUMEN — MARCAS</div>", unsafe_allow_html=True)
            tbl_mca = df_mca_top[["MARCA_L", "VENTA_REAL", "META_PERIODO_MCA", "CUMPL_%"]].copy()
            tbl_mca["Δ vs Meta"] = (df_mca_top["VENTA_REAL"] - df_mca_top["META_PERIODO_MCA"]).apply(
                lambda v: f"+{fmt_usd(v)}" if v >= 0 else f"-{fmt_usd(abs(v))}")
            tbl_mca["VENTA_REAL"]      = tbl_mca["VENTA_REAL"].apply(fmt_usd)
            tbl_mca["META_PERIODO_MCA"]= tbl_mca["META_PERIODO_MCA"].apply(fmt_usd)
            tbl_mca["CUMPL_%"]         = tbl_mca["CUMPL_%"].apply(lambda v: f"{v:.1f}%")
            tbl_mca.columns = ["Marca", "Venta Real", f"Meta {n_meses_sel}m", "Cumpl. %", "Δ vs Meta"]
            st.dataframe(tbl_mca, use_container_width=True, hide_index=True)
        else:
            st.info("La columna MARCA no está disponible en los datos.")

    except Exception as e:
        st.warning(f"⚠️ No se pudo calcular el cumplimiento por marca: {e}")

else:
    st.info("""
    ℹ️ **KPIs de Cumplimiento no disponibles.**
    Asegúrate de que tu Excel tenga una hoja llamada **META** con columnas:
    `MES | SEGMENTO | EJECUTIVO | MARCA | META 2026`
    """)


# ══════════════════════════════════════════════
#  TAB 1 — TENDENCIAS MENSUALES
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Evolución Mensual</div>', unsafe_allow_html=True)
    try:
        for col, default in {"TOTAL VENTA": 0, "UTILIDAD TOTAL $": 0, "TOTAL DESCUENTO": 0,
                              "COSTO_TOTAL": 0, "PARES": 0, "FACTURA_KEY": np.nan}.items():
            if col not in dff.columns:
                dff[col] = default

        mes_gb = dff.groupby("MES").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Descuento=("TOTAL DESCUENTO", "sum"), Costo=("COSTO_TOTAL", "sum"),
            Pares=("PARES", "sum"), Facturas=("FACTURA_KEY", "nunique"),
        ).reset_index()
        mes_gb["Margen_%"] = mes_gb["Utilidad"] / mes_gb["Venta"].replace(0, np.nan)
        mes_gb["MES_NUM"]  = mes_gb["MES"].map(MES_ORDER)
        mes_gb = mes_gb.sort_values("MES_NUM")
        mes_labels = mes_gb["MES"].str.capitalize().tolist()

        col_left, col_right = st.columns([2, 1])
        with col_left:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=mes_labels, y=mes_gb["Venta"], name="Venta Total",
                                  marker_color=COLORS["gray4"], opacity=0.85,
                                  text=[fmt_usd(v) for v in mes_gb["Venta"]],
                                  textposition="outside", textfont=dict(size=9)), secondary_y=False)
            fig.add_trace(go.Bar(x=mes_labels, y=mes_gb["Utilidad"], name="Utilidad Bruta",
                                  marker_color=COLORS["gray3"], opacity=0.85,
                                  text=[fmt_usd(v) for v in mes_gb["Utilidad"]],
                                  textposition="outside", textfont=dict(size=9)), secondary_y=False)
            fig.add_trace(go.Scatter(
                x=mes_labels, y=mes_gb["Margen_%"] * 100, name="Margen %",
                mode="lines+markers+text", line=dict(color=COLORS["gray5"], width=2.5),
                marker=dict(size=7),
                text=[f"{v:.1f}%" for v in mes_gb["Margen_%"].fillna(0) * 100],
                textposition="top center", textfont=dict(size=10),
            ), secondary_y=True)
            fig.update_yaxes(title_text="USD $", secondary_y=False, tickprefix="$", gridcolor=COLORS["gray1"])
            fig.update_yaxes(title_text="Margen %", secondary_y=True, ticksuffix="%", showgrid=False)
            chart_layout(fig, "Venta · Utilidad · Margen %", height=350)
            fig.update_layout(barmode="group", legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            fig2 = go.Figure()
            media_desc = mes_gb["Descuento"].mean()
            fig2.add_trace(go.Bar(
                x=mes_labels, y=mes_gb["Descuento"],
                marker_color=[COLORS["gray2"] if v < media_desc else COLORS["gray4"] for v in mes_gb["Descuento"]],
                text=[fmt_usd(v) for v in mes_gb["Descuento"]],
                textposition="outside", textfont=dict(size=10),
            ))
            chart_layout(fig2, "Descuentos por Mes", height=350)
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=mes_labels, y=mes_gb["Pares"], fill="tozeroy", mode="lines+markers+text",
                line=dict(color=COLORS["gray4"], width=2.5),
                fillcolor="rgba(74,74,74,0.12)", marker=dict(size=7),
                text=[f"{v:,.0f}" for v in mes_gb["Pares"]],
                textposition="top center", textfont=dict(size=9),
            ))
            chart_layout(fig3, "Volumen de Unidades Vendidas (Pares/Items)", height=300)
            st.plotly_chart(fig3, use_container_width=True)

        with col_b:
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=mes_labels, y=mes_gb["Facturas"], mode="lines+markers+text",
                line=dict(color=COLORS["gray3"], width=2.5, dash="dot"),
                marker=dict(size=7, symbol="diamond"),
                text=[f"{v:,.0f}" for v in mes_gb["Facturas"]],
                textposition="top center", textfont=dict(size=9),
            ))
            chart_layout(fig4, "Número de Facturas Emitidas por Mes", height=300)
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown('<div class="section-header">Venta por Segmento × Mes</div>', unsafe_allow_html=True)
        seg_mes = dff.groupby(["MES", "SEGMENTO"])["TOTAL VENTA"].sum().reset_index()
        seg_mes["MES_NUM"]   = seg_mes["MES"].map(MES_ORDER)
        seg_mes = seg_mes.sort_values("MES_NUM")
        seg_mes["MES_LABEL"] = seg_mes["MES"].str.capitalize()

        # Paleta corporativa distinguible — azul marino, verde, naranja, índigo, burdeos, teal
        SEG_COLORS = [
            "#1B3A6B",  # azul marino
            "#2E7D5E",  # verde corporativo
            "#C75B2A",  # naranja quemado
            "#5C6BC0",  # índigo
            "#7B3F6E",  # burdeos
            "#1B7A8A",  # teal oscuro
            "#8D6E2B",  # dorado oscuro
            "#3A6B3A",  # verde pino
        ]
        fig5 = go.Figure()
        for i, seg in enumerate(seg_mes["SEGMENTO"].unique()):
            s = seg_mes[seg_mes["SEGMENTO"] == seg]
            fig5.add_trace(go.Bar(
                x=s["MES_LABEL"], y=s["TOTAL VENTA"], name=seg.title(),
                marker_color=SEG_COLORS[i % len(SEG_COLORS)],
                marker_line=dict(color="rgba(255,255,255,0.3)", width=0.8),
                text=[fmt_usd(v) for v in s["TOTAL VENTA"]],
                textposition="inside", textfont=dict(size=9, color="#FFFFFF"),
            ))
        chart_layout(fig5, "Composición de Venta por Segmento", height=340)
        fig5.update_layout(
            barmode="stack",
            legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
        )
        st.plotly_chart(fig5, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error en Tab Tendencias: {e}")

# ══════════════════════════════════════════════
#  TAB 2 — RENTABILIDAD
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Análisis de Rentabilidad</div>', unsafe_allow_html=True)
    try:
        seg_rent = dff.groupby("SEGMENTO").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Descuento=("TOTAL DESCUENTO", "sum"), Costo=("COSTO_TOTAL", "sum"),
        ).reset_index()
        seg_rent["Margen%"] = seg_rent["Utilidad"] / seg_rent["Venta"].replace(0, np.nan) * 100
        seg_rent["Desc%"]   = seg_rent["Descuento"] / (seg_rent["Venta"]+seg_rent["Descuento"]).replace(0, np.nan) * 100

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            for i, row in seg_rent.iterrows():
                fig.add_trace(go.Bar(
                    x=[row["SEGMENTO"].title()], y=[row["Margen%"]],
                    name=row["SEGMENTO"].title(),
                    marker_color=GRAY_SCALE[i % len(GRAY_SCALE)],
                    text=[f"{row['Margen%']:.1f}%"], textposition="outside",
                ))
            chart_layout(fig, "Margen % por Segmento", height=320)
            fig.update_layout(showlegend=False, yaxis_ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig_wf = go.Figure(go.Waterfall(
                name="Desglose", orientation="v",
                x=["Venta Bruta", "(-) Descuentos", "(-) Costo Mercancía", "= Utilidad Bruta"],
                y=[total_venta, -total_descuento, -total_costo, total_utilidad],
                connector={"line": {"color": COLORS["gray2"]}},
                decreasing={"marker": {"color": COLORS["gray2"]}},
                increasing={"marker": {"color": COLORS["gray4"]}},
                totals={"marker": {"color": COLORS["gray5"]}},
                text=[fmt_usd(total_venta), fmt_usd(-total_descuento),
                      fmt_usd(-total_costo), fmt_usd(total_utilidad)],
                textposition="outside",
            ))
            chart_layout(fig_wf, "Waterfall: Venta → Utilidad Bruta", height=320)
            st.plotly_chart(fig_wf, use_container_width=True)

        zona_scatter = dff.groupby("ZONA").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Transacc=("FACTURA_KEY", "nunique"),
        ).reset_index()
        zona_scatter["Margen%"] = zona_scatter["Utilidad"] / zona_scatter["Venta"].replace(0, np.nan) * 100

        col3, col4 = st.columns(2)
        with col3:
            fig_sc = go.Figure()
            for i, row in zona_scatter.iterrows():
                fig_sc.add_trace(go.Scatter(
                    x=[row["Venta"]], y=[row["Margen%"]], mode="markers+text",
                    marker=dict(size=max(10, row["Transacc"] / 30),
                                color=GRAY_SCALE[i % len(GRAY_SCALE)],
                                line=dict(color="#000", width=1)),
                    text=[row["ZONA"].title()], textposition="top center", name=row["ZONA"].title(),
                ))
            chart_layout(fig_sc, "Zona: Venta Total vs Margen% (tamaño = transacciones)", height=360)
            fig_sc.update_layout(showlegend=False, xaxis_tickprefix="$", yaxis_ticksuffix="%")
            st.plotly_chart(fig_sc, use_container_width=True)

        with col4:
            disc_g = dff.groupby("TIENE_DESCUENTO").agg(
                Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
                Cnt=("FACTURA_KEY", "count"),
            ).reset_index()
            disc_g["Label"]   = disc_g["TIENE_DESCUENTO"].map({True: "Con Descuento", False: "Sin Descuento"})
            disc_g["Margen%"] = disc_g["Utilidad"] / disc_g["Venta"].replace(0, np.nan) * 100
            fig_d = make_subplots(rows=1, cols=2, subplot_titles=("Venta Total", "Margen %"))
            fig_d.add_trace(go.Bar(x=disc_g["Label"], y=disc_g["Venta"],
                                    marker_color=[COLORS["gray3"], COLORS["gray5"]],
                                    text=[fmt_usd(v) for v in disc_g["Venta"]], textposition="outside"),
                             row=1, col=1)
            fig_d.add_trace(go.Bar(x=disc_g["Label"], y=disc_g["Margen%"],
                                    marker_color=[COLORS["gray3"], COLORS["gray5"]],
                                    text=[f"{v:.1f}%" for v in disc_g["Margen%"]], textposition="outside"),
                             row=1, col=2)
            chart_layout(fig_d, "Efectividad de Descuentos: Con vs Sin", height=360)
            fig_d.update_layout(showlegend=False)
            st.plotly_chart(fig_d, use_container_width=True)

        st.markdown('<div class="section-header">Tabla de Rentabilidad por Zona</div>', unsafe_allow_html=True)
        zona_tbl = dff.groupby("ZONA").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Costo=("COSTO_TOTAL", "sum"), Descuento=("TOTAL DESCUENTO", "sum"),
            Facturas=("FACTURA_KEY", "nunique"),
        ).reset_index()
        zona_tbl["Margen%"] = (zona_tbl["Utilidad"] / zona_tbl["Venta"].replace(0, np.nan) * 100).round(1)
        for c in ["Venta", "Utilidad", "Costo", "Descuento"]:
            zona_tbl[c] = zona_tbl[c].apply(fmt_usd)
        zona_tbl.columns = ["Zona", "Venta Total", "Utilidad $", "Costo Total", "Descuento", "Facturas", "Margen %"]
        zona_tbl["Zona"] = zona_tbl["Zona"].str.title()
        st.dataframe(zona_tbl, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Error en Tab Rentabilidad: {e}")

# ══════════════════════════════════════════════
#  TAB 3 — MAPA GEOESPACIAL
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Mapa de Calor Geoespacial — Nicaragua</div>', unsafe_allow_html=True)
    try:
        metrica_mapa = st.radio(
            "Métrica a visualizar en el mapa:",
            ["Venta Total", "Utilidad Total", "Descuento Total", "Nº de Transacciones"],
            horizontal=True,
        )
        campo_map = {"Venta Total": "TOTAL VENTA", "Utilidad Total": "UTILIDAD TOTAL $",
                     "Descuento Total": "TOTAL DESCUENTO", "Nº de Transacciones": "FACTURA_KEY"}[metrica_mapa]

        if campo_map == "FACTURA_KEY":
            city_data = dff.groupby("CIUDAD")[campo_map].nunique().reset_index()
        else:
            city_data = dff.groupby("CIUDAD")[campo_map].sum().reset_index()
        city_data.columns = ["CIUDAD", "VALOR"]
        city_data["CIUDAD"] = city_data["CIUDAD"].str.strip().str.upper()
        city_data["lat"] = city_data["CIUDAD"].map(lambda c: CITY_COORDS.get(c, (None, None))[0])
        city_data["lon"] = city_data["CIUDAD"].map(lambda c: CITY_COORDS.get(c, (None, None))[1])
        city_data = city_data.dropna(subset=["lat", "lon"])
        city_data["Ciudad_Label"] = city_data["CIUDAD"].str.title()

        if campo_map == "FACTURA_KEY":
            city_data["Texto"] = city_data.apply(lambda r: f"{r['Ciudad_Label']}<br>Transacciones: {r['VALOR']:,}", axis=1)
        else:
            city_data["Texto"] = city_data.apply(lambda r: f"{r['Ciudad_Label']}<br>{metrica_mapa}: {fmt_usd(r['VALOR'])}", axis=1)

        if city_data.empty:
            st.warning("⚠️ No se encontraron coordenadas para las ciudades. Verifica los nombres en tu Excel.")
        else:
            fig_map = go.Figure()
            fig_map.add_trace(go.Densitymapbox(
                lat=city_data["lat"], lon=city_data["lon"], z=city_data["VALOR"],
                radius=45,
                colorscale=[[0.0, "rgba(230,230,230,0.0)"], [0.2, "rgba(180,180,180,0.3)"],
                             [0.5, "rgba(110,110,110,0.6)"], [0.8, "rgba(50,50,50,0.8)"],
                             [1.0, "rgba(10,10,10,1.0)"]],
                opacity=0.7, showscale=False,
            ))
            max_val = city_data["VALOR"].max() if city_data["VALOR"].max() > 0 else 1
            fig_map.add_trace(go.Scattermapbox(
                lat=city_data["lat"], lon=city_data["lon"], mode="markers+text",
                marker=dict(size=city_data["VALOR"] / max_val * 55 + 8,
                            color=city_data["VALOR"],
                            colorscale=[[0, "#E8E8E8"], [0.3, "#9A9A9A"], [0.7, "#4A4A4A"], [1, "#1A1A1A"]],
                            opacity=0.85, showscale=True,
                            colorbar=dict(title=dict(text=metrica_mapa, font=dict(size=11, color="#444")),
                                          tickfont=dict(size=9, color="#444"),
                                          bgcolor="rgba(255,255,255,0.9)", bordercolor="#DDD", x=1.02)),
                text=city_data["Ciudad_Label"], textfont=dict(size=9, color="#111"),
                hovertext=city_data["Texto"], hoverinfo="text",
            ))
            fig_map.update_layout(
                mapbox=dict(style="carto-positron", center=dict(lat=12.8, lon=-85.5), zoom=6.0),
                paper_bgcolor=COLORS["card"], height=580, margin=dict(l=0, r=0, t=30, b=0),
                title=dict(text=f"Nicaragua · {metrica_mapa} por Ciudad",
                           font=dict(size=13, color=COLORS["text_dark"]), x=0.01),
                showlegend=False,
            )
            st.plotly_chart(fig_map, use_container_width=True)

            st.markdown('<div class="section-header">Ranking de Ciudades</div>', unsafe_allow_html=True)
            top_city = city_data.sort_values("VALOR", ascending=False).head(15)
            fig_tc = go.Figure(go.Bar(
                x=top_city["VALOR"], y=top_city["Ciudad_Label"], orientation="h",
                marker_color=[GRAY_SCALE[min(i, len(GRAY_SCALE)-1)] for i in range(len(top_city))],
                text=[fmt_usd(v) if campo_map != "FACTURA_KEY" else f"{v:,}" for v in top_city["VALOR"]],
                textposition="outside",
            ))
            chart_layout(fig_tc, f"Top 15 Ciudades — {metrica_mapa}", height=420)
            fig_tc.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig_tc, use_container_width=True)

        zona_map = dff.groupby("ZONA").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
        ).reset_index()
        zona_map["Zona_L"] = zona_map["ZONA"].str.title()
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            fig_zp = go.Figure(go.Pie(
                labels=zona_map["Zona_L"], values=zona_map["Venta"], hole=0.55,
                marker=dict(colors=GRAY_SCALE[:len(zona_map)], line=dict(color="#FFFFFF", width=2)),
                textfont=dict(size=10),
            ))
            chart_layout(fig_zp, "Participación de Venta por Zona", height=340)
            st.plotly_chart(fig_zp, use_container_width=True)
        with col_z2:
            fig_zu = go.Figure(go.Pie(
                labels=zona_map["Zona_L"], values=zona_map["Utilidad"], hole=0.55,
                marker=dict(colors=GRAY_SCALE[:len(zona_map)], line=dict(color="#FFFFFF", width=2)),
                textfont=dict(size=10),
            ))
            chart_layout(fig_zu, "Participación de Utilidad por Zona", height=340)
            st.plotly_chart(fig_zu, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error en Tab Mapa: {e}")

# ══════════════════════════════════════════════
#  TAB 4 — EJECUTIVOS
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Productividad por Ejecutivo</div>', unsafe_allow_html=True)
    try:
        ejec_gb = dff.groupby("EJECUTVO").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Descuento=("TOTAL DESCUENTO", "sum"), Pares=("PARES", "sum"),
            Facturas=("FACTURA_KEY", "nunique"),
        ).reset_index()
        ejec_gb["Margen%"] = ejec_gb["Utilidad"] / ejec_gb["Venta"].replace(0, np.nan) * 100
        ejec_gb["Ticket"]  = ejec_gb["Venta"] / ejec_gb["Facturas"].replace(0, np.nan)
        ejec_gb["Desc%"]   = ejec_gb["Descuento"] / ejec_gb["Venta"].replace(0, np.nan) * 100
        ejec_gb = ejec_gb.sort_values("Venta", ascending=False)
        ejec_gb["Ejecutivo"] = ejec_gb["EJECUTVO"].str.title()

        if not dff_metas.empty and "META_ANUAL" in dff_metas.columns:
            meta_lookup = dff_metas.set_index("EJECUTVO")["META_ANUAL"].to_dict()
            ejec_gb["Meta_Anual"] = ejec_gb["EJECUTVO"].map(meta_lookup).fillna(0)
            ejec_gb["Meta_Per"]   = ejec_gb["Meta_Anual"] * n_meses_sel / 12
            ejec_gb["Cumpl%"]     = np.where(ejec_gb["Meta_Per"] > 0,
                                              ejec_gb["Venta"] / ejec_gb["Meta_Per"] * 100, 0)

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=ejec_gb["Ejecutivo"], y=ejec_gb["Venta"], name="Venta Total",
                                  marker_color=COLORS["gray4"],
                                  text=[fmt_usd(v) for v in ejec_gb["Venta"]],
                                  textposition="outside", textfont=dict(size=9)))
            fig.add_trace(go.Bar(x=ejec_gb["Ejecutivo"], y=ejec_gb["Utilidad"], name="Utilidad",
                                  marker_color=COLORS["gray2"],
                                  text=[fmt_usd(v) for v in ejec_gb["Utilidad"]],
                                  textposition="outside", textfont=dict(size=9)))
            chart_layout(fig, "Venta y Utilidad por Ejecutivo", height=380)
            fig.update_layout(barmode="group", xaxis_tickangle=-30, legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            cats = ["Venta", "Utilidad", "Pares", "Facturas", "Ticket"]
            ejec_norm = ejec_gb.copy()
            for c in cats:
                mx = ejec_norm[c].max()
                ejec_norm[c+"_n"] = ejec_norm[c] / mx if mx > 0 else 0
            fig_r = go.Figure()
            for i, row in ejec_norm.iterrows():
                vals = [row[c+"_n"] for c in cats] + [row[cats[0]+"_n"]]
                color = GRAY_SCALE[i % len(GRAY_SCALE)]
                fig_r.add_trace(go.Scatterpolar(
                    r=vals, theta=cats + cats[:1], fill="toself", name=row["Ejecutivo"],
                    line=dict(color=color, width=1.5), fillcolor=hex_to_rgba(color, 0.12), opacity=0.85,
                ))
            chart_layout(fig_r, "Radar de Desempeño Multi-Métrica", height=380)
            fig_r.update_layout(
                polar=dict(bgcolor=COLORS["card"],
                           radialaxis=dict(visible=True, range=[0, 1], gridcolor=COLORS["gray1"], tickfont=dict(size=8)),
                           angularaxis=dict(gridcolor=COLORS["gray1"])),
                legend=dict(font=dict(size=9)),
            )
            st.plotly_chart(fig_r, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            ejec_s = ejec_gb.sort_values("Margen%", ascending=True)
            media_margen = ejec_gb["Margen%"].mean()
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=ejec_s["Margen%"], y=ejec_s["Ejecutivo"], orientation="h",
                marker_color=[COLORS["gray4"] if v > media_margen else COLORS["gray2"] for v in ejec_s["Margen%"]],
                text=[f"{v:.1f}%" for v in ejec_s["Margen%"]], textposition="outside",
            ))
            chart_layout(fig3, "Margen % por Ejecutivo (oscuro = sobre media)", height=340)
            fig3.update_layout(showlegend=False, xaxis_ticksuffix="%")
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            ejec_d = ejec_gb.sort_values("Ticket", ascending=True)
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(
                x=ejec_d["Ticket"], y=ejec_d["Ejecutivo"], orientation="h",
                marker_color=COLORS["gray3"],
                text=[fmt_usd(v) for v in ejec_d["Ticket"]], textposition="outside",
            ))
            chart_layout(fig4, "Ticket Promedio por Ejecutivo", height=340)
            fig4.update_layout(showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown('<div class="section-header">Tabla Resumen de Ejecutivos</div>', unsafe_allow_html=True)
        cols_tbl = ["Ejecutivo", "Venta", "Utilidad", "Descuento", "Pares", "Facturas", "Margen%", "Ticket", "Desc%"]
        if "Cumpl%" in ejec_gb.columns:
            cols_tbl.append("Cumpl%")
        tbl = ejec_gb[["Ejecutivo"] + [c for c in cols_tbl[1:] if c in ejec_gb.columns]].copy()
        for c, fn in [("Venta", fmt_usd), ("Utilidad", fmt_usd), ("Descuento", fmt_usd), ("Ticket", fmt_usd)]:
            if c in tbl.columns: tbl[c] = tbl[c].apply(fn)
        for c in ["Margen%", "Desc%"]:
            if c in tbl.columns: tbl[c] = tbl[c].apply(lambda v: f"{v:.1f}%")
        if "Cumpl%" in tbl.columns:
            tbl["Cumpl%"] = tbl["Cumpl%"].apply(lambda v: f"{v:.1f}%")
        tbl.rename(columns={"Venta": "Venta Total", "Utilidad": "Utilidad $", "Descuento": "Descuento $",
                             "Pares": "Unidades", "Margen%": "Margen %", "Ticket": "Ticket Prom.",
                             "Desc%": "% Desc.", "Cumpl%": f"Cumpl. {n_meses_sel}m"}, inplace=True)
        st.dataframe(tbl, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Error en Tab Ejecutivos: {e}")

# ══════════════════════════════════════════════
#  TAB 5 — MARCAS & PRODUCTOS
# ══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Desempeño por Marca y Tipo de Producto</div>', unsafe_allow_html=True)
    try:
        marca_gb = dff.groupby("MARCA").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Descuento=("TOTAL DESCUENTO", "sum"), Pares=("PARES", "sum"),
        ).reset_index().sort_values("Venta", ascending=False)
        marca_gb["Margen%"] = marca_gb["Utilidad"] / marca_gb["Venta"].replace(0, np.nan) * 100
        marca_gb["Marca_L"] = marca_gb["MARCA"].str.title()

        top_n = st.slider("Top N marcas a mostrar", 5, len(marca_gb), min(15, len(marca_gb)))
        marca_top = marca_gb.head(top_n)

        col1, col2 = st.columns([3, 2])
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=marca_top["Marca_L"], y=marca_top["Venta"], name="Venta",
                                  marker_color=COLORS["gray4"],
                                  text=[fmt_usd(v) for v in marca_top["Venta"]],
                                  textposition="outside", textfont=dict(size=9)))
            fig.add_trace(go.Bar(x=marca_top["Marca_L"], y=marca_top["Utilidad"], name="Utilidad",
                                  marker_color=COLORS["gray2"],
                                  text=[fmt_usd(v) for v in marca_top["Utilidad"]],
                                  textposition="outside", textfont=dict(size=9)))
            chart_layout(fig, f"Top {top_n} Marcas por Venta y Utilidad", height=380)
            fig.update_layout(barmode="group", xaxis_tickangle=-35, legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = go.Figure(go.Pie(
                labels=marca_top["Marca_L"], values=marca_top["Venta"], hole=0.5,
                marker=dict(colors=[GRAY_SCALE[i % len(GRAY_SCALE)] for i in range(len(marca_top))],
                            line=dict(color="#FFF", width=1.5)),
                textfont=dict(size=9),
            ))
            chart_layout(fig2, "Participación de Mercado (Venta)", height=380)
            fig2.update_layout(legend=dict(font=dict(size=9)))
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            max_pares = marca_top["Pares"].max() if marca_top["Pares"].max() > 0 else 1
            fig3 = go.Figure()
            for i, row in marca_top.iterrows():
                fig3.add_trace(go.Scatter(
                    x=[row["Venta"]], y=[row["Margen%"]], mode="markers+text",
                    marker=dict(size=max(8, row["Pares"] / max_pares * 40 + 6),
                                color=GRAY_SCALE[list(marca_top.index).index(i) % len(GRAY_SCALE)],
                                line=dict(color="#000", width=0.8)),
                    text=[row["Marca_L"]], textposition="top center", textfont=dict(size=8),
                    name=row["Marca_L"],
                ))
            chart_layout(fig3, "Venta vs Margen % por Marca (tamaño = unidades)", height=380)
            fig3.update_layout(showlegend=False, xaxis_tickprefix="$", yaxis_ticksuffix="%")
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            if "TIPO DE PRODUCTO" in dff.columns:
                prod_gb = dff.groupby("TIPO DE PRODUCTO").agg(
                    Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
                ).reset_index().sort_values("Venta", ascending=True)
                prod_gb["Margen%"] = prod_gb["Utilidad"] / prod_gb["Venta"].replace(0, np.nan) * 100
                prod_gb["Prod_L"]  = prod_gb["TIPO DE PRODUCTO"].str.title()
                fig4 = go.Figure(go.Bar(
                    x=prod_gb["Venta"], y=prod_gb["Prod_L"], orientation="h",
                    marker_color=[GRAY_SCALE[i % len(GRAY_SCALE)] for i in range(len(prod_gb))],
                    text=[fmt_usd(v) for v in prod_gb["Venta"]], textposition="outside",
                ))
                chart_layout(fig4, "Venta por Tipo de Producto", height=380)
                fig4.update_layout(showlegend=False)
                st.plotly_chart(fig4, use_container_width=True)

        st.markdown('<div class="section-header">Tipo de Venta: Contado vs Crédito</div>', unsafe_allow_html=True)
        if "TIPO DE VENTA" in dff.columns:
            tv_gb = dff.groupby(["TIPO DE VENTA", "MES"]).agg(Venta=("TOTAL VENTA", "sum")).reset_index()
            tv_gb["MES_NUM"] = tv_gb["MES"].map(MES_ORDER)
            tv_gb = tv_gb.sort_values("MES_NUM")
            tv_gb["MES_L"] = tv_gb["MES"].str.capitalize()
            fig5 = go.Figure()
            for i, tv in enumerate(tv_gb["TIPO DE VENTA"].unique()):
                s = tv_gb[tv_gb["TIPO DE VENTA"] == tv]
                fig5.add_trace(go.Scatter(
                    x=s["MES_L"], y=s["Venta"], name=tv.title(), mode="lines+markers+text",
                    line=dict(color=GRAY_SCALE[i * 2 % len(GRAY_SCALE)], width=2.5),
                    fill="tozeroy", fillcolor=hex_to_rgba(GRAY_SCALE[i * 2 % len(GRAY_SCALE)], 0.13),
                    text=[fmt_usd(v) for v in s["Venta"]],
                    textposition="top center", textfont=dict(size=9),
                ))
            chart_layout(fig5, "Evolución: Contado vs Crédito por Mes", height=300)
            fig5.update_layout(legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig5, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error en Tab Marcas: {e}")

# ══════════════════════════════════════════════
#  TAB 6 — ANÁLISIS DE VARIACIONES
# ══════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Análisis de Variaciones — ¿Por Qué Pasó?</div>', unsafe_allow_html=True)
    try:
        mes_var = dff.groupby("MES").agg(
            Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
            Descuento=("TOTAL DESCUENTO", "sum"), Costo=("COSTO_TOTAL", "sum"),
            Pares=("PARES", "sum"),
        ).reset_index()
        mes_var["MES_NUM"] = mes_var["MES"].map(MES_ORDER)
        mes_var = mes_var.sort_values("MES_NUM")
        mes_var["MES_L"]   = mes_var["MES"].str.capitalize()
        mes_var["Margen%"] = mes_var["Utilidad"] / mes_var["Venta"].replace(0, np.nan) * 100
        for col in ["Venta", "Utilidad", "Descuento", "Pares", "Margen%"]:
            mes_var[f"Δ{col}"] = mes_var[col].pct_change() * 100

        num_cols_corr = [c for c in ["TOTAL VENTA", "UTILIDAD TOTAL $", "TOTAL DESCUENTO",
                                      "COSTO_TOTAL", "PARES", "MARGEN_%"] if c in dff.columns]
        corr = dff[num_cols_corr].corr() if len(num_cols_corr) > 1 else pd.DataFrame()

        col1, col2 = st.columns(2)
        with col1:
            if not corr.empty:
                fig_heat = go.Figure(go.Heatmap(
                    z=corr.values, x=num_cols_corr, y=num_cols_corr,
                    colorscale=[[0, "#FFFFFF"], [0.5, "#9A9A9A"], [1, "#1A1A1A"]],
                    text=np.round(corr.values, 2), texttemplate="%{text}",
                    textfont=dict(size=11, color="#111"), zmin=-1, zmax=1,
                    showscale=True, colorbar=dict(title="Corr.", tickfont=dict(size=9)),
                ))
                chart_layout(fig_heat, "Mapa de Correlaciones entre Variables Clave", height=380)
                fig_heat.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("No hay suficientes columnas numéricas para el mapa de correlación.")

        with col2:
            mes_var2 = mes_var.dropna(subset=["ΔMargen%"])
            if not mes_var2.empty:
                fig_var = go.Figure()
                fig_var.add_trace(go.Bar(
                    x=mes_var2["MES_L"], y=mes_var2["ΔMargen%"],
                    marker_color=[COLORS["pos"] if v >= 0 else COLORS["neg"] for v in mes_var2["ΔMargen%"]],
                    text=[f"{v:+.1f}%" for v in mes_var2["ΔMargen%"]], textposition="outside",
                ))
                chart_layout(fig_var, "Variación Mes a Mes del Margen % (MoM)", height=380)
                fig_var.update_layout(showlegend=False, yaxis_ticksuffix="%")
                st.plotly_chart(fig_var, use_container_width=True)

        st.markdown('<div class="section-header">Impacto de Descuentos sobre Rentabilidad</div>', unsafe_allow_html=True)
        if "% DE DESCUENTO" in dff.columns:
            dff2 = dff.copy()
            dff2["% DE DESCUENTO"] = dff2["% DE DESCUENTO"].fillna(0)
            bins = [-0.01, 0.001, 0.05, 0.10, 0.20, 0.30, 1.01]
            labs = ["Sin dcto.", "1-5%", "5-10%", "10-20%", "20-30%", ">30%"]
            dff2["Rango_Dcto"] = pd.cut(dff2["% DE DESCUENTO"], bins=bins, labels=labs)
            dcto_rng = dff2.groupby("Rango_Dcto", observed=True).agg(
                Venta=("TOTAL VENTA", "sum"), Utilidad=("UTILIDAD TOTAL $", "sum"),
                Cnt=("FACTURA_KEY", "count"),
            ).reset_index()
            dcto_rng["Margen%"] = dcto_rng["Utilidad"] / dcto_rng["Venta"].replace(0, np.nan) * 100

            col3, col4 = st.columns(2)
            with col3:
                fig6 = make_subplots(specs=[[{"secondary_y": True}]])
                fig6.add_trace(go.Bar(x=dcto_rng["Rango_Dcto"].astype(str), y=dcto_rng["Venta"],
                                       name="Venta", marker_color=COLORS["gray3"],
                                       text=[fmt_usd(v) for v in dcto_rng["Venta"]],
                                       textposition="outside", textfont=dict(size=9)), secondary_y=False)
                fig6.add_trace(go.Scatter(
                    x=dcto_rng["Rango_Dcto"].astype(str), y=dcto_rng["Margen%"],
                    name="Margen%", mode="lines+markers+text",
                    line=dict(color=COLORS["gray5"], width=2.5), marker=dict(size=8),
                    text=[f"{v:.1f}%" for v in dcto_rng["Margen%"]],
                    textposition="top center", textfont=dict(size=10),
                ), secondary_y=True)
                fig6.update_yaxes(title_text="Venta $", secondary_y=False, tickprefix="$")
                fig6.update_yaxes(title_text="Margen %", secondary_y=True, ticksuffix="%", showgrid=False)
                chart_layout(fig6, "Rango de Descuento vs Margen%", height=380)
                fig6.update_layout(legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig6, use_container_width=True)

            with col4:
                seg_zona = dff.groupby(["ZONA", "SEGMENTO"]).agg(Utilidad=("UTILIDAD TOTAL $", "sum")).reset_index()
                fig7 = go.Figure()
                for i, seg in enumerate(seg_zona["SEGMENTO"].unique()):
                    s = seg_zona[seg_zona["SEGMENTO"] == seg]
                    fig7.add_trace(go.Bar(
                        x=[z.title() for z in s["ZONA"]], y=s["Utilidad"],
                        name=seg.title(), marker_color=GRAY_SCALE[i * 2 % len(GRAY_SCALE)],
                        text=[fmt_usd(v) for v in s["Utilidad"]],
                        textposition="inside", textfont=dict(size=9, color="#FFFFFF"),
                    ))
                chart_layout(fig7, "Utilidad por Zona y Segmento", height=380)
                fig7.update_layout(barmode="stack", xaxis_tickangle=-25, legend=dict(orientation="h", y=-0.25))
                st.plotly_chart(fig7, use_container_width=True)
        else:
            st.warning("La columna '% DE DESCUENTO' no está presente en los datos.")

        # Tabla MoM
        st.markdown('<div class="section-header">Variaciones Mes a Mes (MoM)</div>', unsafe_allow_html=True)
        tbl2 = mes_var[["MES_L", "Venta", "Utilidad", "Descuento", "Margen%",
                         "ΔVenta", "ΔUtilidad", "ΔDescuento", "ΔMargen%"]].copy()
        for c in ["Venta", "Utilidad", "Descuento"]:
            tbl2[c] = tbl2[c].apply(fmt_usd)
        tbl2["Margen%"] = tbl2["Margen%"].apply(lambda v: f"{v:.1f}%")
        for c in ["ΔVenta", "ΔUtilidad", "ΔDescuento", "ΔMargen%"]:
            tbl2[c] = tbl2[c].apply(lambda v: f"{v:+.1f}%" if pd.notna(v) else "—")
        tbl2.columns = ["Mes", "Venta", "Utilidad", "Descuento", "Margen%",
                         "Δ Venta", "Δ Utilidad", "Δ Descuento", "Δ Margen%"]
        st.dataframe(tbl2, use_container_width=True, hide_index=True)

        # Insights automáticos
        st.markdown('<div class="section-header">Insights Automáticos</div>', unsafe_allow_html=True)
        mejor_zona  = dff.groupby("ZONA")["UTILIDAD TOTAL $"].sum().idxmax()    if "ZONA" in dff.columns and not dff.empty else "N/A"
        peor_zona   = dff.groupby("ZONA")["UTILIDAD TOTAL $"].sum().idxmin()    if "ZONA" in dff.columns and not dff.empty else "N/A"
        mejor_marca = dff.groupby("MARCA")["UTILIDAD TOTAL $"].sum().idxmax()   if "MARCA" in dff.columns and not dff.empty else "N/A"
        mejor_ejec  = dff.groupby("EJECUTVO")["TOTAL VENTA"].sum().idxmax()     if "EJECUTVO" in dff.columns and not dff.empty else "N/A"
        mayor_desc  = dff.groupby("EJECUTVO")["TOTAL DESCUENTO"].sum().idxmax() if "EJECUTVO" in dff.columns and not dff.empty else "N/A"

        cumpl_insight = ""
        if not dff_metas.empty and "META_ANUAL" in dff_metas.columns:
            ventas_e = dff.groupby("EJECUTVO")["TOTAL VENTA"].sum().reset_index()
            comp_e   = pd.merge(ventas_e, dff_metas[["EJECUTVO", "META_ANUAL"]], on="EJECUTVO", how="inner")
            comp_e["Cumpl"] = comp_e["TOTAL VENTA"] / (comp_e["META_ANUAL"] * n_meses_sel / 12) * 100
            if not comp_e.empty:
                ejec_bajo = comp_e.loc[comp_e["Cumpl"].idxmin(), "EJECUTVO"]
                pct_bajo  = comp_e["Cumpl"].min()
                cumpl_insight = (f"⚠️ El ejecutivo con menor cumplimiento es <b>{ejec_bajo.title()}</b> "
                                 f"con <b>{pct_bajo:.1f}%</b> — requiere atención inmediata.")

        insights = [
            f"🏆 La zona con mayor utilidad acumulada es <b>{mejor_zona.title()}</b>, mientras que <b>{peor_zona.title()}</b> es la de menor contribución.",
            f"📦 La marca más rentable del período es <b>{mejor_marca.title()}</b>.",
            f"👤 El ejecutivo con mayor volumen de venta es <b>{mejor_ejec.title()}</b>.",
            f"⚠️ <b>{mayor_desc.title()}</b> es el ejecutivo con mayor monto en descuentos — revisar política.",
            f"📉 A mayor rango de descuento, el margen tiende a disminuir (ver gráfico Rango de Descuento vs Margen%).",
            f"📊 La correlación entre Descuento y Utilidad indica qué tanto afectan los descuentos a la rentabilidad real.",
        ]
        if cumpl_insight:
            insights.insert(2, cumpl_insight)
        for ins in insights:
            st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Error en Tab Variaciones: {e}")

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style='border-top:1px solid {COLORS["border"]};padding:16px 0;
     display:flex;justify-content:space-between;
     font-size:0.72rem;color:{COLORS["text_light"]};'>
  <span>Dashboard Ejecutivo de Ventas 2026 · v2.0 — Alto Contraste</span>
  <span>Datos: Enero–Diciembre 2026 · Actualización mensual automática</span>
</div>
""", unsafe_allow_html=True)
