"""SombraBAQ - Plataforma Geoespacial, Red Social Ambiental y Reportes Ciudadanos."""
import base64, datetime as dt, hashlib, io, json, math, re, uuid, time
import folium, pandas as pd, requests, streamlit as st
from streamlit_folium import st_folium
from zoneinfo import ZoneInfo

st.set_page_config(page_title="SombraBAQ | Observatorio climático", page_icon=":material/park:", layout="wide")

def gee_service_account_credentials(info):
    from google.oauth2 import service_account

    account_info = dict(info)
    account_info["private_key"] = str(account_info.get("private_key") or "").replace("\\n", "\n").strip()
    account_info.setdefault("token_uri", "https://oauth2.googleapis.com/token")
    return service_account.Credentials.from_service_account_info(
        account_info,
        scopes=[
            "https://www.googleapis.com/auth/earthengine",
            "https://www.googleapis.com/auth/cloud-platform",
        ],
    )


def gee_error_message(error, info):
    message = str(error)
    if info:
        private_key = str(info.get("private_key") or "").replace("\\n", "\n").strip()
        email = str(info.get("client_email") or "").strip()
        for secret in (private_key, private_key.replace("\n", "\\n"), email):
            if secret:
                message = message.replace(secret, "[dato sensible oculto]")
    return message[:600]


st.markdown("""<style>
.block-container {padding:1.45rem 2rem 3.2rem !important; max-width:1520px;}
.hero {background:radial-gradient(ellipse at 92% 10%,rgba(134,239,172,.2),transparent 30%),linear-gradient(118deg,#102f25 0%,#166534 58%,#087f73 100%); border:1px solid rgba(255,255,255,.18); border-radius:24px; padding:2rem 2.1rem 1.65rem; margin-bottom:1.15rem; color:white; box-shadow:0 16px 42px rgba(18,55,42,.18); position:relative; overflow:hidden; isolation:isolate;}
.hero:after {content:""; position:absolute; width:320px; height:320px; right:-85px; top:-190px; border-radius:50%; border:1px solid rgba(255,255,255,.13); box-shadow:0 0 0 24px rgba(255,255,255,.035),0 0 0 52px rgba(255,255,255,.025); pointer-events:none; z-index:-1;}
.hero-kicker {display:inline-flex; align-items:center; gap:.55rem; margin-bottom:.45rem; padding:.34rem .78rem; border:1px solid rgba(255,255,255,.24); border-radius:999px; background:rgba(255,255,255,.11); color:#f0fdf4; font-size:.7rem; font-weight:750; letter-spacing:.1em;}
.hero-kicker:before {content:""; width:.48rem; height:.48rem; border-radius:50%; background:#86efac; box-shadow:0 0 0 4px rgba(134,239,172,.14); animation:hero-glow 2.4s ease-in-out infinite;}
.hero h1 {margin:.15rem 0 .3rem; font-size:2.35rem; font-weight:800; color:white; letter-spacing:-.04em; line-height:1.1;}
.hero p {margin:0; color:rgba(255,255,255,.86); font-weight:450; font-size:1rem; max-width:720px; line-height:1.55;}
.hero-tags {display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.15rem;}
.hero-tag {display:inline-flex; align-items:center; gap:.38rem; padding:.35rem .7rem; border:1px solid rgba(255,255,255,.17); border-radius:999px; background:rgba(4,30,22,.2); color:rgba(255,255,255,.94); font-size:.76rem; font-weight:600;}
.hero-tag span {color:#bbf7d0;}
@keyframes hero-glow {50% {opacity:.55; box-shadow:0 0 0 7px rgba(134,239,172,.08);}}
[data-testid="stSidebar"] {border-right:1px solid rgba(22,101,52,.10);}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {line-height:1.45;}
[data-testid="stTabs"] [role="tablist"] {gap:.3rem; border-bottom:1px solid rgba(22,101,52,.14); margin-bottom:1rem; scrollbar-width:thin;}
[data-testid="stTabs"] [role="tab"] {padding:.72rem .9rem; border-radius:12px 12px 0 0; transition:background .18s ease, color .18s ease, transform .18s ease;}
[data-testid="stTabs"] [role="tab"]:hover {background:rgba(22,101,52,.06);}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {background:rgba(22,101,52,.1); color:#166534; font-weight:700; box-shadow:inset 0 -2px #166534;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px; transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease;}
[data-testid="stVerticalBlockBorderWrapper"]:hover {border-color:rgba(22,101,52,.23); box-shadow:0 8px 24px rgba(18,55,42,.055);}
[data-testid="stMetric"] {padding:.35rem .25rem; transition:transform .18s ease;}
[data-testid="stMetric"]:hover {transform:translateY(-3px);}
[data-testid="stMetricValue"] {letter-spacing:-.03em;}
[data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {border-radius:10px; transition:transform .15s ease, box-shadow .15s ease;}
[data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover {transform:translateY(-1px); box-shadow:0 5px 14px rgba(22,101,52,.14);}
[data-testid="stButton"] button:focus-visible, [data-testid="stFormSubmitButton"] button:focus-visible, [data-testid="stTabs"] [role="tab"]:focus-visible {outline:3px solid rgba(22,101,52,.45); outline-offset:2px;}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {border-color:#166534; box-shadow:0 0 0 .15rem rgba(22,101,52,.14);}
[data-testid="stForm"] {border-radius:14px;}
[data-testid="stDataFrame"], [data-testid="stTable"] {border-radius:12px; overflow:hidden;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {margin-bottom:.65rem;}
[data-testid="stSlider"] {padding-top:.2rem;}
::-webkit-scrollbar {width:8px; height:8px;}
::-webkit-scrollbar-thumb {background:#bfd1c4; border-radius:8px;}
::-webkit-scrollbar-track {background:transparent;}
iframe[title="st_folium"] {border-radius:16px; border:1px solid rgba(22,101,52,.14);}
.live-status {border:1px solid rgba(22,101,52,.16); border-radius:14px; padding:.65rem .85rem; margin:.25rem 0 1rem; background:rgba(240,253,244,.58);}
.leyenda {height:8px; border-radius:6px; background:linear-gradient(90deg,#22c55e,#a3e635,#facc15,#fb923c,#ef4444); margin:.45rem 0 .25rem;}
.social-card {background:#f8fafc; border:1px solid #e2e8f0; border-radius:16px; padding:1.35rem; margin-bottom:1rem; box-shadow:0 4px 14px rgba(0,0,0,.045);}
.species-card {border:1px solid rgba(22,101,52,.14); border-radius:16px; padding:1rem; height:100%; background:rgba(255,255,255,.55);}
[data-testid="stStatusWidget"], [data-testid="stAppDeployButton"],
[data-testid="stDecoration"], [data-testid="stSkillsNudge"], [data-testid="stSkillsNudgeAnchor"],
#MainMenu, footer {display:none !important; visibility:hidden !important;}
@media (max-width: 720px) {
    .block-container {padding:.8rem .85rem 2rem !important;}
    .hero {padding:1.3rem 1.2rem 1.1rem; border-radius:18px; margin-bottom:.9rem;}
    .hero h1 {font-size:1.8rem;}
    .hero p {font-size:.92rem;}
    .hero-tags {gap:.4rem; margin-top:.9rem;}
    .hero-tag {font-size:.7rem; padding:.32rem .58rem;}
    [data-testid="stDialog"] [data-testid="stForm"] {padding:.75rem !important;}
    [data-testid="stDialog"] [data-testid="stTextInput"],
    [data-testid="stDialog"] [data-testid="stSelectbox"] {margin-bottom:.2rem;}
    [data-testid="stTabs"] [role="tab"] {padding:.6rem .65rem;}
    iframe[title="st_folium"] {border-radius:12px;}
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {scroll-behavior:auto !important; animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important;}
}
</style>""", unsafe_allow_html=True)

if st.session_state.get("modo_oscuro", False):
    st.markdown("""<style>
:root, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
    color-scheme:dark;
    --primary-color:#4ade80;
    --background-color:#0d1712;
    --secondary-background-color:#15221b;
    --text-color:#e5eee8;
    --link-color:#86efac;
    --border-color:#2a3d32;
    --dataframe-border-color:#2a3d32;
    --code-background-color:#19271f;
}
html, body, .stApp {background-color:#0d1712 !important; color:#e5eee8;}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {background-color:#0d1712; color:#e5eee8;}
[data-testid="stSidebar"] {background-color:#101d16; color:#e5eee8; border-color:#2a3d32;}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stCaptionContainer"], label {color:#e5eee8;}
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"],
[data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stTable"] {
    background-color:#15221b;
    border-color:#2a3d32;
}
[data-testid="stVerticalBlock"], [data-testid="stMetric"] {border-color:#2a3d32 !important;}
[data-testid="stMetric"] {background-color:#15221b;}
[data-testid="stTabs"] [role="tablist"] {border-color:#2a3d32;}
[data-testid="stTabs"] [role="tab"]:hover {background:rgba(74,222,128,.08);}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color:#86efac;
    background:rgba(74,222,128,.12);
    box-shadow:inset 0 -2px #4ade80;
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input, [data-testid="stSelectbox"] [role="group"] {
    background-color:#101d16;
    color:#e5eee8;
    border-color:#35483c;
}
[data-testid="stSelectbox"] [role="combobox"] {background:transparent; color:#e5eee8;}
[data-testid="stSelectbox"] [role="group"] button {color:#e5eee8;}
[role="listbox"], [role="option"] {background-color:#15221b; color:#e5eee8;}
[role="option"][aria-selected="true"] {background-color:#254132; color:#f0fdf4;}
[data-testid="stAlertContainer"] {
    background-color:#1a2a21 !important;
    color:#e5eee8 !important;
    border:1px solid #344c3a !important;
}
[data-testid="stMetricDelta"] {background-color:#1a3b2d; color:#a7f3d0;}
[data-testid="stMetricChart"] {display:none !important;}
[data-testid="stDialog"] {background-color:#15221b; border-color:#2a3d32;}
[data-testid="stButton"] button:not([kind="primary"]),
[data-testid="stFormSubmitButton"] button:not([kind="primary"]) {
    background-color:#1a2a21;
    color:#e5eee8;
    border-color:#35483c;
}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background-color:#166534;
    color:#fff;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {border-color:#42624c; box-shadow:0 8px 24px rgba(0,0,0,.2);}
.live-status {background:#15251c; border-color:#31513a;}
.social-card, .species-card {background:#15221b; border-color:#2a3d32; color:#e5eee8;}
::-webkit-scrollbar-thumb {background:#40564a;}
iframe[title="st_folium"] {border-color:#2a3d32;}
</style>""", unsafe_allow_html=True)

