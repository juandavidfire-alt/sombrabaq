"""SombraBAQ - Plataforma Geoespacial, Red Social Ambiental y Reportes Ciudadanos."""
import base64, datetime as dt, hashlib, io, json, math, re, uuid, time
import folium, pandas as pd, requests, streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="SombraBAQ | Observatorio climático", page_icon=":material/park:", layout="wide")

def gee_service_account_credentials(info):
    from google.oauth2 import service_account

    account_info = dict(info)
    account_info["private_key"] = str(account_info.get("private_key") or "").replace("\\n", "\n").strip()
    account_info.setdefault("token_uri", "https://oauth2.googleapis.com/token")
    return service_account.Credentials.from_service_account_info(
        account_info,
        scopes=["https://www.googleapis.com/auth/earthengine"],
    )


with st.expander("Diagnóstico temporal de Earth Engine"):
    info = None
    try:
        info = dict(st.secrets["gee_service_account"])
    except KeyError:
        st.error("Falta `gee_service_account` en los secretos de Streamlit.")
    except Exception as error:
        st.error(f"No se pudo leer `gee_service_account`: {type(error).__name__}")

    if info is not None:
        st.success("Streamlit encontró las credenciales.")
        if st.button("Probar conexión con Earth Engine", key="probar_conexion_gee"):
            email = str(info.get("client_email") or "").strip()
            private_key = str(info.get("private_key") or "").replace("\\n", "\n").strip()
            project_id = str(info.get("project_id") or "").strip()
            missing = [
                field for field, value in (
                    ("client_email", email),
                    ("private_key", private_key),
                    ("project_id", project_id),
                )
                if not value
            ]

            if missing:
                st.error("Faltan campos en `gee_service_account`: " + ", ".join(missing))
            else:
                try:
                    import ee

                    credentials = gee_service_account_credentials(info)
                    ee.Initialize(credentials, project=project_id)
                    resultado = ee.Number(1).getInfo()
                    st.success(f"Earth Engine conectado: {resultado}")
                except Exception as error:
                    mensaje = str(error)
                    for secreto in (private_key, private_key.replace("\n", "\\n"), email):
                        if secreto:
                            mensaje = mensaje.replace(secreto, "[dato sensible oculto]")
                    st.error(f"Error de conexión: {type(error).__name__}")
                    if mensaje:
                        st.code(mensaje[:600])

