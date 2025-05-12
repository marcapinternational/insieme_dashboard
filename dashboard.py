# pylint: disable=import-error
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

# Configuración de la página (DEBE ser el primer comando de Streamlit)
st.set_page_config(page_title="Dashboard de Dólares ARS - INSIEME GROUP", layout="wide")

# Estilos CSS
st.markdown(
    """
    <style>
    .main {background: linear-gradient(to bottom, #F3F4F6, #E5E7EB);}
    .header {background-color: #1E3A8A; color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; font-family: 'Inter', sans-serif;}
    .header-date {font-size: 20px; font-weight: bold;}
    .header div:last-child {font-size: 24px; font-weight: bold;}
    .stMetric {background-color: #FFFFFF; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid;}
    .stMetric.blue {border-left-color: #1E3A8A;}
    .stMetric.oficial {border-left-color: #065F46;}
    .stMetric.mep {border-left-color: #F97316;}
    .stMetric.ccl {border-left-color: #6B21A8;}
    .stMetric.cripto {border-left-color: #06B6D4;}
    .stMetric.cheque {border-left-color: #3B82F6;}
    h1 {color: #1E3A8A; font-family: 'Inter', sans-serif;}
    h2, h3 {color: #374151; font-family: 'Inter', sans-serif;}
    .sidebar-note {font-size: 14px; color: #374151; font-family: 'Inter', sans-serif;}
    .bold-amount {font-weight: bold; font-size: 20px; color: #1E3A8A; margin-left: 10px;}
    .brecha {font-size: 24px; font-weight: bold; color: #065F46; margin: 10px 0;}
    .brecha-info {font-size: 14px; color: #374151; margin: 5px 0;}
    .cheque-item {margin-bottom: 10px; font-size: 16px; color: #374151;}
    .logo {text-align: center; margin-top: 20px;}
    .logo-ig {font-size: 48px; font-weight: bold; color: #1E3A8A;}
    .logo-text {font-size: 16px; color: #374151;}
    </style>
    """,
    unsafe_allow_html=True
)

# Estado para almacenar datos históricos y cheques
if "dollar_history" not in st.session_state:
    st.session_state.dollar_history = []
if "cheques_cartera" not in st.session_state:
    st.session_state.cheques_cartera = 0  # Solo monto
if "cheques_depositados" not in st.session_state:
    st.session_state.cheques_depositados = []
if "last_update" not in st.session_state:
    st.session_state.last_update = 0

# Función para crear una sesión con reintentos
def create_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# Función para obtener precios desde DolarAPI (principal)
@st.cache_data
def get_dollar_prices(_timestamp):
    url = "https://dolarapi.com/v1/dolares"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    session = create_session()
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = {
            "Dólar Blue": {"Compra": None, "Venta": None},
            "Dólar Oficial": {"Compra": None, "Venta": None},
            "Dólar MEP": {"Compra": None, "Venta": None},
            "Dólar CCL": {"Compra": None, "Venta": None},
            "Dólar Cripto": {"Compra": None, "Venta": None},
        }

        for item in data:
            if item["casa"] == "blue":
                prices["Dólar Blue"] = {"Compra": item["compra"], "Venta": item["venta"]}
            elif item["casa"] == "oficial":
                prices["Dólar Oficial"] = {"Compra": item["compra"], "Venta": item["venta"]}
            elif item["casa"] == "bolsa":
                prices["Dólar MEP"] = {"Compra": item["compra"], "Venta": item["venta"]}
            elif item["casa"] == "contadoconliqui":
                prices["Dólar CCL"] = {"Compra": item["compra"], "Venta": item["venta"]}
            elif item["casa"] == "cripto":
                prices["Dólar Cripto"] = {"Compra": item["compra"], "Venta": item["venta"]}

        return prices
    except Exception as e:
        st.warning(f"Error al obtener datos de DolarAPI: {e}. Intentando con CriptoYa...")
        return get_dollar_prices_fallback()

# Función de respaldo con CriptoYa
@st.cache_data
def get_dollar_prices_fallback(_timestamp):
    url = "https://api.criptoya.com/v1/ar/dolar"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    session = create_session()
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = {
            "Dólar Blue": {"Compra": None, "Venta": None},
            "Dólar Oficial": {"Compra": None, "Venta": None},
            "Dólar MEP": {"Compra": None, "Venta": None},
            "Dólar CCL": {"Compra": None, "Venta": None},
            "Dólar Cripto": {"Compra": None, "Venta": None},
        }

        for dollar_type, values in data.items():
            if dollar_type == "blue":
                prices["Dólar Blue"] = {"Compra": values["bid"], "Venta": values["ask"]}
            elif dollar_type == "oficial":
                prices["Dólar Oficial"] = {"Compra": values["bid"], "Venta": values["ask"]}
            elif dollar_type == "mep":
                prices["Dólar MEP"] = {"Compra": values["bid"], "Venta": values["ask"]}
            elif dollar_type == "ccl":
                prices["Dólar CCL"] = {"Compra": values["bid"], "Venta": values["ask"]}
            elif dollar_type == "cripto":
                prices["Dólar Cripto"] = {"Compra": values["bid"], "Venta": values["ask"]}

        return prices
    except Exception as e:
        st.error(f"Error al obtener datos de CriptoYa: {e}")
        return None