# ---------- CONSTANTES Y CONFIGURACIÓN ----------
ZONAS = {"Suroccidente": (10.950, -74.830), "Suroriente": (10.940, -74.780), "Metropolitana": (10.925, -74.800), "Norte-Centro Histórico": (10.985, -74.795), "Riomar": (11.015, -74.820)}
RADIO_M = 1500
PUNTOS = {"siembra": 50, "residuos": 20, "mantenimiento": 10}
TIPOS = {"siembra": "Siembra de árbol", "residuos": "Foco de residuos", "mantenimiento": "Mantenimiento de árbol"}
ICONOS = {"Libros": "📚", "Descuentos": "🏷️", "Cine": "🎬", "Comida": "🍔", "Naturaleza": "🌱", "Otros": "🎁"}
TIPOS_DOC = {"CC": "Cédula de ciudadanía", "CE": "Cédula de extranjería", "PPT": "Permiso por protección temporal", "PA": "Pasaporte"}
PALETA = ["#22c55e", "#a3e635", "#facc15", "#fb923c", "#ef4444"]
BASES = {"Oscuro": ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", 16), "Calles": ("https://tile.openstreetmap.org/{z}/{x}/{y}.png", 19), "Satélite": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 18)}
PLANTAS = [
    {"nombre": "Roble morado", "cientifico": "Tabebuia rosea", "origen": "Nativo", "tipo": "Árbol grande", "sombra": "Alta", "agua": "Media", "espacio": "Amplio", "uso": "Bulevares, parques y avenidas amplias.", "cuidado": "Luz solar directa y podas formativas durante los primeros años."},
    {"nombre": "Campano / Samán", "cientifico": "Samanea saman", "origen": "Nativo del neotrópico", "tipo": "Árbol muy grande", "sombra": "Muy alta", "agua": "Media-baja", "espacio": "Muy amplio", "uso": "Parques grandes y zonas con espacio para raíces.", "cuidado": "Evitar cercanía a redes, tuberías y cimentaciones."},
    {"nombre": "Ceiba / Bonga", "cientifico": "Ceiba pentandra", "origen": "Nativo", "tipo": "Árbol gigante", "sombra": "Muy alta", "agua": "Media", "espacio": "Excepcional", "uso": "Áreas naturales o grandes reservas urbanas.", "cuidado": "Requiere evaluación técnica por su tamaño adulto y contrafuertes."},
    {"nombre": "Matarratón", "cientifico": "Gliricidia sepium", "origen": "Nativo neotropical", "tipo": "Árbol mediano", "sombra": "Media-alta", "agua": "Media-baja", "espacio": "Mediano", "uso": "Cercas vivas, corredores y restauración.", "cuidado": "Propagación y podas según el plan local de arborización."},
    {"nombre": "Uvero", "cientifico": "Coccoloba uvifera", "origen": "Nativo costero", "tipo": "Árbol pequeño-mediano", "sombra": "Media", "agua": "Baja-media", "espacio": "Mediano", "uso": "Costas, espacios cálidos y suelos arenosos.", "cuidado": "Prefiere alta exposición solar y buena drenaje."},
    {"nombre": "Guayacán amarillo", "cientifico": "Handroanthus ochraceus", "origen": "Nativo", "tipo": "Árbol mediano", "sombra": "Media", "agua": "Media", "espacio": "Mediano", "uso": "Zonas verdes y separación de vías.", "cuidado": "Verificar disponibilidad comercial y procedencia local."},
]

def rampa(v, lo, hi): return PALETA[min(4, max(0, int((v - lo) / (hi - lo) * 5)))]
def zona_cercana(lat, lng): return min(ZONAS, key=lambda z: math.hypot(lat - ZONAS[z][0], (lng - ZONAS[z][1]) * math.cos(math.radians(lat))))

# ---------- CONEXIÓN SUPABASE ----------
def cfg():
    try: sec = dict(st.secrets["supabase"])
    except Exception: sec = {}
    url = (sec.get("url") or "").strip().strip("\"'").rstrip("/").split("/rest/v1")[0]
    if not url or url == "https://": url = "https://tzhjzldfrgpvymokuopn.supabase.co"
    if not url.startswith("http"): url = "https://" + url
    key = (sec.get("anon_key") or "").strip().strip("\"'")
    return url, key

@st.cache_resource
def pub():
    from supabase import create_client
    url, key = cfg()
    if not key:
        raise RuntimeError("Supabase no está configurado. Añade [supabase].anon_key en los secretos de la aplicación.")
    return create_client(url, key)

def sb_client():
    from supabase import create_client
    if "sb" not in st.session_state:
        url, key = cfg()
        if not key:
            raise RuntimeError("Supabase no está configurado. Añade [supabase].anon_key en los secretos de la aplicación.")
        st.session_state.sb = create_client(url, key)
        st.session_state.user = None; st.session_state.admin = False
    return st.session_state.sb

@st.cache_data(ttl=30)
def reportes_publicos():
    rows = pub().table("reportes").select("id,created_at,tipo,zona,lat,lng,nota,puntos,estado,foto_path,user_id").in_("estado", ["aprobado", "verificado_ia"]).order("created_at", desc=True).limit(200).execute().data
    return pd.DataFrame(rows, columns=["id", "created_at", "tipo", "zona", "lat", "lng", "nota", "puntos", "estado", "foto_path", "user_id"])

def obtener_saldo(sb, user_id):
    try:
        ganados = sum(r["puntos"] for r in sb.table("reportes").select("puntos").eq("user_id", user_id).eq("estado", "aprobado").execute().data)
        gastados = sum(c["puntos"] for c in sb.table("canjes").select("puntos").eq("user_id", user_id).execute().data)
    except Exception as error:
        st.error(f"No se pudo consultar el saldo de puntos ({type(error).__name__}).")
        st.stop()

    try:
        resultado_eventos = sb.rpc("puntos_eventos_confirmados").execute().data
        puntos_eventos = int(resultado_eventos or 0)
    except Exception as error:
        codigo = getattr(error, "code", None)
        if codigo not in ("PGRST202", "42883") and "puntos_eventos_confirmados" not in str(error):
            st.error(f"No se pudieron consultar los puntos de eventos ({type(error).__name__}).")
            st.stop()
        if not st.session_state.get("aviso_migracion_eventos"):
            st.warning("Los puntos por eventos se activarán al aplicar `supabase_events.sql` en Supabase.")
            st.session_state.aviso_migracion_eventos = True
        puntos_eventos = 0

    ganados += puntos_eventos
    return ganados - gastados, ganados


def formato_fecha_evento(valor):
    fecha = dt.datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=dt.timezone.utc)
    return fecha.astimezone(ZoneInfo("America/Bogota")).strftime("%d %b %Y · %I:%M %p")


EVENTOS_SUGERIDOS = [
    "Jornada de arborización participativa",
    "Brigada de limpieza de espacio público",
    "Taller práctico de compostaje",
    "Caminata de observación de biodiversidad",
    "Taller de separación de residuos",
    "Jornada de cuidado de árboles",
]

# ---------- EXTRACCIÓN DE DATOS SATELITALES Y CLIMA ----------
@st.cache_resource
def init_ee():
    try:
        import ee
        try:
            info = dict(st.secrets["gee_service_account"])
        except (KeyError, FileNotFoundError):
            info = None

        if info:
            project_id = str(info.get("project_id", "")).strip()
            missing = [
                name for name, value in (
                    ("client_email", str(info.get("client_email") or "").strip()),
                    ("private_key", str(info.get("private_key") or "").strip()),
                    ("project_id", project_id),
                )
                if not value
            ]
            if missing:
                return "Faltan campos de Google Earth Engine en [gee_service_account]: " + ", ".join(missing)
            credentials = gee_service_account_credentials(info)
            ee.Initialize(credentials, project=project_id)
        else:
            ee.Initialize(project="sombrabaq")
        return ee
    except Exception as e: return str(e)

@st.cache_data(ttl=3 * 3600, show_spinner="Consultando satélites (Sentinel-2 y Landsat)…")
def satelite(dias: int):
    ee = init_ee()
    if isinstance(ee, str): return None, None, ee
    area = ee.Geometry.Rectangle([-74.90, 10.88, -74.72, 11.06])
    fin = ee.Date(dt.datetime.now(dt.timezone.utc)); ini = fin.advance(-dias, "day")
    mask_s2 = lambda i: i.updateMask(i.select("SCL").gte(4).And(i.select("SCL").lte(7)))
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(area).filterDate(ini, fin).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(mask_s2)
    ndvi = s2.median().normalizedDifference(["B8", "B4"]).rename("NDVI")
    def lst_img(i):
        qa = i.select("QA_PIXEL"); ok = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        return i.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST").updateMask(ok)
    ls = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")).filterBounds(area).filterDate(ini, fin).map(lst_img)
    lst = ls.median()
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lng, lat]).buffer(RADIO_M), {"zona": n}) for n, (lat, lng) in ZONAS.items()])
    res = ndvi.addBands(lst).reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]
    df = pd.DataFrame([{"Zona": f["properties"]["zona"], "NDVI": f["properties"].get("NDVI"), "LST (°C)": f["properties"].get("LST")} for f in res])
    tiles = {"NDVI": ndvi.getMapId({"min": 0, "max": 0.8, "palette": ["#8c510a", "#d8b365", "#f6e8c3", "#a6d96a", "#1a9641"]})["tile_fetcher"].url_format,
             "LST": lst.getMapId({"min": 28, "max": 45, "palette": ["#2c7bb6", "#ffffbf", "#fdae61", "#d7191c"]})["tile_fetcher"].url_format}
    def pts(img, banda, n, minimo=None):
        try: fs = img.sample(region=area, scale=120, numPixels=800, seed=11, geometries=True, dropNulls=True).limit(800).getInfo()["features"]
        except Exception: return []
        o = sorted(((f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], f["properties"][banda]) for f in fs if banda in f["properties"]), key=lambda t: -t[2])
        if minimo is None: minimo = o[int(len(o) * 0.15)][2] if o else 0
        o = [p for p in o if p[2] >= minimo]
        return o[::max(1, len(o) // n)][:n]
    def sitios(n=12):
        try: fs = ndvi.addBands(lst).sample(region=area, scale=120, numPixels=900, seed=5, geometries=True, dropNulls=True).limit(900).getInfo()["features"]
        except Exception: return []
        c = [(f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], f["properties"]["NDVI"], f["properties"]["LST"]) for f in fs if "NDVI" in f["properties"] and "LST" in f["properties"] and 0.02 <= f["properties"]["NDVI"] <= 0.22]
        c.sort(key=lambda t: -(t[3] - 40 * t[2]))
        out = []
        for p in c:
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 0.006 for q in out): out.append(p)
            if len(out) >= n: break
        return out
    return df, tiles, {"escenas_s2": s2.size().getInfo(), "escenas_landsat": ls.size().getInfo(), "arboles": pts(ndvi, "NDVI", 150, 0.5), "calientes": pts(lst, "LST", 60), "plantar": sitios()}

@st.cache_data(ttl=600)
def clima_vivo():
    r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=15, params={"latitude": ",".join(str(v[0]) for v in ZONAS.values()), "longitude": ",".join(str(v[1]) for v in ZONAS.values()), "current": "temperature_2m,apparent_temperature,relative_humidity_2m,uv_index", "timezone": "America/Bogota"})
    r.raise_for_status()
    d = r.json(); d = d if isinstance(d, list) else [d]
    return pd.DataFrame([{"Zona": z, "Temp (°C)": x["current"]["temperature_2m"], "Sensación (°C)": x["current"]["apparent_temperature"], "Humedad (%)": x["current"]["relative_humidity_2m"], "UV": x["current"]["uv_index"], "Hora": x["current"]["time"]} for z, x in zip(ZONAS, d)])

@st.cache_data(ttl=900)
def calidad_aire():
    try:
        r = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality", timeout=15, params={"latitude": ",".join(str(v[0]) for v in ZONAS.values()), "longitude": ",".join(str(v[1]) for v in ZONAS.values()), "current": "us_aqi,pm2_5,pm10", "timezone": "America/Bogota"})
        if r.ok:
            d = r.json(); d = d if isinstance(d, list) else [d]
            return pd.DataFrame([{"Zona": z, "AQI": x["current"]["us_aqi"], "PM2.5": x["current"]["pm2_5"], "PM10": x["current"]["pm10"]} for z, x in zip(ZONAS, d)])
    except: return None

# ---------- INTELIGENCIA ARTIFICIAL Y REPORTES ----------
OBJETIVO = {"siembra": "un árbol o plántula recién sembrada", "mantenimiento": "un árbol siendo cuidado", "residuos": "basura acumulada o escombros"}

def analizar_foto(datos, tipo):
    from PIL import Image

    imagen = Image.open(io.BytesIO(datos)).convert("RGB")
    imagen.thumbnail((1280, 1280))
    try:
        cfg = dict(st.secrets["anthropic"])
    except (KeyError, FileNotFoundError):
        cfg = {}
    if not cfg.get("api_key"):
        return {
            "cumple": False,
            "confianza": 0.0,
            "metodo": "Revisión manual",
            "detalle": "El servicio de visión no está configurado; no se usó un filtro de color.",
        }

    try:
        import anthropic

        buffer = io.BytesIO()
        imagen.save(buffer, "JPEG", quality=90)
        objetivo = OBJETIVO[tipo]
        criterio = (
            "Para una plantación, busca una plántula o árbol joven claramente colocado en tierra, "
            "con el tallo y el punto de plantación visibles. No cuentes árboles adultos ya establecidos, "
            "césped, hojas, viveros, plantas en maceta, imágenes de pantalla ni vegetación de fondo como "
            "evidencia de una plantación reciente. Si el encuadre no muestra señales suficientes, marca "
            "cumple=false y baja confianza. Una foto nunca demuestra quién sembró, cuándo ocurrió ni "
            "si el lugar tiene permisos. "
            if tipo == "siembra"
            else "Evalúa solo lo visible en la imagen. Si el objetivo no aparece claramente o la evidencia "
            "es ambigua, marca cumple=false y baja confianza. "
        )
        prompt = (
            f"Evalúa si la imagen aporta evidencia visual de {objetivo}. {criterio}"
            "No infieras hechos fuera del encuadre. Responde exclusivamente con un objeto JSON válido "
            'con este esquema: {"cumple": boolean, "confianza": number entre 0 y 1, '
            '"detalle": "descripción breve de elementos visibles y limitaciones"}. '
            "La confianza representa únicamente la claridad visual, no la autenticidad, fecha, ubicación "
            "ni realización de la acción."
        )
        respuesta = anthropic.Anthropic(api_key=cfg["api_key"]).messages.create(
            model=cfg.get("model", "claude-haiku-5-5"),
            max_tokens=250,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.b64encode(buffer.getvalue()).decode(),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        texto = "\n".join(
            bloque.text for bloque in respuesta.content if getattr(bloque, "type", None) == "text"
        )
        coincidencia = re.search(r"\{.*\}", texto, re.S)
        if not coincidencia:
            raise ValueError("La respuesta del servicio no contiene JSON.")
        resultado = json.loads(coincidencia.group())
        cumple = resultado.get("cumple")
        confianza = resultado.get("confianza")
        detalle = resultado.get("detalle")
        if (
            not isinstance(cumple, bool)
            or isinstance(confianza, bool)
            or not isinstance(confianza, (int, float))
            or not math.isfinite(confianza)
            or not 0 <= confianza <= 1
            or not isinstance(detalle, str)
        ):
            raise ValueError("La respuesta del servicio no cumple el formato esperado.")
        return {
            "cumple": cumple,
            "confianza": float(confianza),
            "metodo": "Claude Vision · orientativo",
            "detalle": detalle.strip()[:400],
        }
    except Exception as error:
        return {
            "cumple": False,
            "confianza": 0.0,
            "metodo": "Revisión manual",
            "detalle": f"El análisis visual no se pudo validar ({type(error).__name__}); no se otorgará una aprobación automática.",
        }

def validar_evidencia(datos):
    if len(datos) > 8 * 1024 * 1024:
        return None, "La imagen supera el limite de 8 MB."
    try:
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(datos)) as original:
            original.verify()
        with Image.open(io.BytesIO(datos)) as original:
            imagen = ImageOps.exif_transpose(original).convert("RGB")
            imagen.thumbnail((1600, 1600))
            salida = io.BytesIO()
            imagen.save(salida, "JPEG", quality=88)
        return salida.getvalue(), None
    except Exception:
        return None, "El archivo no contiene una imagen valida."

