import streamlit as st
import pandas as pd
import os
import datetime

# Configuración de la página
st.set_page_config(page_title="Diario de Eging & Inteligencia de Pesca", page_icon="🦑", layout="wide")

DB_FILE = "diario_capturas_eging.csv"

def load_data():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            "Fecha", "Puerto", "Hora", "Marea", "Claridad Agua", 
            "Temp_Agua_C", "Viento_Dir", "Viento_Vel_KmH", "Lluvia", 
            "Fase_Luna", "Resultado", "Marca_Egi", "Color_Egi", "Talla_Egi", "Notas"
        ])
        df.to_csv(DB_FILE, index=False)
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Función matemática para calcular la fase lunar exacta (estándar tablademareas)
def obtener_fase_lunar(fecha_obj):
    ref_date = datetime.date(2000, 1, 6) # Fecha de referencia de Luna Nueva
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
st.sidebar.title("🦑 Menú Principal")
menu = st.sidebar.radio(
    "Selecciona una opción:", 
    ["Registrar Captura", "Ver Diario / Historial", "Asistente Histórico (Similitud)", "Gestión de Datos (CSV)"]
)

# --- VISTA 1: REGISTRAR CAPTURA ---
if menu == "Registrar Captura":
    st.title("🦑 Diario de Capturas Eging")
    st.markdown("---")

    st.subheader("📝 Registrar Nueva Jornada")

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha de la salida", value=datetime.date.today())
        
        # Calculamos la fase lunar automáticamente según la fecha
        fase_lunar_calculada = obtener_fase_lunar(fecha)
        st.info(f"🌙 Fase lunar (Tablademareas): **{fase_lunar_calculada}**")

        puertos_tablademareas = [
            "Puerto de Muros",
            "Muros - Esteiro",
            "Portosín (Porto do Son)",
            "Porto do Son",
            "Corcubión",
            "Lira",
            "Cee"
        ]
        puerto = st.selectbox("Puerto / Pesquero", puertos_tablademareas)
        
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
            "Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", 
            "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)", "Calma / Variable"
        ]
        viento_dir = st.selectbox("Dirección del Viento (Windy)", direcciones_viento)

        viento_vel = st.number_input(
            "Velocidad del Viento (km/h)", min_value=0.0, max_value=120.0, value=15.0, step=1.0
        )

        lluvia_estado = st.selectbox(
            "Previsión de Lluvia", ["Despejado / Sin lluvia", "Llovizna ligera", "Lluvia moderada", "Lluvia intensa"]
        )

        resultado_jornada = st.selectbox(
            "Resultado de la Pesca", 
            ["Éxito (Buenas capturas)", "Regular (Alguna pieza)", "Sin tocar escama (Blanco)"]
        )

        marca_egi = st.text_input("Marca del Egi", placeholder="Ej: Yamashita, DTD...")
        color_egi = st.text_input("Color / Acabado del Egi", placeholder="Ej: Rosa Glow, Natural Sardine...")
        talla_egi = st.selectbox("Tamaño del Egi", ["1.8", "2.0", "2.5", "3.0", "3.5", "Otros"])

    temp_agua = st.slider("Temp. Agua estimada (°C)", min_value=5.0, max_value=25.0, value=15.0, step=0.5)
    notas = st.text_area("Notas rápidas (Ej: Picó a fondo, tirón seco... Estado del mar)")

    if st.button("💾 ¡Guardar Captura en el Historial!"):
        # Captura automática de la hora actual exacta del sistema
        hora_exacta = datetime.datetime.now().strftime("%H:%M")

        nueva_captura = {
            "Fecha": str(fecha), 
            "Puerto": puerto, 
            "Hora": hora_exacta, 
            "Marea": marea,
            "Claridad Agua": claridad, 
            "Temp_Agua_C": temp_agua, 
            "Viento_Dir": viento_dir, 
            "Viento_Vel_KmH": viento_vel,
            "Lluvia": lluvia_estado,
            "Fase_Luna": fase_lunar_calculada,
            "Resultado": resultado_jornada,
            "Marca_Egi": marca_egi, 
            "Color_Egi": color_egi, 
            "Talla_Egi": talla_egi, 
            "Notas": notas
        }
        df = pd.concat([df, pd.DataFrame([nueva_captura])], ignore_index=True)
        save_data(df)
        st.success(f"🎉 ¡Jornada en **{puerto}** a las **{hora_exacta}** guardada correctamente!")

