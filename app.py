import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import os

st.set_page_config(page_title="Diario y Predictor de Eging Pro", page_icon="🦑", layout="wide")

DB_FILE = "diario_capturas_eging.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=[
            "Fecha", "Puerto", "Hora", "Marea", "Claridad_Agua", 
            "Temp_Agua_C", "Viento_Dir", "Fase_Luna", "Marca_Egi", "Color_Egi", "Talla_Egi", "Notas"
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

st.title("🦑 Diario Pro & Predictor de Calamar (Eging)")

opcion = st.sidebar.radio("Navegación", [
    "🎯 ¡Registrar Captura!", 
    "📝 Registrar Jornada sin éxito (Bolos)", 
    "🔮 Predictor por Puerto", 
    "📊 Estadísticas de Señuelos y Artesanos"
])

if opcion == "🎯 ¡Registrar Captura!":
    st.header("🎯 ¡Tengo un Calamar!")
    st.caption("Apunta los datos de esta pieza y el origen exacto del señuelo.")
    
    hora_actual = datetime.now().strftime("%H:%M")
    fecha_actual = datetime.now().date()

    with st.form("form_captura", clear_on_submit=True):
    	col1, col2 = st.columns(2)
    
    with col1:
        # Listado completo de puertos orientado a tablademareas.com
        puertos_tablademareas = [
            "Puerto de Muros", 
            "Portosín (Porto do Son)", 
            "Lira", 
            "Camariñas", 
            "Fisterra", 
            "Muxía", 
            "Porto do Son",
            "Noia",
            "Corcubión",
            "Muros - Esteiro"
        ]
        puerto = st.selectbox("Puerto / Pesquero (Tablademareas)", puertos_tablademareas)
        
        fecha = st.date_input("Fecha", fecha_actual, format="DD/MM/YYYY")
        hora = st.text_input("Hora exacta de la picada", value=hora_actual)
        
        # Estado detallado de la marea
        marea_estado = st.selectbox(
            "Estado de la Marea (Tablademareas)", 
            [
                "Subiendo (Primeras horas)", 
                "Subiendo (A punto de pleamar)", 
                "Pleamar exacta", 
                "Bajando (Primeras horas)", 
                "Bajando (A punto de bajamar)", 
                "Bajamar exacta"
            ]
        )
        
        claridad = st.selectbox("Claridad del Agua", ["Cristalina", "Ligeramente tomada", "Turbia / Oscura"])

    with col2:
        # Datos meteorológicos extraídos de Windy
        direcciones_viento = ["Calma", "Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)"]
        viento_dir = st.selectbox("Dirección del Viento (Windy)", direcciones_viento)
        
        viento_vel = st.slider("Velocidad del Viento (nudos / km/h)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
        
        lluvia_estado = st.selectbox(
            "Previsión de Lluvia (Windy)", 
            ["Despejado / Sin lluvia", "Llovizna ligera", "Lluvia moderada", "Lluvia intensa / Chubascos"]
        )
        
        marca_egi = st.text_input("Marca / Artesano del Egi", placeholder="Ej: Yamashita, DTD...")
        color_egi = st.text_input("Color / Acabado del Egi", placeholder="Ej: Rosa Glow, Natural Sardine...")
        talla_egi = st.selectbox("Tamaño del Egi", ["1.8", "2.0", "2.5", "3.0", "3.5", "Otros"])

    temp_agua = st.slider("Temp. Agua estimada (°C)", min_value=5.0, max_value=25.0, value=15.0, step=0.5)
    notas = st.text_area("Notas rápidas (Ej: Picó a fondo, tirón seco... Estado del mar)")

    submitted = st.form_submit_button("💾 ¡Guardar Captura!")
        
if submitted:
            nueva_captura = {
                "Fecha": fecha, "Puerto": puerto, "Hora": hora, "Marea": marea,
                "Claridad_Agua": claridad, "Temp_Agua_C": temp_agua,
                "Viento_Dir": viento_dir, "Fase_Luna": "Creciente",
                "Marca_Egi": marca_egi, "Color_Egi": color_egi, "Talla_Egi": talla_egi, "Notas": notas
            }
            df = pd.concat([df, pd.DataFrame([nueva_captura])], ignore_index=True)
            save_data(df)
            st.success(f"🎉 ¡Captura con señuelo **{marca_egi}** guardada con éxito!")

elif opcion == "📝 Registrar Jornada sin éxito (Bolos)":
    st.header("📝 Registrar salida sin capturas (Bolos)")
    with st.form("form_bolo"):
        fecha_bolo = st.date_input("Fecha del bolo", datetime.now().date())
        puerto_bolo = st.text_input("Puerto", value="Puerto de Muros")
        motivo = st.text_area("Observaciones del día (Mucho mar de fondo, agua sucia...)")
        if st.form_submit_button("Guardar Jornada en Blanco"):
            st.info("Bolo guardado correctamente.")

elif opcion == "🔮 Predictor por Puerto":
    st.header("🔮 Asistente Predictivo")
    if df.empty:
        st.warning("⚠️ Necesitas registrar algunas capturas para ver recomendaciones.")
    else:
        puerto_sel = st.selectbox("Selecciona tu destino:", df["Puerto"].unique().tolist())
        df_p = df[df["Puerto"] == puerto_sel]
        if not df_p.empty:
            st.subheader(f"🎯 Marcas y Artesanos más efectivos en {puerto_sel}:")
            conteo_marcas = df_p["Marca_Egi"].value_counts()
            st.bar_chart(conteo_marcas)

elif opcion == "📊 Estadísticas de Señuelos y Artesanos":
    st.header("📊 Análisis Global de Marcas y Diseños")
    if df.empty:
        st.info("Aún no hay datos guardados.")
    else:
        st.dataframe(df)
        st.subheader("Eficacia por Marca o Creador")
        fig = px.histogram(df, x="Marca_Egi", color="Puerto", title="Capturas conseguidas por cada Fabricante / Artesano")
        st.plotly_chart(fig, use_container_width=True)