def _publicar(sb, user, ia, zona_cercana, reportes_publicos):
    try:
        hash_foto = hashlib.sha256(ia["datos"]).hexdigest()
        duplicados = sb.table("reportes").select("id").eq("foto_hash", hash_foto).limit(1).execute().data
        if duplicados:
            st.error("Esta misma evidencia ya fue registrada. No se otorgaran puntos adicionales.")
            return
        ruta = f"{user.id}/{uuid.uuid4().hex}.jpg"
        sb.storage.from_("evidencias").upload(ruta, ia["datos"], {"content-type": ia["mime"]})
        sugerencia_ia = "compatible con el objetivo visual" if ia["cumple"] else "insuficiente o no concluyente"
        sb.table("reportes").insert({
            "user_id": user.id, "tipo": ia["tipo"], "lat": ia["pin"][0], "lng": ia["pin"][1], 
            "zona": zona_cercana(*ia["pin"]), "nota": ia["nota"], "foto_path": ruta, 
            "estado": "pendiente", "puntos": PUNTOS[ia["tipo"]], "ia_confianza": ia["confianza"],
            "ia_detalle": f"[{ia['metodo']}] Evidencia {sugerencia_ia}; {ia['detalle']}"[:500],
            "foto_hash": hash_foto
        }).execute()
        
        st.session_state.pop("ia", None); st.session_state.pin = None; reportes_publicos.clear()
        st.success("Reporte enviado a revisión humana. Los puntos se sumarán al saldo solo si la evidencia es aprobada.")
        st.caption(f"Orientación visual ({ia['metodo']}): confianza {ia['confianza']:.0%}. {ia['detalle']}")
        
        # ACTUALIZACIÓN EN TIEMPO REAL: Pausamos 2.5 segs para que el usuario lea, y recargamos para actualizar puntos
        time.sleep(2.5)
        st.rerun()
        
    except Exception as ex: 
        st.error(f"Error interno al guardar: Es posible que la foto esté duplicada o falten permisos. Detalles: {ex}")

# ---------- BARRA LATERAL Y AUTENTICACIÓN ----------
def entrar(sb, email, password, error_container=None):
    try:
        r = sb.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = r.user; sb.postgrest.auth(r.session.access_token)
        st.session_state.admin = bool(
            sb.table("admins").select("user_id").eq("user_id", r.user.id).limit(1).execute().data
        )
        pr = sb.table("perfiles").select("*").eq("user_id", r.user.id).execute().data
        st.session_state.datos_perfil = pr[0] if pr else {}
        st.rerun()
    except Exception:
        destino = st.sidebar if error_container is None else error_container
        destino.error("Credenciales incorrectas o correo sin confirmar.")

@st.dialog("Crear cuenta ciudadana", width="small")
def dialogo_registro():
    sb = sb_client()
    with st.form("registro"):
        st.caption("Completa tus datos para participar en la comunidad.")
        n = st.text_input("Nombres", max_chars=80)
        a = st.text_input("Apellidos", max_chars=80)
        td = st.selectbox("Tipo de documento", list(TIPOS_DOC))
        nd = st.text_input("Número de documento", max_chars=30)
        tl = st.text_input("Celular", max_chars=30)
        z = st.selectbox("Zona", list(ZONAS))
        e = st.text_input("Correo electrónico", max_chars=254)
        p1 = st.text_input("Contraseña", type="password", help="Usa al menos 8 caracteres.")
        p2 = st.text_input("Confirma la contraseña", type="password")
        st.caption("Tu documento y celular se usan para gestionar tu cuenta. No los incluyas en publicaciones.")
        if st.form_submit_button("Crear cuenta", type="primary", width="stretch"):
            correo = e.strip().lower()
            if not all([n.strip(), a.strip(), nd.strip(), tl.strip(), correo]):
                st.error("Completa todos los campos obligatorios.")
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
                st.error("Ingresa un correo electrónico válido.")
            elif p1 != p2 or len(p1) < 8:
                st.error("Las contraseñas no coinciden o tienen menos de 8 caracteres.")
            else:
                try:
                    r = sb.auth.sign_up({
                        "email": correo,
                        "password": p1,
                        "options": {
                            "data": {
                                "nombre": n.strip().title(),
                                "apellido": a.strip().title(),
                                "telefono": tl.strip(),
                                "tipo_doc": td,
                                "num_doc": nd.strip(),
                                "zona": z,
                            }
                        },
                    })
                    if r.session:
                        st.session_state.pop("confirmacion_pendiente", None)
                        entrar(sb, correo, p1)
                    else:
                        st.session_state.confirmacion_pendiente = correo
                        st.success("Recibimos tu solicitud de registro.")
                        st.info(
                            "Revisa tu correo y la carpeta de spam para confirmar la cuenta. "
                            "La entrega depende de la configuración de correo SMTP del proyecto."
                        )
                except Exception as ex:
                    mensaje = str(getattr(ex, "message", None) or ex)
                    mensaje_lower = mensaje.lower()
                    if "rate" in mensaje_lower or "limit" in mensaje_lower:
                        st.error("Se alcanzó el límite de correos de autenticación. Espera antes de volver a intentarlo.")
                    elif "smtp" in mensaje_lower or "email provider" in mensaje_lower:
                        st.error(
                            "Supabase no pudo enviar el correo. Revisa la configuración SMTP y el proveedor Email en Authentication."
                        )
                    else:
                        st.error(f"No se pudo crear la cuenta: {mensaje}")

    correo_pendiente = st.session_state.get("confirmacion_pendiente")
    if correo_pendiente:
        st.caption(f"Correo pendiente de confirmación: {correo_pendiente}")
        if st.button(
            "Reenviar confirmación",
            icon=":material/forward_to_inbox:",
            width="stretch",
            key="reenviar_confirmacion",
        ):
            try:
                sb.auth.resend({"type": "signup", "email": correo_pendiente})
                st.success(
                    "Supabase aceptó la solicitud de reenvío. La entrega puede tardar unos minutos; revisa también spam."
                )
            except Exception as ex:
                mensaje = str(getattr(ex, "message", None) or ex)
                mensaje_lower = mensaje.lower()
                if "rate" in mensaje_lower or "limit" in mensaje_lower:
                    st.error("Se alcanzó el límite de reenvíos. Espera antes de volver a intentarlo.")
                elif "smtp" in mensaje_lower or "email provider" in mensaje_lower:
                    st.error(
                        "Supabase no pudo enviar el correo. Revisa la configuración SMTP y el proveedor Email en Authentication."
                    )
                else:
                    st.error(f"No fue posible reenviar la confirmación: {mensaje}")

@st.dialog("Inicia sesión", width="small")
def dialogo_inicio_sesion():
    sb = sb_client()
    with st.form("inicio_sesion_principal"):
        email = st.text_input("Correo electrónico", max_chars=254)
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Ingresar", type="primary", width="stretch"):
            entrar(sb, email.strip().lower(), password, error_container=st)

def generar_alertas(info, aire, aq):
    out, lm = [], info["LST (°C)"].mean()
    for z, r in info.iterrows():
        n, l = r["NDVI"], r["LST (°C)"]
        if pd.notna(n) and n < 0.30: out.append((3 if n < 0.2 else 2, "Baja cobertura vegetal", z, f"NDVI {n:.2f}: señal satelital de baja cobertura vegetal.", "Verificar el terreno en campo; el NDVI no confirma que el lugar sea apto para sembrar."))
        if pd.notna(l) and l - lm >= 1.5: out.append((3 if l - lm >= 3 else 2, "🔥 Isla de calor", z, f"Superficie {l:.1f} °C ({l - lm:+.1f} °C vs. ciudad).", "Más sombra en calles, paraderos y escuelas; techos y fachadas verdes o reflectantes."))
    if aire is not None:
        for z, r in aire.iterrows():
            if r["Sensación (°C)"] >= 38: out.append((2, "🥵 Calor", z, f"Sensación térmica {r['Sensación (°C)']:.0f} °C.", "Evitar actividad al sol, hidratarse y habilitar sombra y agua."))
            if r["UV"] >= 8: out.append((2, "☀️ UV muy alto", z, f"Índice UV {r['UV']:.0f}.", "Protección solar; evitar exposición entre 10 am y 4 pm."))
    if aq is not None:
        for z, r in aq.iterrows():
            if pd.notna(r["AQI"]) and r["AQI"] > 100: out.append((3, "🫁 Calidad del aire", z, f"AQI {r['AQI']:.0f}.", "Los grupos sensibles deben limitar la actividad al aire libre."))
    return sorted(out, key=lambda x: -x[0])

def sidebar():
    st.sidebar.markdown("### :material/park: SombraBAQ")
    st.sidebar.caption("Observatorio ambiental")
    st.sidebar.toggle(
        "Modo oscuro",
        key="modo_oscuro",
        persist_state="session",
    )
    with st.sidebar.container(border=True):
        st.markdown("**Filtros del mapa**")
        zona_foco = st.selectbox("Zona", ["Todas", *ZONAS], key="map_zone_focus")
        dias = st.slider("Ventana satelital", 20, 120, 60, 10, help="Periodo usado para combinar imágenes satelitales.")
    _, supabase_key = cfg()
    if not supabase_key:
        st.sidebar.warning(
            "La autenticación y las funciones de comunidad requieren configurar Supabase en los secretos del despliegue.",
            title="Supabase pendiente de configuración",
        )
        return dias, zona_foco

    sb = sb_client()
    
    if st.session_state.get("user"):
        pf = st.session_state.get("datos_perfil", {})
        with st.sidebar.container(border=True):
            st.markdown(f"**{pf.get('nombre') or 'Ciudadano'}**")
            st.caption(("Moderador" if st.session_state.admin else "Cuenta ciudadana"))
        if st.sidebar.button("Cerrar sesión", width="stretch"): 
            sb.auth.sign_out(); [st.session_state.pop(k, None) for k in ("user", "admin", "datos_perfil", "pin", "ia")]; st.rerun()
    else:
        with st.sidebar.container(border=True):
            st.markdown("**Iniciar sesión**")
            with st.form("login"):
                e, p = st.text_input("Correo"), st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar", type="primary", width="stretch"): entrar(sb, e, p)
            if st.button("Crear cuenta ciudadana", icon=":material/person_add:", width="stretch"): dialogo_registro()
    return dias, zona_foco

dias, zona_foco = sidebar()
user, admin = st.session_state.get("user"), st.session_state.get("admin")

