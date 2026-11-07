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
    return pd.read_csv(DB_FILE)

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
        resp_mar = requests.get