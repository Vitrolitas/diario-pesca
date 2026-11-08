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
    
    # Normalizar automáticamente fechas a formato DD/MM/YYYY
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
        st.markdown("##### 📅 Fecha de la salida")
        hoy = datetime.date.today()
        
        c_d, c_m, c_a = st.columns(3)
        with c_d:
            dia_sel = st.selectbox("Día", list(range(1, 32)), index=hoy.day - 1)
        with c_m:
            meses_opciones = [
                "01 - Enero",
                "02 - Febrero",
                "03 - Marzo",
                "04 - Abril",
                "05 - Mayo",
                "06 - Junio",
                "07 - Julio",
                "08 - Agosto",
                "09 - Septiembre",
                "10 - Octubre",
                "11 - Noviembre",
                "12 - Diciembre"
            ]
            mes_str_sel = st.selectbox("Mes", meses_opciones, index=hoy.month - 1)
            mes_sel = int(mes_str_sel.split(" - ")[0])
        with c_a:
            ano_sel = st.selectbox("Año", [2024, 2025, 2026, 2027], index=2)
            
        try:
            fecha = datetime.date(ano_sel, mes_sel, dia_sel)
        except ValueError:
            st.warning("⚠️ Fecha no válida. Se ajustará automáticamente.")
            fecha = hoy

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
            "Fecha": fecha.strftime("%d/%m/%Y"), "Puerto": puerto, "Hora": hora_captura, "Marea": marea,
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