# ---------- ESTRUCTURA PRINCIPAL DE PESTAÑAS ----------
st.markdown(
    "<div class='hero'><span class='hero-kicker'>OBSERVATORIO AMBIENTAL · BARRANQUILLA</span>"
    "<h1>SombraBAQ</h1>"
    "<p>Explora el calor y la vegetación de la ciudad, comparte acciones ambientales "
    "y encuentra información para decidir con mejores datos.</p>"
    "<div class='hero-tags'>"
    "<span class='hero-tag'><span>●</span> Datos satelitales</span>"
    "<span class='hero-tag'><span>●</span> Clima urbano</span>"
    "<span class='hero-tag'><span>●</span> Acción ciudadana</span>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

if not cfg()[1]:
    st.warning(
        "El panel climático sigue disponible, pero inicio de sesión, reportes ciudadanos, comunidad y recompensas "
        "están pausados hasta configurar Supabase.",
        title="Configura Supabase para habilitar todas las funciones",
    )
    with st.expander("Cómo configurar la conexión"):
        st.markdown("Abre **Manage app → Settings → Secrets** y añade las credenciales de tu proyecto Supabase:")
        st.code(
            '[supabase]\nurl = "https://<project-ref>.supabase.co"\nanon_key = "<publishable-or-anon-key>"',
            language="toml",
        )
        st.caption("Copia los valores desde Supabase → Project Settings → API. No publiques ni compartas claves secretas.")

if not user and cfg()[1]:
    with st.container(horizontal=True, vertical_alignment="center", wrap=True):
        st.markdown("**Participa en las acciones ambientales de Barranquilla.**")
        if st.button(
            "Crear cuenta",
            key="crear_cuenta_principal",
            icon=":material/person_add:",
            type="primary",
        ):
            dialogo_registro()
        if st.button(
            "Iniciar sesión",
            key="abrir_inicio_sesion",
            icon=":material/login:",
        ):
            dialogo_inicio_sesion()

@st.fragment(run_every=60)
def estado_en_vivo():
    try:
        climate = clima_vivo()
        reportes = reportes_publicos()
        temp = climate["Temp (°C)"].mean()
        uv = climate["UV"].max()
        count = len(reportes)
        signature = f"{count}:{round(temp, 1)}:{round(float(uv), 1)}"
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temperatura media", f"{temp:.1f} °C", "Open-Meteo", icon=":material/thermostat:", border=True, height="stretch",
                      chart_data=climate["Temp (°C)"].tolist(), chart_type="area")
            c2.metric("UV máximo", f"{uv:.0f}", "Protección solar", icon=":material/wb_sunny:", border=True, height="stretch",
                      chart_data=climate["UV"].tolist(), chart_type="line")
            c3.metric("Reportes validados", count, icon=":material/verified:", border=True, height="stretch",
                      chart_data=[count], chart_type="bar")
            c4.metric("Estado del servicio", "Operativo", icon=":material/cloud_done:", border=True, height="stretch",
                      chart_data=[1, 1, 1, 1, 1], chart_type="bar")
        st.caption(f"Última actualización automática: {dt.datetime.now().strftime('%H:%M:%S')} · Se renueva cada 60 segundos")
        if st.session_state.get("live_signature") and st.session_state.live_signature != signature:
            st.toast("Se actualizó la información ambiental o comunitaria.", icon=":material/notifications:")
        st.session_state.live_signature = signature
    except Exception:
        st.warning("La fuente ambiental está temporalmente fuera de línea. El resto de módulos sigue disponible.")

estado_en_vivo()

nombres_tabs = [
    ":material/map: Mapa inteligente",
    ":material/camera_alt: Reportar",
    ":material/groups: Comunidad",
    ":material/redeem: Recompensas",
    ":material/school: Aprende",
    ":material/database: Datos abiertos",
] + ([":material/person: Mi perfil"] if user else []) + ([":material/admin_panel_settings: Moderación"] if admin else [])
tabs = dict(zip(nombres_tabs, st.tabs(
    nombres_tabs,
    key="sombrabaq_main_tabs",
    bind="query-params",
)))

# --- PESTAÑA 1: MAPA Y SUGERENCIAS DE SIEMBRA ---
with tabs[":material/map: Mapa inteligente"]:
    satellite_error = None
    try:
        df, tiles, meta = satelite(dias)
        if df is None:
            satellite_error = gee_error_message(
                meta or "Earth Engine no devolvió detalles del error.",
                info,
            )
            tiles = tiles or {}
            meta = meta if isinstance(meta, dict) else {}
    except Exception as error:
        satellite_error = f"{type(error).__name__}: {gee_error_message(error, info)}"
        df, tiles, meta = None, {}, {}

    # 🚨 NOVEDADES Y SUGERENCIAS DE SIEMBRA (La función que pediste restaurar)
    if df is not None and not df.empty:
        peor_zona = df.loc[df['LST (°C)'].idxmax()]
        st.warning(
            f"La zona **{peor_zona['Zona']}** presenta la temperatura superficial más alta "
            f"({peor_zona['LST (°C)']:.1f} °C). Prioriza una revisión técnica antes de definir "
            "acciones de arborización en este sector.",
            icon=":material/priority_high:",
        )

    @st.fragment(run_every=600)
    def panel_vivo():
        try:
            c = clima_vivo()
            a, b, d, e = st.columns(4)
            a.metric("Temperatura media", f"{c['Temp (°C)'].mean():.1f} °C", icon=":material/thermostat:", border=True)
            b.metric("Sensación máxima", f"{c['Sensación (°C)'].max():.1f} °C", icon=":material/device_thermostat:", border=True)
            d.metric("Humedad media", f"{c['Humedad (%)'].mean():.0f} %", icon=":material/humidity_mid:", border=True)
            e.metric("UV máximo", f"{c['UV'].max():.1f}", icon=":material/wb_sunny:", border=True)
            st.caption(f"Modelo Open-Meteo · Actualizado a las {c['Hora'].iloc[0].replace('T', ' ')}")
        except Exception: pass
    panel_vivo()

    if df is not None and not df.empty:
        try: aire = clima_vivo().set_index("Zona")
        except: aire = None
        try:
            aq_data = calidad_aire()
            aq = aq_data.set_index("Zona") if aq_data is not None else None
        except Exception:
            aq = None
        
        info = df.set_index("Zona")
        o1, o2, o3 = st.columns([3.2, 1.3, 1])
        capa = o1.segmented_control("Capa principal", ["AIRE", "AQI", "LST", "NDVI"], default="AIRE",
                                    format_func=lambda x: {"AIRE": "Aire", "AQI": "Calidad del aire", "LST": "Superficie", "NDVI": "Vegetación"}[x]) or "AIRE"
        ver_ico = o2.toggle("Ver indicadores", True)
        ver_rep = o3.toggle("Ver reportes", True)
        
        zd = {}
        for z, (lat, lng) in ZONAS.items():
            a = aire.loc[z] if aire is not None else None
            q = aq.loc[z] if aq is not None else None
            n, l = info.loc[z, "NDVI"], info.loc[z, "LST (°C)"]
            if capa == "AIRE" and a is not None: txt, col, peso = f"{a['Temp (°C)']:.1f}°C", rampa(a['Temp (°C)'], 28, 36), a['Temp (°C)']
            elif capa == "AQI" and q is not None and pd.notna(q["AQI"]): txt, col, peso = f"AQI {q['AQI']:.0f}", rampa(q["AQI"], 0, 150), q["AQI"]
            elif capa == "LST" and pd.notna(l): txt, col, peso = f"{l:.0f}°C", rampa(l, 30, 44), l
            elif capa == "NDVI" and pd.notna(n): txt, col, peso = f"{n:.2f}", rampa(0.6 - n, 0, 0.6), -n
            else: txt, col, peso = "s/d", "#9ca3af", -999
            
            det = "".join([
                f"🌡️ Aire: {a['Temp (°C)']:.1f}°C (Sensación {a['Sensación (°C)']:.1f}°C)<br>" if a is not None else "",
                f"🫁 Calidad Aire (AQI): {q['AQI']:.0f}<br>" if q is not None and pd.notna(q["AQI"]) else "",
                f"🔥 Superficie (LST): {l:.1f}°C<br>" if pd.notna(l) else "", 
                f"🌿 Vegetación (NDVI): {n:.2f}" if pd.notna(n) else ""
            ])
            zd[z] = (lat, lng, txt, col, peso, det)
        zonas_mapa = zd if zona_foco == "Todas" else {zona_foco: zd[zona_foco]}
        peor = max(zonas_mapa, key=lambda k: zonas_mapa[k][4]) if zonas_mapa else None

        mapa_col, panel_col = st.columns([3, 1.1])
        with mapa_col:
            from folium.plugins import Fullscreen
            centro_mapa = ZONAS.get(zona_foco, (10.97, -74.80))
            m = folium.Map(location=centro_mapa, zoom_start=14 if zona_foco != "Todas" else 12, min_zoom=11, max_zoom=18, tiles=None, prefer_canvas=True, max_bounds=True)
            m.get_root().html.add_child(folium.Element("<style>@keyframes pulso{0%{box-shadow:0 0 0 0 rgba(239,68,68,.75)}100%{box-shadow:0 0 0 24px rgba(239,68,68,0)}}.pulso{animation:pulso 1.6s infinite}</style>"))
            for i_, (nb, (ub, nz)) in enumerate(BASES.items()): folium.TileLayer(ub, attr="Esri/OSM", name=nb, show=(i_ == 0), max_native_zoom=nz, max_zoom=19).add_to(m)
            if capa in tiles: folium.TileLayer(tiles[capa], attr="Google Earth Engine", name=capa, opacity=0.8, overlay=True).add_to(m)
            
            if ver_ico and capa == "NDVI":
                for la, lo, v in meta.get("arboles", []):
                    if zona_foco != "Todas" and zona_cercana(la, lo) != zona_foco: continue
                    folium.CircleMarker(
                        [la, lo],
                        radius=4,
                        color="#f0fdf4",
                        weight=1.5,
                        fill=True,
                        fill_color="#166534",
                        fill_opacity=0.95,
                        tooltip=f"Muestra satelital con NDVI alto ({v:.2f}); no confirma un árbol individual",
                    ).add_to(m)
            if ver_ico and capa in ("NDVI", "LST"):
                for i_p, (la, lo, v, tl) in enumerate(meta.get("plantar", []), 1):
                    if zona_foco != "Todas" and zona_cercana(la, lo) != zona_foco: continue
                    folium.Marker([la, lo], tooltip=f"Punto de revisión #{i_p}: NDVI {v:.2f}, superficie {tl:.0f} °C", icon=folium.DivIcon(icon_size=(22, 22), icon_anchor=(11, 11), html=f'<div class="pulso" style="width:22px;height:22px;border-radius:50%;background:#facc15;border:2px solid #fff;color:#1a1a1a;font:700 11px system-ui;text-align:center;line-height:18px">{i_p}</div>')).add_to(m)
            if ver_ico and capa == "LST":
                for la, lo, v in meta.get("calientes", []):
                    if zona_foco != "Todas" and zona_cercana(la, lo) != zona_foco: continue
                    folium.Marker([la, lo], tooltip=f"Muestra de superficie: {v:.1f} °C", icon=folium.DivIcon(icon_size=(14, 14), html='<div class="pulso" style="width:12px;height:12px;border-radius:50%;background:#ef4444;border:2px solid #fff"></div>')).add_to(m)
            
            for z, (lat, lng, txt, col, peso, det) in zonas_mapa.items():
                folium.Circle([lat, lng], RADIO_M, color=col, weight=2, fill=True, fill_color=col, fill_opacity=0.3 if capa in ("AIRE", "AQI") else 0.08).add_to(m)
                cls = "pulso" if z == peor else ""
                badge = f'<div class="{cls}" style="background:{col};color:#0b1a14;font:700 15px Inter,system-ui;padding:4px 12px;border-radius:14px;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.5);text-align:center;white-space:nowrap">{txt}<div style="font:600 9px system-ui">{z}</div></div>'
                folium.Marker([lat, lng], tooltip=z, icon=folium.DivIcon(icon_size=(110, 44), icon_anchor=(55, 22), html=badge), popup=folium.Popup(f"<div style='font:13px system-ui;min-width:180px'><b>{z}</b><hr style='margin:5px 0'>{det}</div>")).add_to(m)
            
            if ver_rep:
                try:
                    for _, r in reportes_publicos().iterrows():
                        if zona_foco != "Todas" and r["zona"] != zona_foco: continue
                        folium.CircleMarker([r["lat"], r["lng"]], radius=6.5, color="#fff", weight=1.5, fill=True, fill_color="#ef4444" if r["tipo"] == "residuos" else "#22c55e", fill_opacity=1, tooltip=TIPOS.get(r["tipo"])).add_to(m)
                except: pass
                
            folium.LayerControl(collapsed=True).add_to(m); Fullscreen().add_to(m)
            st_folium(m, height=600, width=None, returned_objects=[])
            leyenda_mapa = {
                "AIRE": ("Círculos por zona · Temperatura del aire (°C)", "Menor temperatura", "Mayor temperatura", "Open-Meteo · condición actual estimada; no es una medición en sitio."),
                "AQI": ("Círculos por zona · Calidad del aire (US AQI)", "Mejor calidad", "Peor calidad", "Open-Meteo · estimación de modelo; no equivale a una estación local."),
                "LST": ("Círculos por zona · Temperatura de superficie (°C)", "Menor temperatura", "Mayor temperatura", f"Resumen por zona de Landsat 8/9, últimos {dias} días, escala de análisis de 30 m. El ráster usa una paleta independiente."),
                "NDVI": ("Círculos por zona · Índice de vegetación (NDVI)", "NDVI alto · más vegetación", "NDVI bajo · menos vegetación", f"Resumen por zona de Sentinel-2, últimos {dias} días. El ráster usa tonos propios: marrón para NDVI bajo y verde para NDVI alto."),
            }
            titulo_leyenda, extremo_izq, extremo_der, nota_leyenda = leyenda_mapa[capa]
            st.markdown(f"**{titulo_leyenda}**")
            st.markdown('<div class="leyenda"></div>', unsafe_allow_html=True)
            leyenda_izq, leyenda_der = st.columns(2)
            leyenda_izq.caption(extremo_izq)
            leyenda_der.caption(extremo_der, text_alignment="right")
            st.caption(nota_leyenda)
            if capa in ("LST", "NDVI"):
                cuenta_escenas = meta.get("escenas_landsat" if capa == "LST" else "escenas_s2", 0)
                st.caption(f"Escenas disponibles en el periodo: {cuenta_escenas} · Vista: {zona_foco.lower() if zona_foco != 'Todas' else 'toda la ciudad'}.")
            else:
                st.caption(f"Vista: {zona_foco.lower() if zona_foco != 'Todas' else 'toda la ciudad'}.")
            if capa == "NDVI" and ver_ico:
                st.caption("Puntos verdes discretos: muestras con señal de vegetación alta; no son un inventario de árboles.")

        with panel_col:
            with st.container(border=True):
                st.markdown("**Comparativa local**")
                if zona_foco == "Todas":
                    z = st.selectbox("Zona a inspeccionar", list(ZONAS), key="map_comparison_zone")
                else:
                    z = zona_foco
                    st.caption(f"Zona enfocada: {z}")
                if aire is not None:
                    st.metric("Temperatura del Aire", f"{aire.loc[z,'Temp (°C)']:.1f} °C", f"{aire.loc[z,'Temp (°C)']-aire['Temp (°C)'].mean():+.1f} °C vs media ciudad", delta_color="inverse")
                if pd.notna(info.loc[z, "LST (°C)"]): st.metric("Superficie LST", f"{info.loc[z,'LST (°C)']:.1f} °C", f"{info.loc[z,'LST (°C)']-info['LST (°C)'].mean():+.1f} °C vs ciudad", delta_color="inverse")
                if pd.notna(info.loc[z, "NDVI"]): st.metric("Índice Vegetal (NDVI)", f"{info.loc[z,'NDVI']:.2f}")
            
            st.markdown("**Top Temperatura Superficial**")
            t = df.copy(); t["LST (°C)"] = t["LST (°C)"].round(1)
            st.bar_chart(t.set_index("Zona")["LST (°C)"].sort_values(ascending=False), color="#ef4444", height=200)

        al = generar_alertas(info, aire, aq)
        if zona_foco != "Todas":
            al = [alerta for alerta in al if alerta[2] == zona_foco]
        st.markdown("### Alertas ambientales")
        if not al: st.success("Sin alertas activas con los datos actuales.")
        for nv, tit, z, dato, accion in al[:8]:
            col = {3: "#ef4444", 2: "#f59e0b"}[nv]
            st.markdown(f"<div style='border-left:6px solid {col};background:rgba(127,127,127,.08);padding:.7rem 1rem;border-radius:10px;margin:.4rem 0'><b>{tit} · {z}</b><br>{dato}<br><i>{accion}</i></div>", unsafe_allow_html=True)
        pl = [
            punto for punto in meta.get("plantar", [])
            if zona_foco == "Todas" or zona_cercana(punto[0], punto[1]) == zona_foco
        ]
        if pl:
            dfp = pd.DataFrame([{"Punto": i + 1, "Zona de revisión": zona_cercana(la, lo), "NDVI": round(v, 2), "Superficie (°C)": round(tl, 1), "Mapa": f"https://www.google.com/maps?q={la:.5f},{lo:.5f}"} for i, (la, lo, v, tl) in enumerate(pl)])
            st.markdown("**Puntos candidatos para revisión en campo**")
            st.dataframe(dfp, hide_index=True, width="stretch", column_config={"Mapa": st.column_config.LinkColumn("Ubicación", display_text="Abrir en Google Maps")})
            st.caption("Se generan a partir de muestras satelitales a escala de 120 m con NDVI bajo y temperatura superficial alta. Pueden corresponder a suelo desnudo, techos o vías; no indican por sí solas que el sitio sea apto para sembrar. Verifica en campo y coordina con la autoridad ambiental.")
            st.download_button("Descargar puntos de revisión (CSV)", dfp.to_csv(index=False), "puntos_revision_sombrabaq.csv", "text/csv", icon=":material/download:")
    else:
        st.info(
            "La capa satelital no está disponible por ahora. Se muestra el mapa de Barranquilla "
            "con datos meteorológicos como alternativa.",
            icon=":material/satellite_alt:",
        )
        if satellite_error:
            st.warning("La inicialización o consulta satelital no se completó.")
            with st.expander("Detalle del error satelital"):
                st.code(satellite_error)
        with st.expander("¿Por qué no se ve la capa satelital?"):
            st.markdown(
                "Las imágenes de vegetación y temperatura superficial requieren configurar "
                "Google Earth Engine y que el proyecto y la cuenta de servicio estén autorizados. "
                "Comprueba la autorización del proyecto y las credenciales de Google Earth Engine. "
                "Mientras tanto, el mapa y las mediciones meteorológicas siguen disponibles."
            )

        mapa_col, panel_col = st.columns([3, 1.1])
        try:
            aire_respaldo = clima_vivo().set_index("Zona")
        except requests.RequestException:
            aire_respaldo = None

        with mapa_col:
            from folium.plugins import Fullscreen

            mapa_respaldo = folium.Map(
                location=[10.97, -74.80],
                zoom_start=12,
                min_zoom=11,
                max_zoom=18,
                tiles="OpenStreetMap",
                max_bounds=True,
                prefer_canvas=True,
            )
            for zona, (lat, lng) in ZONAS.items():
                medicion = aire_respaldo.loc[zona] if aire_respaldo is not None else None
                if medicion is not None:
                    temperatura = float(medicion["Temp (°C)"])
                    color = rampa(temperatura, 28, 36)
                    detalle = (
                        f"Temperatura: {temperatura:.1f} °C<br>"
                        f"Sensación térmica: {medicion['Sensación (°C)']:.1f} °C<br>"
                        f"Humedad: {medicion['Humedad (%)']:.0f}%<br>"
                        f"Índice UV: {medicion['UV']:.1f}"
                    )
                    etiqueta = f"{temperatura:.1f} °C"
                else:
                    color = "#64748b"
                    detalle = "Mediciones meteorológicas temporalmente no disponibles."
                    etiqueta = "Sin datos"

                folium.Circle(
                    [lat, lng],
                    radius=RADIO_M,
                    color=color,
                    weight=2,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.16,
                ).add_to(mapa_respaldo)
                folium.CircleMarker(
                    [lat, lng],
                    radius=9,
                    color="white",
                    weight=2,
                    fill=True,
                    fill_color=color,
                    fill_opacity=1,
                    tooltip=f"{zona} · {etiqueta}",
                    popup=folium.Popup(f"<b>{zona}</b><br>{detalle}", max_width=260),
                ).add_to(mapa_respaldo)

            Fullscreen().add_to(mapa_respaldo)
            st_folium(mapa_respaldo, height=600, width=None, returned_objects=[])
            st.caption(
                "Mapa base de OpenStreetMap · Los círculos muestran temperatura del aire por zona; "
                "no representan temperatura superficial satelital."
            )

        with panel_col:
            with st.container(border=True):
                st.markdown("**Condiciones por zona**")
                zona_respaldo = st.selectbox(
                    "Zona a inspeccionar",
                    list(ZONAS),
                    key="zona_respaldo",
                )
                if aire_respaldo is not None:
                    medicion = aire_respaldo.loc[zona_respaldo]
                    st.metric(
                        "Temperatura del aire",
                        f"{medicion['Temp (°C)']:.1f} °C",
                        icon=":material/thermostat:",
                        border=True,
                    )
                    st.metric(
                        "Sensación térmica",
                        f"{medicion['Sensación (°C)']:.1f} °C",
                        icon=":material/device_thermostat:",
                        border=True,
                    )
                    st.metric(
                        "Humedad relativa",
                        f"{medicion['Humedad (%)']:.0f} %",
                        icon=":material/humidity_mid:",
                        border=True,
                    )
                    st.caption(f"Actualizado: {medicion['Hora'].replace('T', ' ')}")
                else:
                    st.warning("No fue posible consultar el servicio meteorológico.")