# --- VISTA 2: VER HISTORIAL ---
elif menu == "Ver Diario / Historial":
    st.title("📂 Historial de Capturas Guardadas")
    st.markdown("---")
    if df.empty:
        st.info("No hay capturas registradas todavía.")
    else:
        st.dataframe(df, use_container_width=True)

# --- VISTA 3: ASISTENTE INTELIGENTE BASADO EN HISTORIAL ---
elif menu == "Asistente Histórico (Similitud)":
    st.title("🧠 Inteligencia de Pesca: Coincidencias Históricas")
    st.markdown("---")
    st.write("Selecciona a qué puerto vas a ir hoy y las condiciones actuales para comprobar si ya pescaste antes en un escenario similar.")

    if df.empty:
        st.warning("Aún no tienes datos guardados en tu historial. Registra algunas salidas primero para que la app pueda comparar.")
    else:
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            puerto_busqueda = st.selectbox("Puerto de destino hoy", [
                "Puerto de Muros", "Muros - Esteiro", "Portosín (Porto do Son)", 
                "Porto do Son", "Corcubión", "Lira", "Cee"
            ])
            viento_busqueda = st.selectbox("Dirección de viento actual", [
                "Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", 
                "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)", "Calma / Variable"
            ])
        with col_h2:
            fase_hoy = obtener_fase_lunar(datetime.date.today())
            st.info(f"📅 Fecha de hoy: **{datetime.date.today()}**")
            st.info(f"🌙 Fase lunar actual calculada: **{fase_hoy}**")

        if st.button("🔍 Buscar coincidencias en mi historial"):
            coincidencias = df[(df["Puerto"] == puerto_busqueda) & (df["Viento_Dir"] == viento_busqueda)]
            
            if not coincidencias.empty:
                st.success(f"¡Encontradas **{len(coincidencias)} jornadas pasadas** en {puerto_busqueda} con viento {viento_busqueda}!")
                st.dataframe(coincidencias, use_container_width=True)
            else:
                coincidencias_puerto = df[df["Puerto"] == puerto_busqueda]
                if not coincidencias_puerto.empty:
                    st.info(f"No hay registros exactos con ese viento, pero sí tienes {len(coincidencias_puerto)} salidas previas en este puerto:")
                    st.dataframe(coincidencias_puerto, use_container_width=True)
                else:
                    st.warning(f"Todavía no tienes ningún registro guardado para el puerto de {puerto_busqueda}.")

# --- VISTA 4: GESTIÓN DE DATOS ---
elif menu == "Gestión de Datos (CSV)":
    st.title("⚙️ Mantenimiento de Datos")
    st.markdown("---")
    st.warning("Zona de restablecimiento: Si el archivo se corrompe o deseas vaciar el historial, puedes restablecerlo aquí.")
    if st.button("🗑️ Restablecer / Vaciar Base de Datos (CSV)"):
        df_vacio = pd.DataFrame(columns=[
            "Fecha", "Puerto", "Hora", "Marea", "Claridad Agua", 
            "Temp_Agua_C", "Viento_Dir", "Viento_Vel_KmH", "Lluvia", 
            "Fase_Luna", "Resultado", "Marca_Egi", "Color_Egi", "Talla_Egi", "Notas"
        ])
        save_data(df_vacio)
        st.success("¡Base de datos restablecida correctamente a cero!")

# --- ASISTENTE DE ABRIGO (SIEMPRE VISIBLE ABAJO) ---
st.markdown("---")
st.subheader("💡 Asistente de Selección de Puerto (Abrigo Geográfico)")

col_pred1, col_pred2 = st.columns(2)

with col_pred1:
    viento_consulta = st.selectbox(
        "Consultar abrigo rápido para viento:", 
        ["Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)"]
    )

with col_pred2:
    fuerza_viento = st.select_slider("Intensidad orientativa", options=["Flojo", "Moderado", "Fuerte"])

def recomendar_puerto(direccion):
    if "Norte" in direccion or "Nordeste" in direccion or "Noroeste" in direccion:
        return {
            "recomendados": ["Muros - Esteiro", "Puerto de Muros", "Corcubión", "Cee"],
            "motivo": "Los vientos del Norte/Nordeste quedan protegidos por el monte en Muros/Esteiro y al fondo de la ría en Corcubión/Cee."
        }
    elif "Sur" in direccion or "Suroeste" in direccion or "Sudeste" in direccion:
        return {
            "recomendados": ["Portosín (Porto do Son)", "Porto do Son"],
            "motivo": "La cara sur de la ría (Portosín y Porto do Son) queda perfectamente al resguardo de la Sierra del Barbanza con componente Sur."
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