# --- VISTA 3: ASISTENTE INTELIGENTE MULTIVARIABLE Y VEREDICTO COMPLETO ---
elif menu == "Asistente Histórico (Similitud)":
    st.title("🧠 Asistente Histórico de Diagnóstico Total (Multivariable)")
    st.markdown("---")
    st.write("Configura **todas las variables previstas para hoy**. El asistente contrastará cada parámetro contra tu historial para emitir un diagnóstico de coincidencia y un veredicto de pesca ultra preciso.")

    if df.empty:
        st.warning("Aún no tienes jornadas guardadas en el diario. Registra salidas para activar el diagnóstico inteligente.")
    else:
        col_input1, col_input2 = st.columns(2)

        with col_input1:
            puerto_target = st.selectbox("Puerto de destino hoy", list(PUERTOS_COORDS.keys()))
            
            if "clima_asistente" not in st.session_state:
                st.session_state.clima_asistente = obtener_clima_open_meteo(puerto_target)

            if st.button("🌐 Cargar Clima Automático para el Diagnóstico"):
                st.session_state.clima_asistente = obtener_clima_open_meteo(puerto_target)
                st.success("¡Datos meteorológicos cargados para la simulación!")

            clima_asi = st.session_state.clima_asistente

            direcciones_viento = [
                "Norte (N)", "Nordeste (NE)", "Este (E)", "Sudeste (SE)", 
                "Sur (S)", "Suroeste (SW)", "Oeste (W)", "Noroeste (NW)", "Calma / Variable"
            ]
            try:
                def_v_idx = direcciones_viento.index(clima_asi["dir"])
            except ValueError:
                def_v_idx = 0

            viento_dir_target = st.selectbox("Dirección del viento prevista", direcciones_viento, index=def_v_idx)
            viento_vel_target = st.number_input("Velocidad del viento prevista (km/h)", min_value=0.0, max_value=120.0, value=clima_asi["vel"], step=1.0)
            
            marea_target = st.selectbox("Estado de la marea previsto", [
                "Subiendo (Primeras horas)", "Subiendo (A punto de pleamar)", "Pleamar exacta",
                "Bajando (Primeras horas)", "Bajando (A punto de bajamar)", "Bajamar exacta"
            ])

        with col_input2:
            fase_target = obtener_fase_lunar(datetime.date.today())
            st.info(f"🌙 Fase lunar actual calculada: **{fase_target}**")
            
            claridad_target = st.selectbox("Claridad estimada del agua", ["Cristalina", "Ligeramente tomada", "Turbia / Oscura"])
            
            opciones_lluvia = ["Despejado / Sin lluvia", "Llovizna ligera", "Lluvia moderada", "Lluvia intensa"]
            try:
                def_l_idx = opciones_lluvia.index(clima_asi["lluvia"])
            except ValueError:
                def_l_idx = 0
            lluvia_target = st.selectbox("Previsión de lluvia / cielo", opciones_lluvia, index=def_l_idx)

            temp_amb_target = st.number_input("Temp. ambiente estimada (°C)", min_value=-5.0, max_value=40.0, value=clima_asi["temp"], step=0.5)
            temp_agua_target = st.number_input("Temp. del agua estimada (°C)", min_value=5.0, max_value=25.0, value=clima_asi["temp_agua"], step=0.5)

        if st.button("🔍 Ejecutar Diagnóstico Multivariable Completo"):
            st.markdown("---")
            
            resultados_analisis = []

            for idx, row in df.iterrows():
                coincidencias = []
                diferencias = []
                puntos = 0

                # 1. Puerto (Peso: 25%)
                if str(row["Puerto"]) == puerto_target:
                    coincidencias.append("Puerto exacto")
                    puntos += 25
                else:
                    diferencias.append(f"Puerto ({row['Puerto']})")

                # 2. Viento Dirección (Peso: 15%)
                if str(row["Viento_Dir"]) == viento_dir_target:
                    coincidencias.append("Dirección viento")
                    puntos += 15
                else:
                    diferencias.append(f"Viento ({row['Viento_Dir']})")

                # 3. Viento Velocidad (+/- 10 km/h) (Peso: 10%)
                try:
                    vel_pasada = float(row["Viento_Vel_KmH"])
                    if abs(vel_pasada - viento_vel_target) <= 10.0:
                        coincidencias.append("Intensidad viento similar")
                        puntos += 10
                    else:
                        diferencias.append(f"Vel. viento ({vel_pasada} km/h)")
                except Exception:
                    pass

                # 4. Fase Lunar (Peso: 15%)
                if str(row["Fase_Luna"]) == fase_target:
                    coincidencias.append("Fase lunar")
                    puntos += 15
                else:
                    diferencias.append(f"Luna ({row['Fase_Luna']})")

                # 5. Marea (Peso: 10%)
                if str(row["Marea"]) == marea_target:
                    coincidencias.append("Marea")
                    puntos += 10
                else:
                    diferencias.append(f"Marea ({row['Marea']})")

                # 6. Claridad del Agua (Peso: 10%)
                if str(row["Claridad Agua"]) == claridad_target:
                    coincidencias.append("Claridad agua")
                    puntos += 10
                else:
                    diferencias.append(f"Agua ({row['Claridad Agua']})")

                # 7. Temperatura del Agua (+/- 1.5 °C) (Peso: 10%)
                try:
                    t_agua_pasada = float(row["Temp_Agua_C"])
                    if abs(t_agua_pasada - temp_agua_target) <= 1.5:
                        coincidencias.append("Temp. agua óptima")
                        puntos += 10
                    else:
                        diferencias.append(f"Temp. agua ({t_agua_pasada}°C)")
                except Exception:
                    pass

                # 8. Lluvia / Cielo (Peso: 5%)
                if str(row["Lluvia"]) == lluvia_target:
                    coincidencias.append("Cielo/Lluvia")
                    puntos += 5
                else:
                    diferencias.append(f"Cielo ({row['Lluvia']})")

                nota_texto = str(row["Notas"]) if pd.notna(row["Notas"]) else ""
                if len(nota_texto.strip()) > 2:
                    coincidencias.append("Incluye notas de experiencia")

                resultados_analisis.append({
                    "Fecha": row["Fecha"],
                    "Puerto": row["Puerto"],
                    "Resultado_Pieza": row["Resultado"],
                    "Marca_Egi": row["Marca_Egi"],
                    "Color_Egi": row["Color_Egi"],
                    "Talla_Egi": row["Talla_Egi"],
                    "Similitud_%": min(puntos, 100),
                    "Coincidencias": ", ".join(coincidencias) if coincidencias else "Ninguna",
                    "Diferencias": ", ".join(diferencias) if diferencias else "Ninguna",
                    "Notas": nota_texto
                })

            df_analisis = pd.DataFrame(resultados_analisis).sort_values(by="Similitud_%", ascending=False)
            
            st.subheader("📋 Tabla Comparativa de Diagnóstico Multivariable")
            st.dataframe(df_analisis[["Fecha", "Puerto", "Similitud_%", "Resultado_Pieza", "Marca_Egi", "Color_Egi", "Coincidencias", "Diferencias"]], use_container_width=True, hide_index=True)

            st.markdown("### ⚖️ Valoración Final y Veredicto Diagnóstico")
            
            top_coincidencia = df_analisis.iloc[0]
            max_similitud = top_coincidencia["Similitud_%"]

            if max_similitud >= 70:
                st.success(f"🎯 **DIAGNÓSTICO MUY FAVORABLE (Coincidencia global del {max_similitud}%)**")
                st.write(f"Las variables actuales encajan de forma muy sólida con tu jornada del **{top_coincidencia['Fecha']}** en **{puerto_target}**, donde obtuviste una captura de **{top_coincidencia['Resultado_Pieza']}**.")
                st.info(f"💡 **Recomendación de equipo:** Se aconseja utilizar el señuelo Egi **{top_coincidencia['Marca_Egi']}** en color **{top_coincidencia['Color_Egi']}** (Talla **{top_coincidencia['Talla_Egi']}**).")
            elif max_similitud >= 40:
                st.warning(f"⚠️ **DIAGNÓSTICO MODERADO (Coincidencia global del {max_similitud}%)**")
                st.write(f"Existen buenas coincidencias en factores clave, pero ten en cuenta las siguientes diferencias respecto a tu histórico: *{top_coincidencia['Diferencias']}*.")
                st.info(f"💡 **Sugerencia:** Puedes probar con el Egi **{top_coincidencia['Marca_Egi']}** ({top_coincidencia['Color_Egi']}), pero valora adaptar la técnica según el estado del mar.")
            else:
                st.error(f"❄️ **DIAGNÓSTICO BAJO / INCIERTO (Coincidencia máxima del {max_similitud}%)**")
                st.write(f"El escenario actual para {puerto_target} presenta demasiadas variables diferentes respecto a tus registros anteriores guardados.")

            if top_coincidencia["Notas"]:
                st.markdown(f"📝 **Nota rápida registrada en esa jornada de referencia ({top_coincidencia['Fecha']}):**")
                st.markdown(f"> {top_coincidencia['Notas']}")

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