# --- PESTAÑA 2: REPORTAR ---
with tabs[":material/camera_alt: Reportar"]:
    if not user:
        st.info(
            "Inicia sesión o crea una cuenta desde la barra lateral para registrar una acción ambiental.",
            icon=":material/person:",
        )
    else:
        st.subheader("Comparte una acción ambiental", icon=":material/add_a_photo:")
        st.caption("Marca dónde ocurrió, agrega una foto y envía el reporte para revisión.")
        st.warning(
            "Por privacidad, evita incluir rostros, placas, documentos o ubicaciones privadas en la evidencia.",
            icon=":material/privacy_tip:",
        )

        with st.container(border=True):
            st.markdown("#### 1. Marca la ubicación")
            st.caption("Haz clic en el mapa donde realizaste la acción.")
            m2 = folium.Map(location=[10.97, -74.80], zoom_start=12)
            pin = st.session_state.get("pin")
            if pin:
                folium.Marker(pin, icon=folium.Icon(color="green", icon="leaf")).add_to(m2)
            out = st_folium(
                m2,
                height=390,
                width=None,
                returned_objects=["last_clicked"],
                key="report_location_map",
            )
            if out and out.get("last_clicked"):
                pin = st.session_state.pin = [
                    out["last_clicked"]["lat"],
                    out["last_clicked"]["lng"],
                ]
            if pin:
                st.badge("Ubicación seleccionada", icon=":material/location_on:", color="green")
                st.caption(f"Coordenadas: {pin[0]:.5f}, {pin[1]:.5f}")
                if st.button("Quitar ubicación", key="clear_report_location", icon=":material/location_off:"):
                    st.session_state.pin = None
                    st.rerun()
            else:
                st.info("Selecciona un punto en el mapa para continuar.", icon=":material/map:")

        with st.container(border=True):
            st.markdown("#### 2. Describe y agrega evidencia")
            c1, c2 = st.columns(2)
            tipo = c1.selectbox(
                "Tipo de acción",
                list(TIPOS),
                format_func=lambda k: f"{TIPOS[k]} · {PUNTOS[k]} puntos",
            )
            nota = c2.text_input(
                "Nota para la comunidad (opcional)",
                max_chars=150,
                help="Describe brevemente la acción, sin incluir datos personales.",
            )
            foto = st.camera_input(
                "Toma una foto",
                help="También puedes seleccionar una imagen desde tu dispositivo.",
                key="report_camera",
            )
            if foto is None:
                foto = st.file_uploader(
                    "O selecciona una imagen",
                    type=["jpg", "jpeg", "png"],
                    key="report_upload",
                )
            if foto is not None:
                st.image(
                    foto,
                    caption="Vista previa de la evidencia",
                    alt="Vista previa de la foto adjunta al reporte",
                )

            if st.button(
                "Enviar reporte",
                icon=":material/send:",
                type="primary",
                disabled=foto is None or not pin,
            ):
                datos = foto.getvalue()
                datos, error_evidencia = validar_evidencia(datos)
                if error_evidencia:
                    st.error(error_evidencia)
                else:
                    with st.spinner("Analizando la evidencia y guardando el reporte…"):
                        ia = analizar_foto(datos, tipo)
                        st.session_state.ia = {
                            **ia,
                            "datos": datos,
                            "tipo": tipo,
                            "pin": pin,
                            "nota": nota,
                            "mime": foto.type or "image/jpeg",
                        }
                        _publicar(
                            st.session_state.sb,
                            user,
                            st.session_state.ia,
                            zona_cercana,
                            reportes_publicos,
                        )
        
        if st.session_state.get("ia"):
            ia = st.session_state.ia
            st.markdown(f"**Orientación visual:** {ia['metodo']} · confianza `{ia['confianza']:.0%}`. *{ia['detalle']}*")
            st.caption("El modelo no verifica fecha, ubicación, autoría ni que la siembra haya ocurrido. Ningún análisis automático aprueba reportes ni otorga puntos.")

