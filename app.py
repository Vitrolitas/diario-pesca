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
        viento_vel = st.number_input("Velocidad del Viento (km/h)", min_value=0.0, max_value=120.0, value=clima["vel"], step=1.0)

        opciones_lluvia = ["Despejado / Sin lluvia", "Llovizna ligera", "Lluvia moderada", "Lluvia intensa"]
        try:
            default_lluvia_idx = opciones_lluvia.index(clima["lluvia"])
        except ValueError:
            default_lluvia_idx = 0

        lluvia_estado = st.selectbox("Previsión de Lluvia", opciones_lluvia, index=default_lluvia_idx)
        
        resultado_jornada = st.selectbox(
            "Resultado / Pieza Capturada", 
            ["Chipirón", "Calamar medio", "Calamar grande", "Sepia", "Choco", "Pulpo"]
        )

        marca_egi = st.text_input("Marca del Egi", placeholder="Ej: Yamashita, DTD...")
        color_egi = st.text_input("Color / Acabado del Egi", placeholder="Ej: Rosa Glow, Natural Sardine...")
        talla_egi = st.selectbox("Tamaño del Egi", ["1.8", "2.0", "2.5", "3.0", "3.5", "Otros"])

    st.markdown("### Registros Térmicos (Ambiente y Mar)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        temp_ambiente = st.slider("Temp. Ambiente / Exterior (°C) [Open-Meteo]", min_value=-5.0, max_value=40.0, value=clima["temp"], step=0.5)
    with col_t2:
        temp_agua = st.slider("Temp. Superficie del Agua (°C) [Open-Meteo Marine]", min_value=5.0, max_value=25.0, value=clima["temp_agua"], step=0.1)

    notas = st.text_area("Notas rápidas (Ej: Picó a fondo, tirón seco... Estado del mar)")

    if st.button("💾 ¡Guardar Captura en el Historial!"):
        nueva_captura = {
            "Fecha": str(fecha), "Puerto": puerto, "Hora": hora_captura, "Marea": marea,
            "Claridad Agua": claridad, "Temp_Ambiente_C": temp_ambiente, "Temp_Agua_C": temp_agua, 
            "Viento_Dir": viento_dir, "Viento_Vel_KmH": viento_vel, "Lluvia": lluvia_estado,
            "Fase_Luna": fase_lunar_calculada, "Resultado": resultado_jornada,
            "Marca_Egi": marca_egi, "Color_Egi": color_egi, "Talla_Egi": talla_egi, "Notas": notas
        }
        df = pd.concat([df, pd.DataFrame([nueva_captura])], ignore_index=True)
        save_data(df)
        st.success(f"🎉 ¡Captura de **{resultado_jornada}** guardada correctamente en el historial!")

# --- VISTA 2: VER HISTORIAL Y TOTALES ---
elif menu == "Ver Diario / Historial":
    st.title("📂 Historial y Estadísticas de Capturas")
    st.markdown("---")
    
    if df.empty:
        st.info("No hay capturas registradas todavía.")
    else:
        # --- PANEL DE RESUMEN Y TOTALES ---
        st.subheader("📊 Totales y Resumen de Capturas")
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.markdown("#### 🦑 Total por Especie / Tipo")
            conteo_especies = df["Resultado"].value_counts().reset_index()
            conteo_especies.columns = ["Especie / Pieza", "Cantidad Total"]
            st.dataframe(conteo_especies, use_container_width=True, hide_index=True)
            
        with col_m2:
            st.markdown("#### 📅 Total Diario (Capturas por Fecha)")
            conteo_diario = df["Fecha"].value_counts().reset_index()
            conteo_diario.columns = ["Fecha", "Piezas Capturadas"]
            conteo_diario = conteo_diario.sort_values(by="Fecha", ascending=False)
            st.dataframe(conteo_diario, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📋 Listado Completo de Registros")
        st.dataframe(df, use_container_width=True)

# --- VISTA 3: ASISTENTE INTELIGENTE BASADO EN HISTORIAL ---
elif menu == "Asistente Histórico (Similitud)":
    st.title("Inteligencia de Pesca: Coincidencias Históricas")
    st.markdown("---")
    st.write("Selecciona a qué puerto vas a ir hoy y las condiciones actuales para comprobar si ya pescaste antes en un escenario similar.")

    if df.empty:
        st.warning("Aún no tienes datos guardados en tu historial.")
    else:
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            puerto_busqueda = st.selectbox("Puerto de destino hoy", list(PUERTOS_COORDS.keys()))
            viento_busqueda = st.selectbox("Dirección de viento actual", [
                "Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", 
                "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)", "Calma / Variable"
            ])
        with col_h2:
            fase_hoy = obtener_fase_lunar(datetime.date.today())
            st.info(f"Fecha de hoy: **{datetime.date.today()}**")
            st.info(f"Fase lunar actual calculada: **{fase_hoy}**")

        if st.button("🔍 Buscar coincidencias en mi historial"):
            coincidencias = df[(df["Puerto"] == puerto_busqueda) & (df["Viento_Dir"] == viento_busqueda)]
            if not coincidencias.empty:
                st.success(f"¡Encontradas **{len(coincidencias)} jornadas pasadas** en {puerto_busqueda} con viento {viento_busqueda}!")
                st.dataframe(coincidencias, use_container_width=True)
            else:
                st.warning("No hay registros exactos con ese viento para este puerto.")

# --- VISTA 4: GESTIÓN DE DATOS ---
elif menu == "Gestión de Datos (CSV)":
    st.title("Mantenimiento de Datos")
    st.markdown("---")
    if st.button("🗑️ Restablecer / Vaciar Base de Datos (CSV)"):
        df_vacio = pd.DataFrame(columns=[
            "Fecha", "Puerto", "Hora", "Marea", "Claridad Agua", 
            "Temp_Ambiente_C", "Temp_Agua_C", "Viento_Dir", "Viento_Vel_KmH", "Lluvia", 
            "Fase_Luna", "Resultado", "Marca_Egi", "Color_Egi", "Talla_Egi", "Notas"
        ])
        save_data(df_vacio)
        st.success("¡Base de datos restablecida correctamente a cero!")