st.markdown("""<style>
/* CSS Seguro para Modo Claro/Oscuro de Streamlit */
.block-container {padding-top:1.25rem !important; padding-bottom:2.5rem !important; max-width:1440px;}
.hero {background:linear-gradient(118deg,#12372a 0%,#166534 58%,#087f73 100%); border:1px solid rgba(255,255,255,.12); border-radius:16px; padding:1.35rem 1.65rem; margin-bottom:.65rem; color:white; box-shadow:0 10px 28px rgba(18,55,42,.12); position:relative; overflow:hidden;}
.hero:after {content:""; position:absolute; width:220px; height:220px; right:-70px; top:-130px; border-radius:50%; background:rgba(255,255,255,.07);}
.hero h1 {margin:.12rem 0 .18rem; font-size:2.05rem; font-weight:800; color:white; letter-spacing:-.035em;}
.hero p {margin:0; opacity:.88; font-weight:500; font-size:1rem; max-width:760px;}
.hero .live {background:rgba(255,255,255,.16); padding:.22rem .75rem; border-radius:20px; font-size:.72rem; font-weight:800; letter-spacing:.08em; display:inline-block;}
.hero .live::before {content:""; display:inline-block;width:.42rem;height:.42rem;border-radius:50%;background:#86efac;margin-right:.45rem;box-shadow:0 0 0 4px rgba(134,239,172,.12);animation:parpadeo 1.5s infinite;}
@keyframes parpadeo {50% {opacity:.3}}
@keyframes aparecer {from {opacity:0; transform:translateY(8px)} to {opacity:1; transform:translateY(0)}}
.hero {animation:aparecer .45s ease-out both;}
[data-testid="stVerticalBlockBorderWrapper"] {animation:aparecer .32s ease-out both;}
[data-testid="stSidebar"] {border-right:1px solid rgba(22,101,52,.10);}
[data-testid="stMetric"] {padding:.15rem .1rem; transition:transform .18s ease, box-shadow .18s ease;}
[data-testid="stMetric"]:hover {transform:translateY(-2px);}
[data-testid="stTabs"] [role="tablist"] {gap:.18rem; border-bottom:1px solid rgba(22,101,52,.12); margin-bottom:.7rem;}
[data-testid="stTabs"] [role="tab"] {padding:.7rem .82rem; border-radius:10px 10px 0 0; transition:background .18s ease, color .18s ease;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {background:rgba(22,101,52,.10); color:#166534;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px;}
[data-testid="stButton"] button {border-radius:9px; transition:transform .15s ease, box-shadow .15s ease;}
[data-testid="stButton"] button:hover {transform:translateY(-1px); box-shadow:0 5px 14px rgba(22,101,52,.12);}
[data-testid="stForm"] {border-radius:12px;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {margin-top:-.55rem; margin-bottom:.8rem;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {line-height:1.35;}
[data-testid="stSlider"] {padding-top:.15rem;}
[data-testid="stMetricValue"] {letter-spacing:-.025em;}
::-webkit-scrollbar {width:8px; height:8px;}
::-webkit-scrollbar-thumb {background:#bfd1c4; border-radius:8px;}
::-webkit-scrollbar-track {background:transparent;}
iframe[title="st_folium"] {border-radius:12px; border:1px solid rgba(22,101,52,.12);}
@media (max-width: 720px) {
    .block-container {padding-top:.75rem !important;}
    .hero {padding:1.1rem; border-radius:12px;}
    .hero h1 {font-size:1.65rem;}
    .hero p {font-size:.9rem;}
    [data-testid="stTabs"] [role="tab"] {padding:.55rem .55rem;}
}
.live-status {border:1px solid rgba(22,101,52,.16);border-radius:14px;padding:.55rem .8rem;margin:.25rem 0 1rem;background:rgba(240,253,244,.58);}
.leyenda {height:8px; border-radius:6px; background:linear-gradient(90deg,#22c55e,#a3e635,#facc15,#fb923c,#ef4444); margin:.4rem 0 .2rem}
.social-card {background:#f8fafc; border:1px solid #e2e8f0; border-radius:16px; padding:1.5rem; margin-bottom:1.2rem; transition:transform .2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05);}
.social-card:hover {transform:translateY(-3px); border-color:#22c55e;}
.species-card {border:1px solid rgba(22,101,52,.14); border-radius:16px; padding:1rem; height:100%; background:rgba(255,255,255,.55);}
@media (prefers-color-scheme: dark) {
    .social-card {background:#0e2017; border-color:#1f6f4a;}
    .live-status {background:#10291e;border-color:#1f6f4a;}
    .species-card {background:#10291e;border-color:#1f6f4a;}
}
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
        return ganados - gastados, ganados
    except Exception: return 0, 0

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
    from PIL import Image; im = Image.open(io.BytesIO(datos)).convert("RGB"); im.thumbnail((1024, 1024))
    try: cfg = dict(st.secrets["anthropic"])
    except Exception: cfg = {}
    if cfg.get("api_key"):
        try:
            import anthropic; buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
            texto = ("Verifica si la foto muestra " + OBJETIVO[tipo] + ". Sé estricto, rechaza capturas de pantalla. "
                     'Responde SOLO un JSON: {"cumple": true|false, "confianza": 0 a 1, "detalle": "frase breve de justificación"}')
            msg = anthropic.Anthropic(api_key=cfg["api_key"]).messages.create(model=cfg.get("model", "claude-haiku-5-5"), max_tokens=200, messages=[{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}, {"type": "text", "text": texto}]}])
            j = json.loads(re.search(r"\{.*\}", msg.content[0].text, re.S).group())
            return {"cumple": bool(j.get("cumple")), "confianza": float(j.get("confianza", 0)), "metodo": "Claude Vision AI", "detalle": j.get("detalle", "")}
        except Exception: pass
    
    import numpy as np; a = np.asarray(im.resize((256, 256)), dtype=float) / 255
    verde = float(((2 * a[..., 1] - a[..., 0] - a[..., 2]) > 0.08).mean())
    if tipo == "residuos": return {"cumple": False, "confianza": 0.0, "metodo": "Filtro Demo", "detalle": "El filtro demo de color no procesa basura. Enviado a revisión manual."}
    return {"cumple": verde >= 0.12, "confianza": min(1.0, verde * 3), "metodo": "Filtro Demo de Vegetación", "detalle": f"Color verde detectado: {verde:.0%} del área."}

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

def _publicar(sb, user, ia, ok, zona_cercana, reportes_publicos):
    try:
        hash_foto = hashlib.sha256(ia["datos"]).hexdigest()
        duplicados = sb.table("reportes").select("id").eq("foto_hash", hash_foto).limit(1).execute().data
        if duplicados:
            st.error("Esta misma evidencia ya fue registrada. No se otorgaran puntos adicionales.")
            return
        ruta = f"{user.id}/{uuid.uuid4().hex}.jpg"
        sb.storage.from_("evidencias").upload(ruta, ia["datos"], {"content-type": ia["mime"]})
        estado_final = "aprobado" if ok else "pendiente"
        
        sb.table("reportes").insert({
            "user_id": user.id, "tipo": ia["tipo"], "lat": ia["pin"][0], "lng": ia["pin"][1], 
            "zona": zona_cercana(*ia["pin"]), "nota": ia["nota"], "foto_path": ruta, 
            "estado": estado_final, "puntos": PUNTOS[ia["tipo"]], "ia_confianza": ia["confianza"],
            "ia_detalle": f"[{ia['metodo']}] {ia['detalle']}"[:500], "foto_hash": hash_foto
        }).execute()
        
        st.session_state.pop("ia", None); st.session_state.pin = None; reportes_publicos.clear()
        if ok:
            st.success(f"¡Validación automática exitosa! Has ganado **{PUNTOS[ia['tipo']]} puntos**. 🌍✨")
            st.balloons()
        else: 
            st.info("La plataforma no pudo validar la imagen automáticamente. Ha sido enviada a moderación manual.")
        
        # ACTUALIZACIÓN EN TIEMPO REAL: Pausamos 2.5 segs para que el usuario lea, y recargamos para actualizar puntos
        time.sleep(2.5)
        st.rerun()
        
    except Exception as ex: 
        st.error(f"Error interno al guardar: Es posible que la foto esté duplicada o falten permisos. Detalles: {ex}")

# ---------- BARRA LATERAL Y AUTENTICACIÓN ----------
def entrar(sb, email, password):
    try:
        r = sb.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = r.user; sb.postgrest.auth(r.session.access_token)
        st.session_state.admin = bool(sb.table("admins").select("user_id").execute().data)
        pr = sb.table("perfiles").select("*").eq("user_id", r.user.id).execute().data
        st.session_state.datos_perfil = pr[0] if pr else {}
        st.rerun()
    except Exception: st.sidebar.error("Credenciales incorrectas o correo sin confirmar.")

@st.dialog("Crear cuenta ciudadana", width="large")
def dialogo_registro():
    sb = sb_client()
    with st.form("registro"):
        st.markdown("**Datos personales**")
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombres *")
        a = c2.text_input("Apellidos *")
        td = c1.selectbox("Tipo doc *", list(TIPOS_DOC))
        nd = c2.text_input("Número doc *")
        tl = c1.text_input("Celular *")
        z = c2.selectbox("Zona", list(ZONAS))
        st.markdown("**Datos de acceso**")
        e = st.text_input("Correo electrónico *")
        p1 = st.text_input("Contraseña *", type="password")
        p2 = st.text_input("Repetir Contraseña *", type="password")
        if st.form_submit_button("Registrar Cuenta", type="primary", width="stretch"):
            if p1 == p2 and len(p1) >= 8:
                try:
                    r = sb.auth.sign_up({"email": e.strip().lower(), "password": p1, "options": {"data": {"nombre": n.strip().title(), "apellido": a.strip().title(), "telefono": tl, "tipo_doc": td, "num_doc": nd, "zona": z}}})
                    if r.session: entrar(sb, e, p1)
                    else: st.success("Registro exitoso. Revisa tu correo (y spam) para confirmar.")
                except Exception as ex: st.error(f"Error al registrar: {ex}")
            else: st.error("Las contraseñas no coinciden o tienen menos de 8 caracteres.")

def invitado(sb):
    try:
        r = sb.auth.sign_in_anonymously(); st.session_state.user = r.user
        sb.postgrest.auth(r.session.access_token); st.session_state.admin = False; st.session_state.datos_perfil = {"nombre": "Invitado"}
        st.rerun()
    except Exception as ex:
        st.sidebar.error("Activa «Allow anonymous sign-ins» en Supabase → Authentication → Sign In / Providers." if "anonymous" in str(ex).lower() or "disabled" in str(ex).lower() else f"No se pudo entrar: {ex}")

def generar_alertas(info, aire, aq):
    out, lm = [], info["LST (°C)"].mean()
    for z, r in info.iterrows():
        n, l = r["NDVI"], r["LST (°C)"]
        if pd.notna(n) and n < 0.30: out.append((3 if n < 0.2 else 2, "🌱 Plantar", z, f"NDVI {n:.2f}: poca vegetación.", "Priorizar árboles de sombra nativos o adaptados y corredores verdes. Confirmar especies y permisos con la autoridad ambiental local."))
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
    with st.sidebar.container(border=True):
        st.markdown("**Configuración del análisis**")
        dias = st.slider("Ventana satelital", 20, 120, 60, 10, help="Periodo usado para combinar imágenes satelitales.")
    _, supabase_key = cfg()
    if not supabase_key:
        st.sidebar.warning(
            "La autenticación y las funciones de comunidad requieren configurar Supabase en los secretos de Streamlit Cloud.",
            title="Supabase pendiente de configuración",
        )
        return dias

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
            if st.button("Entrar como invitado", icon=":material/science:", width="stretch"): invitado(sb)
    return dias

dias = sidebar()
user, admin = st.session_state.get("user"), st.session_state.get("admin")

# ---------- ESTRUCTURA PRINCIPAL DE PESTAÑAS ----------
st.markdown(
    "<div class='hero'><span class='live'>DATOS EN TIEMPO REAL</span>"
    "<h1>SombraBAQ</h1>"
    "<p>Observatorio climático para Barranquilla · Satélites, comunidad y acción ambiental</p>"
    "</div>",
    unsafe_allow_html=True,
)

if not cfg()[1]:
    st.warning(
        "El panel climático sigue disponible, pero inicio de sesión, reportes ciudadanos, comunidad y recompensas "
        "están pausados hasta configurar Supabase.",
        title="Configura Supabase para habilitar todas las funciones",
    )
    with st.expander("Cómo configurarlo en Streamlit Cloud"):
        st.markdown("Abre **Manage app → Settings → Secrets** y añade las credenciales de tu proyecto Supabase:")
        st.code(
            '[supabase]\nurl = "https://<project-ref>.supabase.co"\nanon_key = "<publishable-or-anon-key>"',
            language="toml",
        )
        st.caption("Copia los valores desde Supabase → Project Settings → API. No publiques ni compartas claves secretas.")

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
    
    try:
        df, tiles, meta = satelite(dias)
    except Exception:
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
        peor = max(zd, key=lambda k: zd[k][4]) if zd else None

        mapa_col, panel_col = st.columns([3, 1.1])
        with mapa_col:
            from folium.plugins import Fullscreen
            m = folium.Map(location=[10.97, -74.80], zoom_start=12, min_zoom=11, max_zoom=18, tiles=None, prefer_canvas=True, max_bounds=True)
            m.get_root().html.add_child(folium.Element("<style>@keyframes pulso{0%{box-shadow:0 0 0 0 rgba(239,68,68,.75)}100%{box-shadow:0 0 0 24px rgba(239,68,68,0)}}.pulso{animation:pulso 1.6s infinite}.arbol{filter:drop-shadow(0 2px 2px rgba(0,0,0,.6));transition:transform .15s}.arbol:hover{transform:scale(1.8)}</style>"))
            for i_, (nb, (ub, nz)) in enumerate(BASES.items()): folium.TileLayer(ub, attr="Esri/OSM", name=nb, show=(i_ == 0), max_native_zoom=nz, max_zoom=19).add_to(m)
            if capa in tiles: folium.TileLayer(tiles[capa], attr="Google Earth Engine", name=capa, opacity=0.8, overlay=True).add_to(m)
            
            if ver_ico and capa == "NDVI":
                for la, lo, v in meta.get("arboles", []): folium.Marker([la, lo], tooltip=f"Muestra verde: NDVI {v:.2f}", icon=folium.DivIcon(icon_size=(26, 26), icon_anchor=(13, 13), html=f'<div class="arbol" style="font-size:{13 + int((v - 0.5) * 40)}px">🌳</div>')).add_to(m)
            if ver_ico and capa in ("NDVI", "LST"):
                for i_p, (la, lo, v, tl) in enumerate(meta.get("plantar", []), 1):
                    folium.Marker([la, lo], tooltip=f"Plantar #{i_p}: NDVI {v:.2f}, superficie {tl:.0f} °C", icon=folium.DivIcon(icon_size=(22, 22), icon_anchor=(11, 11), html=f'<div class="pulso" style="width:22px;height:22px;border-radius:50%;background:#facc15;border:2px solid #fff;color:#1a1a1a;font:700 11px system-ui;text-align:center;line-height:18px">{i_p}</div>')).add_to(m)
            if ver_ico and capa == "LST":
                for la, lo, v in meta.get("calientes", []): folium.Marker([la, lo], tooltip=f"Foco de calor: {v:.1f} °C", icon=folium.DivIcon(icon_size=(14, 14), html='<div class="pulso" style="width:12px;height:12px;border-radius:50%;background:#ef4444;border:2px solid #fff"></div>')).add_to(m)
            
            for z, (lat, lng, txt, col, peso, det) in zd.items():
                folium.Circle([lat, lng], RADIO_M, color=col, weight=2, fill=True, fill_color=col, fill_opacity=0.3 if capa in ("AIRE", "AQI") else 0.08).add_to(m)
                cls = "pulso" if z == peor else ""
                badge = f'<div class="{cls}" style="background:{col};color:#0b1a14;font:700 15px Inter,system-ui;padding:4px 12px;border-radius:14px;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.5);text-align:center;white-space:nowrap">{txt}<div style="font:600 9px system-ui">{z}</div></div>'
                folium.Marker([lat, lng], tooltip=z, icon=folium.DivIcon(icon_size=(110, 44), icon_anchor=(55, 22), html=badge), popup=folium.Popup(f"<div style='font:13px system-ui;min-width:180px'><b>{z}</b><hr style='margin:5px 0'>{det}</div>")).add_to(m)
            
            if ver_rep:
                try:
                    for _, r in reportes_publicos().iterrows(): folium.CircleMarker([r["lat"], r["lng"]], radius=6.5, color="#fff", weight=1.5, fill=True, fill_color="#ef4444" if r["tipo"] == "residuos" else "#22c55e", fill_opacity=1, tooltip=TIPOS.get(r["tipo"])).add_to(m)
                except: pass
                
            folium.LayerControl(collapsed=True).add_to(m); Fullscreen().add_to(m)
            st_folium(m, height=600, width=None, returned_objects=[])
            st.markdown('<div class="leyenda"></div>', unsafe_allow_html=True)
            st.caption("Barra de escala: Verde (Óptimo) a Rojo (Crítico). La zona palpitante requiere atención prioritaria.")

        with panel_col:
            with st.container(border=True):
                st.markdown("**Comparativa Local**")
                z = st.selectbox("Zona a inspeccionar", list(ZONAS), label_visibility="collapsed")
                if aire is not None:
                    st.metric("Temperatura del Aire", f"{aire.loc[z,'Temp (°C)']:.1f} °C", f"{aire.loc[z,'Temp (°C)']-aire['Temp (°C)'].mean():+.1f} °C vs media ciudad", delta_color="inverse")
                if pd.notna(info.loc[z, "LST (°C)"]): st.metric("Superficie LST", f"{info.loc[z,'LST (°C)']:.1f} °C", f"{info.loc[z,'LST (°C)']-info['LST (°C)'].mean():+.1f} °C vs ciudad", delta_color="inverse")
                if pd.notna(info.loc[z, "NDVI"]): st.metric("Índice Vegetal (NDVI)", f"{info.loc[z,'NDVI']:.2f}")
            
            st.markdown("**Top Temperatura Superficial**")
            t = df.copy(); t["LST (°C)"] = t["LST (°C)"].round(1)
            st.bar_chart(t.set_index("Zona")["LST (°C)"].sort_values(ascending=False), color="#ef4444", height=200)

        al = generar_alertas(info, aire, aq)
        st.markdown("### 🚨 Alertas y plan de siembra")
        if not al: st.success("Sin alertas activas con los datos actuales.")
        for nv, tit, z, dato, accion in al[:8]:
            col = {3: "#ef4444", 2: "#f59e0b"}[nv]
            st.markdown(f"<div style='border-left:6px solid {col};background:rgba(127,127,127,.08);padding:.7rem 1rem;border-radius:10px;margin:.4rem 0'><b>{tit} · {z}</b> <span style='opacity:.7'>({'Crítica' if nv == 3 else 'Alta'})</span><br>{dato}<br><i>{accion}</i></div>", unsafe_allow_html=True)
        pl = meta.get("plantar", [])
        if pl:
            dfp = pd.DataFrame([{"Prioridad": i + 1, "Zona": zona_cercana(la, lo), "NDVI": round(v, 2), "Superficie (°C)": round(tl, 1), "Mapa": f"https://www.google.com/maps?q={la:.5f},{lo:.5f}"} for i, (la, lo, v, tl) in enumerate(pl)])
            st.markdown("**📍 Sitios prioritarios para plantar** (vegetación muy baja y superficie caliente; los números amarillos del mapa)")
            st.dataframe(dfp, hide_index=True, width="stretch", column_config={"Mapa": st.column_config.LinkColumn("Ubicación", display_text="Abrir en Google Maps")})
            st.caption("Son puntos muestreados por satélite (30 m): pueden ser suelo desnudo, techos o vías. Verifica en campo y coordina con la autoridad ambiental antes de sembrar.")
            st.download_button("⬇️ Descargar plan de siembra (CSV)", dfp.to_csv(index=False), "plan_siembra_sombrabaq.csv", "text/csv")
    else:
        st.info(
            "La capa satelital no está disponible por ahora. Se muestra el mapa de Barranquilla "
            "con datos meteorológicos como alternativa.",
            icon=":material/satellite_alt:",
        )
        with st.expander("¿Por qué no se ve la capa satelital?"):
            st.markdown(
                "Las imágenes de vegetación y temperatura superficial requieren configurar "
                "Google Earth Engine. En Streamlit Cloud, agrega las credenciales de una cuenta "
                "de servicio autorizada bajo `[gee_service_account]` en **Manage app → Settings → Secrets**. "
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
    if not user: st.info("Inicia sesión en la barra lateral para registrar reportes ambientales y ganar puntos.")
    else:
        st.warning("Protege datos personales: no incluyas rostros, placas, documentos o ubicaciones privadas en la evidencia.", icon=":material/privacy_tip:")
        st.markdown("### 1. Selecciona la ubicación en el mapa")
        m2 = folium.Map(location=[10.97, -74.80], zoom_start=12)
        pin = st.session_state.get("pin")
        if pin: folium.Marker(pin, icon=folium.Icon(color="green", icon="leaf")).add_to(m2)
        out = st_folium(m2, height=350, width=None, returned_objects=["last_clicked"])
        if out and out.get("last_clicked"): pin = st.session_state.pin = [out["last_clicked"]["lat"], out["last_clicked"]["lng"]]
        st.caption("Haz clic exacto en el mapa donde realizaste la acción." if not pin else f"✅ Ubicación guardada: {pin[0]:.5f}, {pin[1]:.5f}")
        
        st.markdown("### 2. Evidencia y Validación Automática")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("¿Qué acción realizaste?", list(TIPOS), format_func=lambda k: f"{TIPOS[k]} (+{PUNTOS[k]} pts)")
            nota = c2.text_input("Mensaje para el Muro de la Comunidad (opcional)", max_chars=150)
            
            foto = st.camera_input("Toma la foto de tu aporte en vivo", help="También puedes subir una imagen desde tu galería.") or st.file_uploader("Imagen desde la galería", type=["jpg", "jpeg", "png"])
            
            if st.button("Analizar foto y publicar", icon=":material/auto_awesome:", type="primary", disabled=foto is None or not pin):
                datos = foto.getvalue()
                datos, error_evidencia = validar_evidencia(datos)
                if error_evidencia:
                    st.error(error_evidencia)
                    st.stop()
                with st.spinner("La Inteligencia Artificial está escaneando tu imagen y procesando tus puntos..."):
                    ia = analizar_foto(datos, tipo)
                    ok = ia["cumple"] and ia["confianza"] >= 0.5
                    st.session_state.ia = {**ia, "datos": datos, "tipo": tipo, "pin": pin, "nota": nota, "mime": foto.type or "image/jpeg"}
                    _publicar(st.session_state.sb, user, st.session_state.ia, ok, zona_cercana, reportes_publicos)
        
        if st.session_state.get("ia"):
            ia = st.session_state.ia
            st.markdown(f"**Análisis de la IA:** {ia['metodo']} detectó un nivel de confianza del `{ia['confianza']:.0%}`. *{ia['detalle']}*")

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
            else: st.info("Inicia sesión (o entra como invitado) para publicar.")
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
        st.subheader("Próximas actividades")
        with st.container(border=True):
            st.markdown("**Brigada de limpieza: Parque Suri Salcedo**")
            st.caption("Programación comunitaria · Próximamente")
            st.button("Inscripciones abiertas pronto", key="b1", width="stretch", disabled=True)
        with st.container(border=True):
            st.markdown("**Siembra masiva: Bulevar de Buenavista**")
            st.caption("Programación comunitaria · Próximamente")
            st.button("Inscripciones abiertas pronto", key="b2", width="stretch", disabled=True)
        st.caption("Las actividades se habilitarán cuando exista una convocatoria confirmada.")

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
                                codigo = st.session_state.sb.rpc("canjear", {"p_cupon": int(r.id)}).execute().data
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

    a1, a2, a3, a4, a5 = st.tabs(["Guía de plantas", "Separación de residuos", "Islas de calor", "Conceptos clave", "Mini evaluación"])
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
        st.markdown("#### Comprueba lo aprendido")
        q1 = st.radio("¿Qué dato suele indicar una superficie caliente?", ["NDVI alto", "LST alto", "UV bajo"], key="aprende_q1")
        q2 = st.radio("Antes de sembrar en una vía, debes:", ["Comprar rápido", "Confirmar especie y permisos", "Cubrir las raíces"], key="aprende_q2")
        q3 = st.radio("¿Cuál ayuda a reducir una isla de calor?", ["Más asfalto oscuro", "Más sombra y vegetación", "Menos drenaje"], key="aprende_q3")
        if st.button("Ver resultado", type="primary", key="aprende_resultado"):
            aciertos = sum([q1 == "LST alto", q2 == "Confirmar especie y permisos", q3 == "Más sombra y vegetación"])
            if aciertos == 3:
                st.success("Resultado perfecto: 3 de 3 respuestas correctas.")
                st.balloons()
            else:
                st.warning(f"Obtuviste {aciertos} de 3. Revisa las secciones y vuelve a intentarlo.")
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