# --- PESTAÑA 3: COMUNIDAD ---
with tabs[":material/groups: Comunidad"]:
    st.markdown("### 🤝 Muro de Impacto Ambiental SombraBAQ")
    c1, c2 = st.columns([2, 1])
    with c1:
        sub1, sub2 = st.tabs(["📰 Novedades ambientales", "🌱 Aportes verificados"])
        with sub1:
            if user:
                with st.expander("✍️ Publicar una novedad"):
                    with st.form("nuevo_post", clear_on_submit=True):
                        tt = st.text_input("Título *", max_chars=120)
                        tx = st.text_area("¿Qué está pasando? *", max_chars=800)
                        en = st.text_input("Enlace a la fuente (opcional)", placeholder="https://")
                        im = st.file_uploader("Imagen (opcional)", type=["jpg", "jpeg", "png"])
                        if st.form_submit_button("Publicar", type="primary"):
                            if not (tt.strip() and tx.strip()): st.error("Escribe un título y un texto.")
                            elif en.strip() and not en.strip().startswith(("http://", "https://")): st.error("El enlace debe empezar por http:// o https://")
                            else:
                                try:
                                    ruta = None
                                    if im is not None:
                                        ruta = f"{user.id}/post_{uuid.uuid4().hex}.jpg"; st.session_state.sb.storage.from_("evidencias").upload(ruta, im.getvalue(), {"content-type": im.type or "image/jpeg"})
                                    pf = st.session_state.get("datos_perfil") or {}
                                    autor = f"{pf['nombre']} {pf['apellido'][:1]}." if pf.get("nombre") and pf.get("apellido") else (pf.get("nombre") or "Ciudadano")
                                    st.session_state.sb.table("publicaciones").insert({"user_id": user.id, "autor": autor, "titulo": tt.strip(), "texto": tx.strip(), "enlace": en.strip() or None, "imagen_path": ruta}).execute()
                                    st.success("¡Publicado!"); time.sleep(1); st.rerun()
                                except Exception as ex: st.error(f"No se pudo publicar: {ex}")
            else: st.info("Inicia sesión para publicar una novedad.")
            try: posts = pub().table("publicaciones").select("*").order("created_at", desc=True).limit(15).execute().data
            except Exception: posts = []
            if not posts: st.info("Aún no hay novedades. ¡Publica la primera!")
            for p in posts:
                with st.container(border=True):
                    st.markdown(f"#### {p['titulo']}"); st.caption(f"{p['autor']} · {p['created_at'][:10]}"); st.write(p["texto"])
                    if p.get("enlace"): st.link_button("🔗 Ver fuente", p["enlace"])
                    if p.get("imagen_path"):
                        try: st.image(st.session_state.sb.storage.from_("evidencias").create_signed_url(p["imagen_path"], 600)["signedURL"], width=380)
                        except Exception: pass
                    if admin and st.button("🗑️ Eliminar", key=f"dp{p['id']}"): st.session_state.sb.table("publicaciones").delete().eq("id", p["id"]).execute(); st.rerun()
        with sub2:
            try: feed = reportes_publicos()
            except Exception: feed = pd.DataFrame()
            if feed.empty: st.info("Aún no hay aportes verificados.")
            for _, post in feed.head(10).iterrows():
                with st.container(border=True):
                    st.markdown(f"**🌱 {TIPOS.get(post['tipo'])} · {post['zona']}**"); st.caption(f"{str(post['created_at'])[:10]} · 🏅 {post['puntos']} pts")
                    st.write(post["nota"] or "Acción climática validada a favor de Barranquilla.")
                    try: st.image(st.session_state.sb.storage.from_("evidencias").create_signed_url(post["foto_path"], 600)["signedURL"], width=320)
                    except Exception: pass
    with c2:
        st.subheader("Próximos eventos")
        st.caption("Inscríbete y registra tu llegada con el equipo organizador. Los puntos se acreditan solo al confirmar tu asistencia.")
        with st.expander("Proponer y publicar un evento", expanded=not user):
            st.caption("Las publicaciones son públicas e inmediatas. Cada cuenta autenticada puede publicar hasta 3 eventos en 24 horas; el organizador no puede verificar su propia asistencia.")
            if not user:
                st.info("Inicia sesión para proponer un evento.")
            else:
                with st.form("crear_evento_comunitario"):
                    titulo_propuesta = st.text_input("Título del evento", max_chars=120)
                    tema_columnas = st.columns(2)
                    tema_propuesta = tema_columnas[0].text_input("Tema", max_chars=100)
                    dirigido_propuesta = tema_columnas[1].text_input("¿Para quién está dirigido?", max_chars=120)
                    descripcion_propuesta = st.text_area(
                        "¿De qué se trata? Incluye qué harán las personas",
                        max_chars=1200,
                    )
                    lugar_propuesta = st.text_input("Lugar real de encuentro", max_chars=200)
                    fecha_columnas_propuesta = st.columns(2)
                    fecha_propuesta = fecha_columnas_propuesta[0].date_input(
                        "Fecha",
                        value=dt.date.today() + dt.timedelta(days=7),
                        min_value=dt.date.today(),
                        key="community_event_date",
                    )
                    hora_propuesta = fecha_columnas_propuesta[1].time_input(
                        "Hora local",
                        value=dt.time(9, 0),
                        key="community_event_time",
                    )
                    cupos_propuesta = st.number_input(
                        "Cupos",
                        min_value=1,
                        max_value=500,
                        value=20,
                        step=1,
                        key="community_event_capacity",
                    )
                    st.caption("Los eventos comunitarios reciben 10 puntos al confirmar asistencia. Los ejemplos DEMO no acreditan puntos.")
                    if st.form_submit_button("Publicar evento", type="primary", icon=":material/campaign:"):
                        fecha_local_propuesta = dt.datetime.combine(
                            fecha_propuesta,
                            hora_propuesta,
                            tzinfo=ZoneInfo("America/Bogota"),
                        )
                        if (
                            len(titulo_propuesta.strip()) < 5
                            or len(tema_propuesta.strip()) < 3
                            or len(dirigido_propuesta.strip()) < 3
                            or len(descripcion_propuesta.strip()) < 10
                            or len(lugar_propuesta.strip()) < 3
                        ):
                            st.error("Completa el título, tema, público, descripción y lugar.")
                        elif fecha_local_propuesta <= dt.datetime.now(ZoneInfo("America/Bogota")):
                            st.error("La fecha y hora del evento deben ser futuras.")
                        else:
                            try:
                                st.session_state.sb.rpc(
                                    "crear_evento_usuario",
                                    {
                                        "p_titulo": titulo_propuesta.strip(),
                                        "p_tema": tema_propuesta.strip(),
                                        "p_dirigido_a": dirigido_propuesta.strip(),
                                        "p_descripcion": descripcion_propuesta.strip(),
                                        "p_lugar": lugar_propuesta.strip(),
                                        "p_fecha": fecha_local_propuesta.isoformat(),
                                        "p_cupos": int(cupos_propuesta),
                                    },
                                ).execute()
                                st.success("Evento publicado y visible para la comunidad.")
                                st.rerun()
                            except Exception as error:
                                st.error(
                                    f"No se pudo publicar el evento: "
                                    f"{getattr(error, 'message', None) or type(error).__name__}"
                                )
        eventos_disponibles = True
        try:
            eventos = (
                pub().table("eventos_comunitarios")
                .select("id,titulo,tema,dirigido_a,descripcion,lugar,fecha,puntos,cupos,es_demo")
                .eq("estado", "publicado")
                .gte("fecha", dt.datetime.now(dt.timezone.utc).isoformat())
                .order("fecha")
                .limit(20)
                .execute()
                .data
            )
            mis_asistencias = {}
            if user:
                registros = (
                    st.session_state.sb.table("asistencias_eventos")
                    .select("evento_id,estado")
                    .eq("usuario_id", user.id)
                    .execute()
                    .data
                )
                mis_asistencias = {registro["evento_id"]: registro["estado"] for registro in registros}
        except Exception as error:
            eventos = []
            eventos_disponibles = False
            codigo_error = getattr(error, "code", None)
            detalle_error = str(error).lower()
            tabla_faltante = next(
                (tabla for tabla in ("eventos_comunitarios", "asistencias_eventos") if tabla in detalle_error),
                None,
            )
            if codigo_error in ("PGRST205", "42P01"):
                tabla = tabla_faltante or "eventos_comunitarios"
                st.error(f"Supabase no encuentra `{tabla}` en su esquema API. Ejecuta `supabase_events.sql`; si ya lo aplicaste, recarga el esquema con `NOTIFY pgrst, 'reload schema';`.")
                st.caption(f"Código de Supabase: {codigo_error}.")
            elif codigo_error in ("PGRST204", "42703"):
                st.error("El esquema de eventos no está actualizado. Ejecuta `supabase_eventos_comunidad.sql` después de `supabase_events.sql`; si ya lo hiciste, recarga el esquema de Supabase.")
                st.caption(f"Diagnóstico: {codigo_error}")
            elif codigo_error in ("42501", "PGRST301"):
                st.error("Supabase rechazó la consulta de eventos. Revisa los permisos y las políticas RLS de `supabase_events.sql`.")
                st.caption(f"Diagnóstico: {codigo_error}")
            else:
                st.error("No se pudieron cargar los eventos. Revisa la conexión, el esquema y los permisos de Supabase.")
                st.caption(f"Referencia: {codigo_error or type(error).__name__}")

        if eventos_disponibles and not eventos:
            st.info("Aún no hay convocatorias publicadas. El equipo administrador puede crear eventos desde Moderación.")
        for evento in eventos:
            with st.container(border=True):
                if evento.get("es_demo"):
                    st.badge("DEMO · No es un evento real · No asistir", icon=":material/science:", color="orange")
                st.subheader(evento["titulo"])
                st.caption(f"{formato_fecha_evento(evento['fecha'])} · {evento['lugar']}")
                st.caption(f"Tema: {evento['tema']} · Dirigido a: {evento['dirigido_a']}")
                st.write(evento["descripcion"])
                if evento.get("es_demo"):
                    st.badge("Solo demostración · sin puntos", icon=":material/loyalty:", color="gray")
                else:
                    st.badge(f"{evento['puntos']} puntos al confirmar asistencia", icon=":material/loyalty:", color="green")
                st.caption(f"Cupos máximos: {evento['cupos']}")
                estado_asistencia = mis_asistencias.get(evento["id"])
                if estado_asistencia == "pendiente":
                    st.badge("Inscripción pendiente de asistencia", icon=":material/schedule:", color="orange")
                elif estado_asistencia == "confirmada":
                    st.success(f"Asistencia confirmada · {evento['puntos']} puntos incluidos en tu saldo.")
                elif estado_asistencia == "rechazada":
                    st.badge("Asistencia no confirmada", icon=":material/cancel:", color="red")
                elif not user:
                    st.info("Inicia sesión para inscribirte.")
                elif st.button("Inscribirme", key=f"inscribirse_evento_{evento['id']}", icon=":material/event_available:", width="stretch"):
                    try:
                        st.session_state.sb.rpc(
                            "registrar_asistencia_evento",
                            {"p_evento_id": int(evento["id"])},
                        ).execute()
                        st.success("Inscripción creada. Tu asistencia quedará pendiente hasta que el equipo la confirme en el evento.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"No se pudo completar la inscripción ({type(error).__name__}).")



# --- PESTAÑA 4: RECOMPENSAS ---
with tabs[":material/redeem: Recompensas"]:
    st.header("Tienda verde de aliados", icon=":material/redeem:")
    if not user: st.warning("Inicia sesión para ver tu saldo acumulado y canjear cupones reales.")
    else:
        saldo, ganados = obtener_saldo(st.session_state.sb, user.id)
        
        with st.container(border=True):
            ca, cb = st.columns(2)
            ca.metric("💰 Saldo Disponible", f"{saldo} pts")
            cb.metric("🏆 Acumulados Históricos", f"{ganados} pts")
        
        try:
            cat = pd.DataFrame(st.session_state.sb.table("cupones").select("*").eq("activo", True).order("puntos").execute().data)
            if cat.empty: st.info("Catálogo de recompensas vacío. Inyecta los cupones desde Supabase.")
            else:
                cols = st.columns(3)
                for i, r in enumerate(cat.itertuples()):
                    with cols[i % 3].container(border=True):
                        st.markdown(f"### {ICONOS.get(r.categoria, '🎁')} {r.descripcion}")
                        st.caption(f"📍 {r.comercio} · Stock disponible: {r.stock}")
                        st.markdown(f"**Costo: {r.puntos} pts**")
                        if st.button("Canjear recompensa", key=f"c_{r.id}", width="stretch", type="primary", disabled=saldo < r.puntos or r.stock <= 0):
                            codigo = uuid.uuid4().hex[:6].upper()
                            try:
                                codigo = st.session_state.sb.rpc(
                                    "canjear_evento_recompensa",
                                    {"p_cupon_id": int(r.id)},
                                ).execute().data
                                pass
                                st.success(f"¡Canje Exitoso! Muestra este código en la tienda: **{codigo}**")
                                time.sleep(2)
                                st.rerun() # Actualiza el saldo en vivo
                            except Exception as ex: st.error(getattr(ex, "message", None) or str(ex))
        except Exception: st.info("Configura la tabla 'canjes' y 'cupones' en Supabase para activar esta sección.")

# --- PESTAÑA 5: APRENDE ---
with tabs[":material/school: Aprende"]:
    st.header("Academia ambiental", icon=":material/school:")
    st.caption("Aprende a interpretar el clima urbano, elegir especies y actuar con seguridad.")
    if df is not None and not df.dropna().empty:
        d = df.dropna()
        caliente = d.loc[d['LST (°C)'].idxmax()]
        fresca = d.loc[d['LST (°C)'].idxmin()]
        st.info(f"Dato satelital activo: {caliente['Zona']} es aproximadamente {d['LST (°C)'].max() - d['LST (°C)'].min():.1f} °C más caliente en superficie que {fresca['Zona']}.")

    a1, a2, a3, a4, a5, a6, a7 = st.tabs([
        "Guía de plantas",
        "Separación de residuos",
        "Islas de calor",
        "Conceptos clave",
        "Acciones locales",
        "Siembra responsable",
        "Evidencia ciudadana",
    ])
    with a1:
        filtro = st.segmented_control("Tamaño adulto", ["Todas", "Pequeño-mediano", "Mediano", "Grande"], default="Todas")
        especies = PLANTAS
        if filtro == "Pequeño-mediano":
            especies = [p for p in especies if "pequeño" in p["tipo"].lower() or "mediano" in p["tipo"].lower()]
        elif filtro == "Mediano":
            especies = [p for p in especies if p["tipo"] == "Árbol mediano"]
        elif filtro == "Grande":
            especies = [p for p in especies if "grande" in p["tipo"].lower() or "gigante" in p["tipo"].lower()]
        cols = st.columns(2)
        for i, planta in enumerate(especies):
            with cols[i % 2].container(border=True):
                st.subheader(planta["nombre"])
                st.caption(f"*{planta['cientifico']}* · {planta['origen']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Tamaño", planta["tipo"])
                c2.metric("Sombra", planta["sombra"])
                c3.metric("Espacio", planta["espacio"])
                st.write(f"**Uso recomendado:** {planta['uso']}")
                st.write(f"**Cuidado:** {planta['cuidado']}")
                nivel = {"Baja": .25, "Media": .55, "Media-alta": .75, "Alta": .75, "Muy alta": .95}.get(planta["sombra"], .5)
                st.progress(nivel, text=f"Potencial de sombra: {planta['sombra']}")
        st.warning("Antes de sembrar: confirma la especie con la autoridad ambiental, revisa redes y tuberías, pide permisos y prepara un plan de riego para los primeros meses.")
    with a2:
        r1, r2, r3 = st.columns(3)
        r1.info("Aprovechables", icon=":material/recycling:")
        r1.write("Plástico limpio, vidrio, metales, papel y cartón seco.")
        r2.info("Orgánicos", icon=":material/compost:")
        r2.write("Restos de comida y residuos aptos para aprovechamiento.")
        r3.warning("No aprovechables", icon=":material/delete:")
        r3.write("Papel higiénico, servilletas sucias y empaques contaminados.")
        with st.expander("¿Cómo preparar un objeto reciclable?"):
            st.write("Vacía, limpia cuando sea necesario, seca y compacta sin mezclar otros residuos.")
        with st.expander("¿Qué hacer con aparatos electrónicos o peligrosos?"):
            st.write("No los mezcles con residuos comunes. Busca puntos de recolección autorizados.")
    with a3:
        st.markdown("#### Cómo se forma una isla de calor")
        pasos = [
            ("1", "Superficies absorbentes", "Asfalto y techos oscuros retienen más energía durante el día."),
            ("2", "Poca vegetación", "Hay menos sombra y menos evaporación que enfríen el entorno."),
            ("3", "Ventilación limitada", "Las geometrías urbanas pueden reducir el movimiento natural del aire."),
            ("4", "Respuesta climática", "La sombra, la vegetación, los techos claros y el agua pueden reducir el efecto."),
        ]
        for num, titulo, texto in pasos:
            c1, c2 = st.columns([.12, 1])
            c1.metric("Paso", num)
            c2.markdown(f"**{titulo}**")
            c2.caption(texto)
    with a4:
        with st.expander("¿Qué mide el NDVI?", expanded=True):
            st.write("El NDVI estima la cantidad y condición de vegetación mediante reflectancia satelital. Cerca de 0 puede representar suelo, asfalto o construcciones; valores altos suelen indicar vegetación vigorosa.")
        with st.expander("¿Qué mide la temperatura superficial?"):
            st.write("Mide cuánto calor emite la superficie visible desde el satélite. Puede diferir de la temperatura ambiente reportada por estaciones.")
        with st.expander("¿Qué significa el AQI?"):
            st.write("Resume la calidad del aire y el nivel de contaminación. Valores bajos indican menor riesgo; valores altos requieren precaución, especialmente en personas sensibles.")
        with st.expander("¿Cómo interpretar los puntos prioritarios?"):
            st.write("Los puntos son señales satelitales, no órdenes de siembra. Deben verificarse en campo antes de intervenir.")
    with a5:
        st.markdown("#### Acciones ambientales en tu entorno")
        acciones = [
            ("En casa", "Separa los residuos, reduce productos desechables y lleva pilas o aparatos electrónicos a puntos de recolección autorizados."),
            ("En tu barrio", "Reporta acumulaciones de residuos e identifica zonas sin sombra. Comparte ubicación aproximada, sin exponer datos personales."),
            ("En espacios verdes", "Coordina las actividades con responsables del lugar. Confirma permisos, especies apropiadas y plan de riego antes de sembrar."),
            ("Durante una jornada", "Lleva agua, usa protección solar, respeta las indicaciones del equipo y no intervengas cerca de redes o zonas de tránsito."),
        ]
        for titulo, detalle in acciones:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.write(detalle)
    with a6:
        st.markdown("#### Antes, durante y después de una siembra")
        fases = [
            ("Antes", "Confirma permisos, responsable del espacio, especie adecuada y disponibilidad de agua. Revisa redes subterráneas, cableado y espacio adulto con la autoridad local."),
            ("Durante", "Protege las raíces del sol y el viento, evita doblarlas y no entierres el cuello del árbol. Sigue las instrucciones del vivero y del equipo técnico; no improvises junto a vías o redes."),
            ("Después", "Define quién hará el riego y seguimiento. Registra fecha, especie y ubicación aproximada; revisa el estado del ejemplar y reporta daños a la entidad responsable."),
        ]
        for fase, detalle in fases:
            with st.container(border=True):
                st.subheader(fase)
                st.write(detalle)
        st.warning("No siembres en andenes, separadores ni parques sin autorización. Si hay cables, tuberías, tránsito o árboles inestables, suspende la actividad y contacta a la autoridad competente.")
        with st.expander("Lista de comprobación para una jornada"):
            st.markdown(
                "- Permiso y responsable del sitio confirmados.\n"
                "- Especie y espacio adulto revisados con personal técnico.\n"
                "- Agua, herramientas adecuadas y equipo de protección disponibles.\n"
                "- Ruta segura de acceso y retiro de residuos definida.\n"
                "- Plan de riego y seguimiento asignado."
            )
    with a7:
        st.markdown("#### Cómo registrar evidencia útil y respetuosa")
        pautas = [
            ("Contexto", "Toma una imagen general del lugar y otra clara de la acción, sin depender solo de un primer plano."),
            ("Claridad", "Evita fotos movidas, oscuras, recortadas o con el objetivo muy lejos. No uses capturas de pantalla ni imágenes descargadas."),
            ("Privacidad", "No incluyas rostros, placas, documentos, teléfonos ni interiores privados. Pide permiso antes de fotografiar a otras personas."),
            ("Honestidad", "Describe solo lo que hiciste y lo que la foto muestra. Una imagen no confirma por sí sola fecha, ubicación, autoría o que una planta se haya sembrado recientemente."),
            ("Seguimiento", "Conserva una foto posterior para observar el estado de la planta, sin exponer datos personales ni ubicaciones sensibles."),
        ]
        for titulo, detalle in pautas:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.write(detalle)
        st.info("Los reportes de SombraBAQ pasan por revisión humana. La IA brinda orientación visual y no aprueba reportes ni otorga puntos.")
    with st.expander("Fuentes y recursos oficiales"):
        st.caption("Verifica cada fuente antes de compartirla.")
        links = [("Islas de calor urbanas", "https://www.epa.gov/heatislands"),
                 ("NDVI y teledetección", "https://earthobservatory.nasa.gov/features/MeasuringVegetation"),
                 ("IDEAM de Colombia", "https://www.ideam.gov.co/"),
                 ("Ministerio de Ambiente", "https://www.minambiente.gov.co/"),
                 ("Google Earth Engine", "https://developers.google.com/earth-engine"),
                 ("iNaturalist", "https://www.inaturalist.org/")]
        cols = st.columns(2)
        for i, (titulo, url) in enumerate(links):
            cols[i % 2].link_button(titulo, url, width="stretch")

# --- PESTAÑA 6: DATOS ABIERTOS ---
with tabs[":material/database: Datos abiertos"]:
    @st.fragment(run_every=60)
    def abiertos():
        try: rp = reportes_publicos()
        except Exception: return
        a, b, c = st.columns(3)
        a.metric("Reportes validados", len(rp)); b.metric("Puntos otorgados", int(rp["puntos"].sum()) if len(rp) else 0)
        c.metric("Siembras aprobadas", int((rp["tipo"] == "siembra").sum()) if len(rp) else 0)
        st.markdown("### 🏆 Ranking ciudadano")
        try: rk = pd.DataFrame(pub().rpc("ranking_publico").execute().data)
        except Exception: rk = pd.DataFrame()
        if rk.empty: st.info("Aún no hay ciudadanos en el ranking. Publica un reporte verificado para aparecer.")
        else:
            med = ["🥇", "🥈", "🥉"]; top = st.columns(min(3, len(rk)))
            for i, r in enumerate(rk.head(3).itertuples()): top[i].metric(f"{med[i]} {r.alias}", f"{r.puntos} pts", f"{r.siembras} siembras", delta_color="off")
            rk.insert(0, "Puesto", range(1, len(rk) + 1))
            st.dataframe(rk.rename(columns={"alias": "Ciudadano", "puntos": "Puntos", "siembras": "Siembras", "reportes": "Reportes"}), hide_index=True, width="stretch",
                         column_config={"Puntos": st.column_config.ProgressColumn("Puntos", min_value=0, max_value=max(1, int(rk["puntos"].max())), format="%d")})
            st.caption("Solo se muestra el nombre y la inicial del apellido. Puntos de reportes aprobados.")
        if len(rp):
            st.markdown("### 🗺️ Puntos por zona"); st.bar_chart(rp.groupby("zona")["puntos"].sum().sort_values(ascending=False), color="#16a34a", height=260)
            gj = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r.lng, r.lat]}, "properties": {"tipo": r.tipo, "zona": r.zona, "fecha": r.created_at}} for r in rp.itertuples()]}
            st.download_button("⬇️ Descargar datos (GeoJSON)", json.dumps(gj, ensure_ascii=False), "sombrabaq_reportes.geojson", "application/geo+json")
    abiertos()