# Obtener precios y almacenar en el historial
current_time = time.time()
if current_time - st.session_state.last_update >= 60:  # Actualizar cada 60 segundos
    prices = get_dollar_prices(current_time)
    if prices:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.dollar_history.append({
            "timestamp": timestamp,
            "Dólar Blue": prices["Dólar Blue"]["Venta"],
            "Dólar Oficial": prices["Dólar Oficial"]["Venta"],
            "Dólar MEP": prices["Dólar MEP"]["Venta"],
            "Dólar CCL": prices["Dólar CCL"]["Venta"],
            "Dólar Cripto": prices["Dólar Cripto"]["Venta"],
        })
        # Limitar el historial a las últimas 100 entradas
        st.session_state.dollar_history = st.session_state.dollar_history[-100:]
        st.session_state.last_update = current_time
else:
    prices = get_dollar_prices(st.session_state.last_update)  # Usar caché

# Mostrar encabezado con fecha y hora
fecha = datetime.now().strftime("%d/%m/%Y")
hora = datetime.fromtimestamp(st.session_state.last_update).strftime("%H:%M:%S") if st.session_state.last_update else "No actualizado"
st.markdown(
    f"""
    <div class="header">
        <div class="header-date">{fecha}<br>Última actualización: {hora}</div>
        <div>INSIEME GROUP</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Mostrar precios actuales
st.subheader("Precios Actuales (ARS)")
if prices:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="stMetric blue">', unsafe_allow_html=True)
        st.metric(
            label="Dólar Blue",
            value=f"Venta: ${prices['Dólar Blue']['Venta']:.2f}",
            delta=f"Compra: ${prices['Dólar Blue']['Compra']:.2f}",
            delta_color="off"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stMetric oficial">', unsafe_allow_html=True)
        st.metric(
            label="Dólar Oficial",
            value=f"Venta: ${prices['Dólar Oficial']['Venta']:.2f}",
            delta=f"Compra: ${prices['Dólar Oficial']['Compra']:.2f}",
            delta_color="off"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stMetric mep">', unsafe_allow_html=True)
        st.metric(
            label="Dólar MEP",
            value=f"Venta: ${prices['Dólar MEP']['Venta']:.2f}",
            delta=f"Compra: ${prices['Dólar MEP']['Compra']:.2f}",
            delta_color="off"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="stMetric ccl">', unsafe_allow_html=True)
        st.metric(
            label="Dólar CCL",
            value=f"Venta: ${prices['Dólar CCL']['Venta']:.2f}",
            delta=f"Compra: ${prices['Dólar CCL']['Compra']:.2f}",
            delta_color="off"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="stMetric cripto">', unsafe_allow_html=True)
        st.metric(
            label="Dólar Cripto",
            value=f"Venta: ${prices['Dólar Cripto']['Venta']:.2f}",
            delta=f"Compra: ${prices['Dólar Cripto']['Compra']:.2f}",
            delta_color="off"
        )
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.error("No se pudieron cargar los datos. Verifica tu conexión o intenta de nuevo.")

# Gráfico comparativo
st.subheader("Evolución de Precios de Venta (ARS)")
if st.session_state.dollar_history:
    df = pd.DataFrame(st.session_state.dollar_history)
    fig = go.Figure()
    colors = ["#1E3A8A", "#065F46", "#F97316", "#6B21A8", "#06B6D4"]
    for i, dollar in enumerate(["Dólar Blue", "Dólar Oficial", "Dólar MEP", "Dólar CCL", "Dólar Cripto"]):
        # Mostrar solo el último punto con el nombre
        text = [""] * (len(df) - 1) + [dollar]  # Nombre solo en el último punto
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df[dollar],
                mode="lines+markers+text",
                name=dollar,
                line=dict(color=colors[i], width=2),
                marker=dict(size=8),
                text=text,
                textposition="middle right",
                textfont=dict(size=12, color=colors[i]),
            )
        )
    fig.update_layout(
        title="Evolución de Precios de Venta (ARS)",
        xaxis_title="Tiempo",
        yaxis_title="Precio de Venta (ARS)",
        font=dict(family="Inter, sans-serif", size=14, color="#374151"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#F3F4F6",
        showlegend=True,
        margin=dict(l=40, r=80, t=60, b=40),  # Aumentar margen derecho para los nombres
        title_x=0.5,
        xaxis_tickangle=45,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Esperando datos para el gráfico...")

# Sección de cheques
total_cartera = st.session_state.cheques_cartera
total_depositados = sum(cheque["monto"] for cheque in st.session_state.cheques_depositados) if st.session_state.cheques_depositados else 0
total_general = total_cartera - total_depositados  # Total General = Cartera - Depositados

st.markdown(
    f"<h2>Gestión de Cheques - INSIEME GROUP <span class='bold-amount'>${total_general:,}</span></h2>",
    unsafe_allow_html=True
)
with st.expander("Actualizar Cartera de Cheques"):
    with st.form("cheques_cartera_form"):
        monto = st.number_input("Monto total de la cartera (ARS)", min_value=0, step=1000, value=st.session_state.cheques_cartera)
        submitted = st.form_submit_button("Actualizar Cartera")
        if submitted:
            st.session_state.cheques_cartera = monto  # Reemplaza el valor anterior
            st.session_state.last_update = time.time()  # Forzar actualización
            st.success("Cartera de cheques actualizada.")
            st.rerun()  # Forzar re-renderización inmediata

with st.expander("Actualizar Cheques Depositados"):
    with st.form("cheques_depositados_form"):
        nombre = st.text_input("Nombre del cheque")
        monto_cheque = st.number_input("Monto del cheque (ARS)", min_value=0, step=1000)
        submitted = st.form_submit_button("Agregar Cheque")
        if submitted and nombre and monto_cheque:
            st.session_state.cheques_depositados.append({"nombre": nombre, "monto": monto_cheque})
            st.session_state.last_update = time.time()  # Forzar actualización
            st.success(f"Cheque '{nombre}' agregado.")
            st.rerun()  # Forzar re-renderización inmediata

# Mostrar datos de cheques
if st.session_state.cheques_cartera or st.session_state.cheques_depositados:
    st.markdown(
        f"<h3>Cartera de Cheques <span class='bold-amount'>${total_cartera:,}</span></h3>",
        unsafe_allow_html=True
    )
    st.markdown('<div class="stMetric cheque">', unsafe_allow_html=True)
    st.metric(
        label="Cartera de Cheques",
        value=f"Monto: ${st.session_state.cheques_cartera:,}",
        delta=None,  # Sin cantidad de cheques
        delta_color="off"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.cheques_depositados:
        st.markdown(
            f"<h3>Cheques Depositados <span class='bold-amount'>${total_depositados:,}</span></h3>",
            unsafe_allow_html=True
        )
        for i, cheque in enumerate(st.session_state.cheques_depositados):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"<div class='cheque-item'>{cheque['nombre']}: ${cheque['monto']:,}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("Eliminar", key=f"delete_cheque_{i}"):
                    st.session_state.cheques_depositados.pop(i)
                    st.session_state.last_update = time.time()  # Forzar actualización
                    st.success(f"Cheque '{cheque['nombre']}' eliminado.")
                    st.rerun()  # Forzar re-renderización inmediata

    st.markdown(
        f"<h3>Total General (ARS) <span class='bold-amount'>${total_general:,}</span></h3>",
        unsafe_allow_html=True
    )
    st.markdown('<div class="stMetric cheque">', unsafe_allow_html=True)
    st.metric(
        label="Total General (ARS)",
        value=f"${total_general:,}",
        delta="Cartera - Depositados",
        delta_color="off"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Resumen financiero en la barra lateral
with st.sidebar:
    with st.expander("Resumen Financiero"):
        # Mostrar "HAY BRECHA" y detalles si Dólar Cripto < Dólar Blue
        if prices and prices["Dólar Cripto"]["Venta"] and prices["Dólar Blue"]["Venta"] and prices["Dólar Cripto"]["Venta"] < prices["Dólar Blue"]["Venta"]:
            spread = prices["Dólar Blue"]["Venta"] - prices["Dólar Cripto"]["Venta"]
            porcentaje = (spread / prices["Dólar Blue"]["Venta"]) * 100
            st.markdown(
                "<div class='brecha'>HAY BRECHA</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='brecha-info'>Spread: ${spread:,.2f}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='brecha-info'>Porcentaje: {porcentaje:.2f}%</div>",
                unsafe_allow_html=True
            )
        st.markdown(
            f"<div class='sidebar-note'>Cartera: <span class='bold-amount'>${total_cartera:,}</span></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='sidebar-note'>Depositados: <span class='bold-amount'>${total_depositados:,}</span></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='sidebar-note'>Total General: <span class='bold-amount'>${total_general:,}</span></div>",
            unsafe_allow_html=True
        )
    # Logo "IG"
    st.markdown(
        """
        <div class="logo">
            <div class="logo-ig">IG</div>
            <div class="logo-text">Insieme Group</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Actualización automática cada 60 segundos
if current_time - st.session_state.last_update >= 60:
    st.session_state.last_update = current_time
    time.sleep(1)  # Breve pausa para evitar sobrecarga
    st.rerun()