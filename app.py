import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Diario de Eging & Asistente", page_icon="🦑", layout="wide")

DB_FILE = "diario_capturas_eging.csv"

def load_data():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            "Fecha", "Puerto", "Hora", "Marea", "Claridad Agua", 
            "Temp_Agua_C", "Viento_Dir", "Viento_Vel_KmH", "Lluvia", 
            "Fase_Luna", "Marca_Egi", "Color_Egi", "Talla_Egi", "Notas"
        ])
        df.to_csv(DB_FILE, index=False)
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.title("🦑 Menú Principal")
menu = st.sidebar.radio("Ir a:", ["Registrar Captura", "Ver Diario / Historial"])

# --- VISTA 1: REGISTRAR CAPTURA ---
if menu == "Registrar Captura":
    st.title("🦑 Diario de Capturas Eging")
    st.markdown("---")

    st.subheader("📝 Registrar Nueva Captura")

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha de la salida")
        
        puertos_tablademareas = [
            "Puerto de Muros",
            "Muros - Esteiro",
            "Portosín (Porto do Son)",
            "Porto do Son",
            "Corcubión",
            "Lira",
            "Cee"
        ]
        puerto = st.selectbox("Puerto / Pesquero (Tablademareas)", puertos_tablademareas)
        
        hora = st.text_input("Hora aproximada", placeholder="Ej: 20:30")
        marea = st.selectbox("Estado de la Marea", [
            "Subiendo (Primeras horas)",
            "Subiendo (A punto de pleamar)",
            "Pleamar exacta",
            "Bajando (Primeras horas)",
            "Bajando (A punto de bajamar)",
            "Bajamar exacta"
        ])
        claridad = st.selectbox("Claridad del Agua", ["Cristalina", "Ligeramente tomada", "Turbia / Oscura"])

    with col2:
        direcciones_viento = [
            "Norte (N)", 
            "Nordeste (NE)", 
            "Este (E)", 
            "Sudeste (SE)", 
            "Sur (S)", 
            "Suroeste (SW)", 
            "Oeste (W)", 
            "Noroeste (NW)",
            "Calma / Variable"
        ]
        viento_dir = st.selectbox("Dirección del Viento (Windy)", direcciones_viento)

        viento_vel = st.number_input(
            "Velocidad del Viento (km/h)", 
            min_value=0.0, 
            max_value=120.0, 
            value=15.0, 
            step=1.0,
            help="Introduce los km/h que marca Windy para la hora de la pesca."
        )

        lluvia_estado = st.selectbox(
            "Previsión de Lluvia (Windy)",
            ["Despejado / Sin lluvia", "Llovizna ligera", "Lluvia moderada", "Lluvia intensa / Chubascos"]
        )

        marca_egi = st.text_input("Marca del Egi", placeholder="Ej: Yamashita, DTD...")
        color_egi = st.text_input("Color / Acabado del Egi", placeholder="Ej: Rosa Glow, Natural Sardine...")
        talla_egi = st.selectbox("Tamaño del Egi", ["1.8", "2.0", "2.5", "3.0", "3.5", "Otros"])

    temp_agua = st.slider("Temp. Agua estimada (°C)", min_value=5.0, max_value=25.0, value=15.0, step=0.5)
    notas = st.text_area("Notas rápidas (Ej: Picó a fondo, tirón seco... Estado del mar)")

    if st.button("💾 ¡Guardar Captura!"):
        nueva_captura = {
            "Fecha": str(fecha), 
            "Puerto": puerto, 
            "Hora": hora, 
            "Marea": marea,
            "Claridad Agua": claridad, 
            "Temp_Agua_C": temp_agua, 
            "Viento_Dir": viento_dir, 
            "Viento_Vel_KmH": viento_vel,
            "Lluvia": lluvia_estado,
            "Fase_Luna": "Creciente",
            "Marca_Egi": marca_egi, 
            "Color_Egi": color_egi, 
            "Talla_Egi": talla_egi, 
            "Notas": notas
        }
        df = pd.concat([df, pd.DataFrame([nueva_captura])], ignore_index=True)
        save_data(df)
        st.success(f"🎉 ¡Captura con señuelo **{marca_egi}** guardada con éxito!")

# --- VISTA 2: VER HISTORIAL ---
elif menu == "Ver Diario / Historial":
    st.title("📂 Historial de Capturas Guardadas")
    st.markdown("---")
    if df.empty:
        st.info("No hay capturas registradas todavía.")
    else:
        st.dataframe(df, use_container_width=True)

# --- ASISTENTE DE ABRIGO (SIEMPRE VISIBLE ABAJO) ---
st.markdown("---")
st.subheader("💡 Asistente de Selección de Puerto (Abrigo)")

col_pred1, col_pred2 = st.columns(2)

with col_pred1:
    viento_consulta = st.selectbox(
        "Dirección del viento actual (para consultar abrigo)", 
        ["Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)"]
    )

with col_pred2:
    fuerza_viento = st.select_slider("Intensidad del viento", options=["Flojo", "Moderado", "Fuerte"])

def recomendar_puerto(direccion):
    if "Norte" in direccion or "Nordeste" in direccion or "Noroeste" in direccion:
        return {
            "recomendados": ["Muros - Esteiro", "Puerto de Muros", "Corcubión", "Cee"],
            "motivo": "Los vientos del Norte y Nordeste quedan protegidos por el monte en Muros/Esteiro y al fondo de la ría en Corcubión/Cee."
        }
    elif "Sur" in direccion or "Suroeste" in direccion or "Sudeste" in direccion:
        return {
            "recomendados": ["Portosín (Porto do Son)", "Porto do Son"],
            "motivo": "La cara sur de la ría (Portosín y Porto do Son) queda perfectamente al resguardo de la Sierra del Barbanza con vientos de componente Sur."
        }
    elif "Este" in direccion:
        return {
            "recomendados": ["Lira", "Puerto de Muros", "Portosín (Porto do Son)"],
            "motivo": "Con viento de Este (tierra a mar), el agua se mantiene bastante plana y pescable en casi todas las dársenas."
        }
    else: 
        return {
            "recomendados": ["Muros - Esteiro", "Cee"],
            "motivo": "Con viento directo de mar abierto (Oeste), los spots más resguardados son los ubicados al fondo de las rías."
        }

res = recomendar_puerto(viento_consulta)

st.success(f"📌 **Puertos más abrigados recomendados:** {', '.join(res['recomendados'])}")
st.info(f"ℹ️ **Razón técnica:** {res['motivo']}")