# --- PESTAÑA 7: PERFIL ---
if user:
    with tabs[":material/person: Mi perfil"]:
        sb = st.session_state.sb; pf = st.session_state.get("datos_perfil", {})
        saldo, ganados = obtener_saldo(sb, user.id)
        NIV = [(0, "🌱 Semilla"), (50, "🌿 Brote"), (150, "🌳 Árbol"), (400, "🌲 Bosque")]
        i = max(j for j, (mn, _) in enumerate(NIV) if ganados >= mn)
        
        st.subheader(f"Configuración de la cuenta: {(pf.get('nombre', '') + ' ' + pf.get('apellido', '')).strip() or user.email}")
        
        k = st.columns(3)
        k[0].metric("Rango Ciudadano", NIV[i][1])
        k[1].metric("Puntos Históricos", ganados)
        k[2].metric("Reportes Exitosos", len(reportes_publicos()[reportes_publicos()['user_id'] == user.id]) if not reportes_publicos().empty else 0)
        if i < 3: st.progress(min(1.0, ganados / NIV[i + 1][0]), text=f"Faltan {NIV[i + 1][0] - ganados} pts para avanzar a {NIV[i + 1][1]}")

        with st.expander("Estado de mis reportes", expanded=True):
            try:
                mis_reportes = sb.table("reportes").select("id,created_at,tipo,zona,estado,nota,puntos").eq("user_id", user.id).order("created_at", desc=True).limit(50).execute().data
                if not mis_reportes:
                    st.caption("Todavia no has enviado reportes.")
                for reporte in mis_reportes:
                    estado = reporte["estado"]
                    icono = {"pendiente": "schedule", "aprobado": "check_circle", "verificado_ia": "verified", "rechazado": "cancel"}.get(estado, "pending")
                    estado_label = {"pendiente": "En revision", "aprobado": "Aprobado", "verificado_ia": "Verificado", "rechazado": "Rechazado"}.get(estado, estado)
                    st.markdown(f":material/{icono}: **{TIPOS.get(reporte['tipo'], reporte['tipo'])}** · {reporte['zona']}")
                    st.caption(f"{estado_label} · {str(reporte['created_at'])[:16].replace('T', ' ')} · {reporte['puntos']} puntos")
            except Exception:
                st.caption("No fue posible consultar el estado de tus reportes.")

        with st.expander("Mis eventos e inscripciones"):
            try:
                inscripciones = (
                    sb.table("asistencias_eventos")
                    .select("id,evento_id,estado,registrado_at,verificado_at")
                    .eq("usuario_id", user.id)
                    .order("registrado_at", desc=True)
                    .limit(50)
                    .execute()
                    .data
                )
                ids_eventos = list({inscripcion["evento_id"] for inscripcion in inscripciones})
                eventos_usuario = {}
                if ids_eventos:
                    eventos_usuario = {
                        evento["id"]: evento
                        for evento in sb.table("eventos_comunitarios")
                        .select("id,titulo,fecha,puntos,lugar")
                        .in_("id", ids_eventos)
                        .execute()
                        .data
                    }
                if not inscripciones:
                    st.caption("Todavía no tienes inscripciones a eventos.")
                for inscripcion in inscripciones:
                    evento_usuario = eventos_usuario.get(inscripcion["evento_id"])
                    if not evento_usuario:
                        continue
                    st.markdown(f"**{evento_usuario['titulo']}** · {evento_usuario['lugar']}")
                    if inscripcion["estado"] == "confirmada":
                        st.success(f"Asistencia confirmada · {evento_usuario['puntos']} puntos acreditados.")
                    elif inscripcion["estado"] == "pendiente":
                        st.badge("Pendiente de confirmación presencial", icon=":material/schedule:", color="orange")
                    else:
                        st.badge("Asistencia no confirmada", icon=":material/cancel:", color="red")
                    st.caption(f"{formato_fecha_evento(evento_usuario['fecha'])} · Inscripción {str(inscripcion['registrado_at'])[:16]}")
            except Exception as error:
                st.warning("No se pudo consultar el historial de eventos. Confirma que `supabase_events.sql` esté aplicado.")
                st.caption(f"Diagnóstico: {type(error).__name__}")
        
        with st.expander("🎟️ Mis Códigos Canjeados", expanded=True):
            try:
                mis_canjes = sb.table("canjes").select("created_at, puntos, codigo, cupones(descripcion, comercio)").eq("user_id", user.id).order("created_at", desc=True).execute().data
                if mis_canjes:
                    for c in mis_canjes: st.success(f"**{c['cupones']['descripcion']} en {c['cupones']['comercio']}** - Tu código: `{c['codigo']}` (Pagado con {c['puntos']} pts)")
                else: st.caption("No has canjeado recompensas aún. Ve a la Tienda Verde.")
            except Exception: st.caption("Historial no disponible.")
        
        with st.form("perfil_form"):
            st.markdown("**Actualizar datos de contacto**")
            c1, c2 = st.columns(2)
            tel = c1.text_input("Celular de contacto", pf.get("telefono", ""))
            zona = c2.selectbox("Zona de residencia principal", list(ZONAS), index=list(ZONAS).index(pf["zona"]) if pf.get("zona") in ZONAS else 0)
            if st.form_submit_button("Guardar cambios en el perfil", type="primary"):
                try:
                    sb.table("perfiles").update({"telefono": tel, "zona": zona}).eq("user_id", user.id).execute()
                    st.session_state.datos_perfil = {**pf, "telefono": tel, "zona": zona}; st.success("Datos guardados en Supabase.")
                except Exception as ex: st.error(f"Error de base de datos: {ex}")

