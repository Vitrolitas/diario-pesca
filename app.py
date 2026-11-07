import streamlit as st
import pandas as pd
import os
import datetime
import requests

# Configuración de la página
st.set_page_config(page_title="Diario de Eging & Clima Automático", page_icon="🦑", layout="wide")

DB_FILE = "diario_capturas_eging.csv"

def load_data():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            "Fecha", "Puerto", "Hora", "Marea", "Claridad Agua", 
            "Temp_Ambiente_C", "Temp_Agua_C", "Viento_Dir", "Viento_Vel_KmH", "Lluvia", 
            "Fase_Luna", "Resultado", "Marca_Egi", "Color_Egi", "Talla_Egi", "Notas"
        ])
        df.to_csv(DB_FILE, index=False)
    
    df = pd.read_csv(DB_FILE)
    
    # Normalizar automáticamente fechas antiguas o nuevas a formato DD/MM/YYYY
    if not df.empty and "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.strftime("%d/%m/%Y").fillna(df["Fecha"])
        
    return df

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Coordenadas geográficas exactas de tus puertos habituales
PUERTOS_COORDS = {
    "Puerto de Muros": {"lat": 42.775, "lon": -9.060},
    "Muros - Esteiro": {"lat": 42.792, "lon": -8.983},
    "Portosín (Porto do Son)": {"lat": 42.783, "lon": -8.933},
    "Porto do Son": {"lat": 42.738, "lon": -9.006},
    "Corcubión": {"lat": 42.946, "lon": -9.186},
    "Lira": {"lat": 42.778, "lon": -9.141},
    "Cee": {"lat": 42.956, "lon": -9.189}
}

def grados_a_rumbo(grados):
    if grados is None:
        return "Calma / Variable"
    direcciones = ["Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)"]
    index = int((grados + 22.5) / 45) % 8
    return direcciones[index]

def obtener_clima_open_meteo(puerto_nombre):
    coords = PUERTOS_COORDS.get(puerto_nombre, {"lat": 42.775, "lon": -9.060})
    
    url_atmosfera = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,precipitation,wind_speed_10m,wind_direction_10m"
    url_marina = f"https://marine-api.open-meteo.com/v1/marine?latitude={coords['lat']}&longitude={coords['lon']}&current=sea_surface_temperature"

    temp_amb = 15.0
    viento_vel = 10.0
    viento_dir_txt = "Norte (N)"
    lluvia_txt = "Despejado / Sin lluvia"
    temp_agua = 15.0

    try:
        resp_at = requests.get(url_atmosfera, timeout=5)
        if resp_at.status_code == 200:
            data_at = resp_at.json().get("current", {})
            temp_amb = float(data_at.get("temperature_2m", 15.0))
            viento_vel = float(data_at.get("wind_speed_10m", 10.0))
            viento_grados = data_at.get("wind_direction_10m", 0)
            precipitacion = data_at.get("precipitation", 0.0)
            
            if precipitacion == 0.0:
                lluvia_txt = "Despejado / Sin lluvia"
            elif precipitacion < 1.0:
                lluvia_txt = "Llovizna ligera"
            elif precipitacion < 5.0:
                lluvia_txt = "Lluvia moderada"
            else:
                lluvia_txt = "Lluvia intensa"
                
            viento_dir_txt = grados_a_rumbo(viento_grados)
    except Exception:
        pass

    try:
        resp_mar = requests.get(url_marina, timeout=5)
        if resp_mar.status_code == 200:
            data_mar = resp_mar.json().get("current", {})
            val_agua = data_mar.get("sea_surface_temperature")
            if val_agua is not None:
                temp_agua = float(val_agua)
    except Exception:
        pass

    return {
        "temp": temp_amb,
        "vel": viento_vel,
        "dir": viento_dir_txt,
        "lluvia": lluvia_txt,
        "temp_agua": temp_agua
    }

def obtener_fase_lunar(fecha_obj):
    ref_date = datetime.date(2000, 1, 6)
    days = (fecha_obj - ref_date).days
    cycle = 29.5305877
    lunar_age = (days % cycle)
    
    if lunar_age < 1.84: return "Luna Nueva"
    elif lunar_age < 5.54: return "Creciente cóncava"
    elif lunar_age < 9.23: return "Cuarto Creciente"
    elif lunar_age < 12.92: return "Gibosa creciente"
    elif lunar_age < 16.61: return "Luna Llena"
    elif lunar_age < 20.30: return "Gibosa menguante"
    elif lunar_age < 24.00: return "Cuarto Menguante"
    elif lunar_age < 27.68: return "Menguante cóncava"
    else: return "Luna Nueva"

df = load_data()

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.title("Menú Principal")
menu = st.sidebar.radio(
    "Selecciona una opción:", 
    ["Registrar Captura", "Ver Diario / Historial", "Asistente Histórico (Similitud)", "Gestión de Datos (CSV)"]
)

# --- VISTA 1: REGISTRAR CAPTURA ---
if menu == "Registrar Captura":
    st.title("Diario de Capturas Eging (Clima & Agua Automáticos)")
    st.markdown("---")

    st.subheader("Registrar Nueva Jornada")

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha de la salida", value=datetime.date.today())
        fase_lunar_calculada = obtener_fase_lunar(fecha)
        st.info(f"Fase lunar (Tablademareas): **{fase_lunar_calculada}**")

        puertos_tablademareas = list(PUERTOS_COORDS.keys())
        puerto = st.selectbox("Puerto / Pesquero", puertos_tablademareas)
        
        if "clima_actual" not in st.session_state:
            st.session_state.clima_actual = obtener_clima_open_meteo(puerto)

        if st.button("🌐 Cargar Clima y Temp. Agua de Open-Meteo"):
            st.session_state.clima_actual = obtener_clima_open_meteo(puerto)
            st.success(f"¡Datos meteorológicos y marinos actualizados para **{puerto}**!")

        clima = st.session_state.clima_actual

        hora_actual_str = datetime.datetime.now().strftime("%H:%M")
        hora_captura = st.text_input("Hora de la captura", value=hora_actual_str, placeholder="Ej: 20:30")

        marea = st.selectbox("Estado de la Marea", [
            "Subiendo (Primeras horas)", "Subiendo (A punto de pleamar)", "Pleamar exacta",
            "Bajando (Primeras horas)", "Bajando (A punto de bajamar)", "Bajamar exacta"
        ])
        claridad = st.selectbox("Claridad del Agua", ["Cristalina", "Ligeramente tomada", "Turbia / Oscura"])

    with col2:
        direcciones_viento = [
            "Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", 
            "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)", "Calma / Variable"
        ]
        
        try:
            default_viento_idx = direcciones_viento.index(clima["dir"])
        except ValueError:
            default_viento_idx = 0

        viento_dir = st.selectbox("Dirección del Viento (Open-Meteo)", direcciones_viento, index=default_viento_idx)