# --- PESTAÑA 8: MODERACIÓN ---
if admin:
    with tabs[":material/admin_panel_settings: Moderación"]:
        with st.expander("Publicar una convocatoria", expanded=False):
            plantilla = st.selectbox("Tipo de actividad", ["Personalizada", *EVENTOS_SUGERIDOS], key="event_template")
            titulo_evento = st.text_input(
                "Título",
                value="" if plantilla == "Personalizada" else plantilla,
                max_chars=120,
                key=f"event_title_{plantilla}",
            )
            descripcion_evento = st.text_area("Descripción y recomendaciones para asistentes", max_chars=1200)
            lugar_evento = st.text_input("Lugar de encuentro", max_chars=200)
            fecha_columnas = st.columns(2)
            fecha_evento = fecha_columnas[0].date_input(
                "Fecha",
                value=dt.date.today() + dt.timedelta(days=7),
                min_value=dt.date.today(),
                key="event_date",
            )
            hora_evento = fecha_columnas[1].time_input("Hora local", value=dt.time(9, 0), key="event_time")
            puntos_columnas = st.columns(2)
            puntos_evento = puntos_columnas[0].number_input("Puntos al confirmar asistencia", min_value=1, max_value=500, value=30, step=5)
            cupos_evento = puntos_columnas[1].number_input("Cupos", min_value=1, max_value=10000, value=30, step=1)
            if st.button("Publicar evento", key="publish_event", icon=":material/campaign:", type="primary"):
                fecha_local = dt.datetime.combine(fecha_evento, hora_evento, tzinfo=ZoneInfo("America/Bogota"))
                if len(titulo_evento.strip()) < 5 or len(descripcion_evento.strip()) < 10 or len(lugar_evento.strip()) < 3:
                    st.error("Completa un título, una descripción y un lugar válidos.")
                elif fecha_local <= dt.datetime.now(ZoneInfo("America/Bogota")):
                    st.error("La fecha y hora del evento deben ser futuras.")
                else:
                    try:
                        st.session_state.sb.rpc(
                            "crear_evento_comunitario",
                            {
                                "p_titulo": titulo_evento.strip(),
                                "p_descripcion": descripcion_evento.strip(),
                                "p_lugar": lugar_evento.strip(),
                                "p_fecha": fecha_local.isoformat(),
                                "p_puntos": int(puntos_evento),
                                "p_cupos": int(cupos_evento),
                            },
                        ).execute()
                        st.success("Evento publicado. La inscripción no acredita puntos hasta confirmar la asistencia.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"No se pudo publicar el evento ({type(error).__name__}).")

        st.subheader("Asistencias pendientes")
        try:
            asistencias_pendientes = (
                st.session_state.sb.table("asistencias_eventos")
                .select("id,evento_id,usuario_id,registrado_at")
                .eq("estado", "pendiente")
                .order("registrado_at")
                .limit(100)
                .execute()
                .data
            )
            ids_eventos = list({registro["evento_id"] for registro in asistencias_pendientes})
            eventos_por_id = {}
            if ids_eventos:
                eventos_por_id = {
                    evento["id"]: evento
                    for evento in st.session_state.sb.table("eventos_comunitarios")
                    .select("id,titulo,fecha,es_demo")
                    .in_("id", ids_eventos)
                    .execute()
                    .data
                }
            if not asistencias_pendientes:
                st.caption("No hay asistencias esperando verificación.")
            for asistencia in asistencias_pendientes:
                evento_asistencia = eventos_por_id.get(asistencia["evento_id"])
                with st.container(border=True):
                    st.markdown(f"**{evento_asistencia['titulo'] if evento_asistencia else 'Evento no disponible'}**")
                    if evento_asistencia:
                        st.caption(f"Fecha del evento: {formato_fecha_evento(evento_asistencia['fecha'])}")
                        if evento_asistencia.get("es_demo"):
                            st.info("Es un evento de demostración: no confirmes asistencia ni otorgues puntos.")
                    st.caption(f"Referencia de inscripción: {asistencia['id']} · Usuario: {asistencia['usuario_id']}")
                    motivo = st.text_input("Nota de verificación (opcional)", max_chars=300, key=f"nota_asistencia_{asistencia['id']}")
                    confirmar, rechazar = st.columns(2)
                    fecha_evento_asistencia = (
                        dt.datetime.fromisoformat(evento_asistencia["fecha"].replace("Z", "+00:00"))
                        if evento_asistencia
                        else None
                    )
                    if fecha_evento_asistencia and fecha_evento_asistencia.tzinfo is None:
                        fecha_evento_asistencia = fecha_evento_asistencia.replace(tzinfo=dt.timezone.utc)
                    puede_confirmar = (
                        fecha_evento_asistencia is not None
                        and fecha_evento_asistencia <= dt.datetime.now(dt.timezone.utc)
                        and not evento_asistencia.get("es_demo")
                    )
                    if evento_asistencia and evento_asistencia.get("es_demo"):
                        st.caption("Las asistencias de eventos DEMO no se pueden confirmar.")
                    elif not puede_confirmar:
                        st.info("La asistencia solo se confirma después de la fecha del evento.")
                    if confirmar.button(
                        "Confirmar asistencia",
                        key=f"confirmar_asistencia_{asistencia['id']}",
                        icon=":material/person_check:",
                        type="primary",
                        disabled=not puede_confirmar,
                        width="stretch",
                    ):
                        try:
                            st.session_state.sb.rpc(
                                "verificar_asistencia_evento",
                                {
                                    "p_asistencia_id": int(asistencia["id"]),
                                    "p_accion": "confirmar",
                                    "p_razon": motivo.strip() or None,
                                },
                            ).execute()
                            st.success("Asistencia confirmada; los puntos ya cuentan para los canjes.")
                            st.rerun()
                        except Exception as error:
                            st.error(f"No se pudo confirmar la asistencia ({type(error).__name__}).")
                    if rechazar.button(
                        "No asistió",
                        key=f"rechazar_asistencia_{asistencia['id']}",
                        icon=":material/person_off:",
                        width="stretch",
                    ):
                        try:
                            st.session_state.sb.rpc(
                                "verificar_asistencia_evento",
                                {
                                    "p_asistencia_id": int(asistencia["id"]),
                                    "p_accion": "rechazar",
                                    "p_razon": motivo.strip() or None,
                                },
                            ).execute()
                            st.success("Asistencia marcada como no confirmada.")
                            st.rerun()
                        except Exception as error:
                            st.error(f"No se pudo actualizar la asistencia ({type(error).__name__}).")
        except Exception as error:
            st.warning("El módulo de asistencia requiere aplicar `supabase_events.sql` y revisar permisos de administrador.")
            st.caption(f"Diagnóstico: {type(error).__name__}")

        try:
            pend = st.session_state.sb.table("reportes").select("*").eq("estado", "pendiente").order("created_at").limit(20).execute().data
            st.write(f"**{len(pend)} reportes manuales en cola de revisión**")
            for r in pend:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 2])
                    try: c1.image(st.session_state.sb.storage.from_("evidencias").create_signed_url(r["foto_path"], 300)["signedURL"], width=200)
                    except: c1.caption("Sin evidencia gráfica")
                    c2.markdown(f"**{TIPOS[r['tipo']]}** en {r['zona']}")
                    c2.caption(f"Nota del usuario: {r['nota'] or 'Sin texto'}")
                    c2.caption(
                        f"Orientación visual ({(r.get('ia_confianza') or 0):.0%}): "
                        f"{r.get('ia_detalle') or 'No disponible; revisar manualmente.'}"
                    )
                    b1, b2, _ = c2.columns([1, 1, 3])
                    razon = c2.text_input("Motivo de moderación", key=f"motivo_{r['id']}", max_chars=300)
                    if b1.button("Aprobar reporte", key=f"a_{r['id']}"):
                        now = dt.datetime.now(dt.timezone.utc).isoformat()
                        st.session_state.sb.table("reportes").update({
                            "estado": "aprobado",
                            "moderado_por": st.session_state.user.id,
                            "moderado_at": now,
                            "razon_moderacion": razon.strip() or "Aprobado tras revisión manual."
                        }).eq("id", r["id"]).execute()
                        try:
                            st.session_state.sb.table("moderacion_log").insert({
                                "reporte_id": r["id"], "moderador_id": st.session_state.user.id,
                                "accion": "aprobar", "razon": razon.strip() or None
                            }).execute()
                        except Exception:
                            pass
                        reportes_publicos.clear()
                        st.success("Reporte aprobado y registrado.")
                        st.rerun()
                    if b2.button("Rechazar", key=f"r_{r['id']}"):
                        now = dt.datetime.now(dt.timezone.utc).isoformat()
                        st.session_state.sb.table("reportes").update({
                            "estado": "rechazado",
                            "moderado_por": st.session_state.user.id,
                            "moderado_at": now,
                            "razon_moderacion": razon.strip() or "Rechazado tras revisión manual."
                        }).eq("id", r["id"]).execute()
                        try:
                            st.session_state.sb.table("moderacion_log").insert({
                                "reporte_id": r["id"], "moderador_id": st.session_state.user.id,
                                "accion": "rechazar", "razon": razon.strip() or None
                            }).execute()
                        except Exception:
                            pass
                        reportes_publicos.clear()
                        st.rerun()
        except Exception: st.info("Cola limpia. No hay reportes esperando revisión manual.")

st.divider()
st.caption("Fuentes: Google Earth Engine (Sentinel-2, Landsat 8/9), Open-Meteo y reportes ciudadanos. SombraBAQ es una plataforma ambiental en fase operativa: la información debe verificarse antes de tomar decisiones críticas.")
st.caption("Desarrollado y programado por Juan David Barrios, estudiante de Ingeniería de Software de la Universidad de Barranquilla.")
