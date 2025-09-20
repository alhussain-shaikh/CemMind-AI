import os
import sys
import uuid
import time
import graphviz
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
import asyncio

# Project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Imports
from simulation.batch_generator import generate_data, upload_to_gcs
from services.cloud.bigquery_client import load_csv_from_gcs, query_sample
from google.genai import types
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

# ---------------- Environment ----------------
load_dotenv()
PROJECT = os.getenv("PROJECT")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_DEST_PREFIX = os.getenv("GCS_DEST_PREFIX")
LOCAL_CSV = os.getenv("LOCAL_CSV")
VERTEX_AGENT = os.getenv("VERTEX_AGENT")
REGION = "us-central1"

# ---------------- Utility Functions ----------------
def analyze_plant(latest_data: dict) -> dict:
    """Analyze cement plant data and return suggestions + stage severities."""
    kiln_temp = latest_data.get("kiln_temp_C")
    mill_power = latest_data.get("mill_power_kW")
    af_rate = latest_data.get("AF_rate_percent")
    free_lime = latest_data.get("clinker_free_lime_percent")
    co2 = latest_data.get("CO2_emission_kgpt")

    report = (
        f"Kiln Temp: {kiln_temp}°C\n"
        f"Mill Power: {mill_power} kW\n"
        f"AF Rate: {af_rate}%\n"
        f"Free Lime: {free_lime}%\n"
        f"CO₂ Emission: {co2} kg/ton\n"
    )

    suggestions = []
    severity = {stage: "normal" for stage in ["Raw", "Preheat", "Clinker", "Grind", "Sustain"]}

    # Kiln temp
    if kiln_temp > 1500:
        suggestions.append("🔥 Kiln temperature is critical! Reduce fuel immediately.")
        severity["Preheat"] = "critical"
    elif kiln_temp > 1450:
        suggestions.append("⚠️ Kiln temperature is high, monitor fuel closely.")
        severity["Preheat"] = "warning"

    # AF rate
    if af_rate < 3:
        suggestions.append("Critical low AF rate; sustainability compromised.")
        severity["Sustain"] = "critical"
    elif af_rate < 5:
        suggestions.append("Increase alternative fuel rate to improve sustainability.")
        severity["Sustain"] = "warning"

    # Free lime
    if free_lime > 4:
        suggestions.append("Clinker free lime is critically high; poor quality risk.")
        severity["Clinker"] = "critical"
    elif free_lime > 2.5:
        suggestions.append("Free lime is high; adjust kiln process.")
        severity["Clinker"] = "warning"

    # CO₂
    if co2 > 1000:
        suggestions.append("Critical CO₂ emissions; energy optimization needed.")
        severity["Sustain"] = "critical"
    elif co2 > 800:
        suggestions.append("High CO₂ emission; consider process efficiency improvements.")
        severity["Sustain"] = "warning"

    # Mill power
    if mill_power > 6000:
        suggestions.append("Critical grinding load; immediate action required.")
        severity["Grind"] = "critical"
    elif mill_power > 5000:
        suggestions.append("Mill power is high; check grinding efficiency.")
        severity["Grind"] = "warning"

    return {
        "text": report + ("\n".join(suggestions) if suggestions else "\nAll metrics within normal range."),
        "severity": severity
    }

def render_process_diagram(severity: dict):
    """Render cement process flow with color-coded severities."""
    process = graphviz.Digraph()
    process.attr(rankdir="LR", size="8,5")
    process.attr("node", shape="box", style="rounded,filled")

    color_map = {
        "normal": "palegreen",
        "warning": "gold",
        "critical": "lightcoral"
    }

    # Helper to add node with severity color
    def node(name, label):
        level = severity.get(name, "normal")
        process.node(name, label, fillcolor=color_map.get(level, "lightgrey"))

    node("Raw", "🪨 Raw Material Prep\n(Mill Power kW)")
    node("Preheat", "🔥 Preheating & Calcination\n(Kiln Temp °C)")
    node("Clinker", "🧱 Clinker Formation\n(Free Lime %)")
    node("Grind", "⚙️ Grinding & Cooling\n(Mill Power kW)")
    node("Sustain", "🌿 Sustainability\n(AF Rate %, CO₂)")

    process.edges([("Raw","Preheat"), ("Preheat","Clinker"), ("Clinker","Grind"), ("Grind","Sustain")])
    return process

# Example usage
result = analyze_plant({
    "kiln_temp_C": 1475,
    "mill_power_kW": 5100,
    "AF_rate_percent": 4,
    "clinker_free_lime_percent": 3,
    "CO2_emission_kgpt": 900
})


@st.cache_data
def load_historical(limit=200):
    df = query_sample(PROJECT, DATASET, TABLE)
    return df.tail(limit)

# ---------------- Vertex AI Agent ----------------
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    )
]

generate_content_config = types.GenerateContentConfig(
    safety_settings=safety_settings,
    temperature=0.28,
    max_output_tokens=1000,
    top_p=0.95,
)

cemmind_agent = Agent(
    name="cemmind_agent_v1",
    model="gemini-2.0-flash",
    description="Provides analysis and optimization suggestions for cement plant operations.",
    generate_content_config=generate_content_config,
    instruction=(
        "You are a helpful cement plant AI assistant. "
        "Use the 'analyze_plant' tool to provide insights on plant metrics. "
        "Present actionable suggestions clearly."
    ),
    tools=[analyze_plant]
)
app = AdkApp(agent=cemmind_agent)

async def get_ai_suggestion(message: str) -> str:
    """Fetch AI response from CemMind Agent."""
    ai_suggestion = "⚠️ No response from CemMind Agent."
    async for event in app.async_stream_query(user_id="user123", message=message):
        parts = event.get("content", {}).get("parts", [])
        for part in parts:
            if "function_call" in part:
                func_call = part["function_call"]
                if func_call["name"] == "analyze_plant":
                    latest_data = func_call["args"]["latest_data"]
                    ai_suggestion = analyze_plant(latest_data)
            elif "text" in part:
                ai_suggestion = part["text"]
    return ai_suggestion

# ---------------- Streamlit Layout ----------------
st.set_page_config(layout="wide", page_title="CemMind AI Dashboard", page_icon="🏭")

# Sidebar controls
st.sidebar.header("⚙️ Controls")
rows = st.sidebar.slider("Rows to Generate", 100, 2000, 500, step=100)
history_points = st.sidebar.slider("History Points", 50, 500, 200, step=50)
refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 10, 3)

if st.sidebar.button("🚀 Push Bulk Data"):
    with st.spinner("Generating synthetic plant data..."):
        generate_data(rows)
    with st.spinner("Uploading to GCS..."):
        gcs_path = upload_to_gcs(LOCAL_CSV, GCS_BUCKET, GCS_DEST_PREFIX)
    with st.spinner("Loading into BigQuery..."):
        load_csv_from_gcs(PROJECT, DATASET, TABLE, gcs_path, write_disposition="WRITE_APPEND")
    st.sidebar.success("✅ Bulk data pushed to BigQuery")

# Simulation state
if "simulate" not in st.session_state:
    st.session_state.simulate = False
if "df_sim" not in st.session_state:
    st.session_state.df_sim = load_historical(history_points)

col1, col2 = st.sidebar.columns(2)
if col1.button("▶️ Start Simulation"):
    st.session_state.simulate = True
if col2.button("⏹ Stop Simulation"):
    st.session_state.simulate = False

st.title("🏭 CemMind AI – Smart Cement Plant Dashboard")

# Placeholders
kpi_placeholder = st.empty()
tab_placeholder = st.empty()

# Simulation loop
def render_kpis(latest):
    k1, k2, k3, k4, k5 = st.columns(5)

    # KPI details with explanations
    kpi_data = [
        ("🔥 Kiln Temp (°C)", latest['kiln_temp_C'], "#ffe5e5",
        "Maintaining optimal kiln temperature (~1450°C) is crucial for clinker quality. Too high = excess fuel use, too low = poor clinker."),
        ("⚡ Mill Power (kW)", latest['mill_power_kW'], "#e6f0ff",
        "Mill power reflects energy consumed in grinding. High values indicate heavy load or inefficiency."),
        ("🌱 AF Rate (%)", latest['AF_rate_percent'], "#e8fbe6",
        "Alternative Fuel Rate measures % of traditional fuel replaced with sustainable options. Higher is better for sustainability."),
        ("🧪 Free Lime (%)", latest['clinker_free_lime_percent'], "#fff5e6",
        "Free lime shows how complete clinker reactions are. High values = poor clinker quality and unstable cement."),
        ("🌍 CO₂ Emission (kg/ton)", latest['CO2_emission_kgpt'], "#f0f0f0",
        "Represents carbon intensity of cement production. Lower CO₂ = more sustainable process.")
    ]


    def get_severity_icon(title, value):
        if "Kiln" in title:
            if 1430 <= value <= 1470: return "🟢"
            elif 1400 <= value < 1430 or 1470 < value <= 1500: return "🟠"
            else: return "🔴"

        if "Mill" in title:
            if value < 4200: return "🟢"
            elif value < 4600: return "🟠"
            else: return "🔴"

        if "AF Rate" in title:
            if value >= 15: return "🟢"
            elif value >= 10: return "🟠"
            else: return "🔴"

        if "Free Lime" in title:
            if value < 1.5: return "🟢"
            elif value < 2.5: return "🟠"
            else: return "🔴"

        if "CO₂" in title:
            if value < 850: return "🟢"
            elif value < 900: return "🟠"
            else: return "🔴"

        return "❓"

    # Modern Tooltip CSS
    st.markdown(
        """
        <style>
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: pointer;
            margin-left: 12px;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 240px;
            background-color: #222;
            color: #fff;
            text-align: left;
            border-radius: 8px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            bottom: 130%; /* Position above */
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.25);
            font-size: 13px;
            line-height: 1.4;
            transition: opacity 0.25s ease, transform 0.25s ease;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
            transform: translateX(-50%) translateY(-4px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Render KPI cards with modern tooltips
    for col, (title, val, color, tooltip) in zip([k1, k2, k3, k4, k5], kpi_data):
        icon = get_severity_icon(title, val)
        with col:
            st.markdown(
                f"""
                <div style="background-color:{color}; border-radius:12px; padding:15px;">
                    <h5 style="color:black; display:flex; justify-content:space-between; align-items:center;">
                        {title}
                        <span class="tooltip">ⓘ
                            <span class="tooltiptext">{tooltip}</span>
                        </span>
                    </h5>
                    <p style="font-size:22px; font-weight:bold; color:black; margin:0;">{val:.1f} {icon}</p>
                </div>
                """,
                unsafe_allow_html=True
            )



def render_tabs(df):
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🤖 AI Copilot", "🌿 Sustainability", "📑 Raw Data"])

    # Trends
    with tab1:
        fig1 = px.line(df, x='step', y=['kiln_temp_C','mill_power_kW'],
                       title="Kiln Temperature & Mill Power", template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
        fig2 = px.line(df, x='step', y=['AF_rate_percent','clinker_free_lime_percent'],
                       title="Alternative Fuel Rate & Free Lime", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

    # ---------------- AI Copilot with streaming ----------------
    with tab2:
        st.subheader("🤖 CemMind AI Copilot")

        latest_row = df.tail(1).to_dict(orient="records")[0]
        default_prompt = f"Given the latest plant data {latest_row}, suggest 3 optimizations."

        # Latest plant suggestion streaming
        suggestion_placeholder = st.empty()
        suggestion_text = ""

        async def stream_ai_response(message: str):
            nonlocal suggestion_text
            async for event in app.async_stream_query(user_id="user123", message=message):
                parts = event.get("content", {}).get("parts", [])
                for part in parts:
                    if "function_call" in part and part["function_call"]["name"] == "analyze_plant":
                        latest_data = part["function_call"]["args"]["latest_data"]
                        result = analyze_plant(latest_data)
                        suggestion_text = result["text"]
                        suggestion_placeholder.markdown(f"🤖 **AI Copilot Suggestion:**\n\n{suggestion_text}")
                        st.graphviz_chart(render_process_diagram(result["severity"]))
                    elif "text" in part:
                        suggestion_text += part["text"]
                        suggestion_placeholder.markdown(f"🤖 **AI Copilot Suggestion:**\n\n{suggestion_text}")
                # suggestion_placeholder.markdown(f"🤖 **AI Copilot Suggestion:**\n\n{suggestion_text}")

        # Run streaming for latest metrics
        with st.spinner("Fetching AI suggestions for latest plant data..."):
            asyncio.run(stream_ai_response(default_prompt))

        st.markdown("---")
        st.subheader("💬 Ask CemMind AI Anything")

        # Chat input with unique key
        user_query = st.text_input("Type your question:", "", key=f"chat_input_tab2_{uuid.uuid4()}")

        if st.button("Send Query", key=f"chat_send_button_{uuid.uuid4()}"):
            chat_placeholder = st.empty()
            chat_text = ""

            async def stream_chat_response():
                nonlocal chat_text
                async for event in app.async_stream_query(user_id="user123", message=user_query.strip()):
                    parts = event.get("content", {}).get("parts", [])
                    for part in parts:
                        if "function_call" in part and part["function_call"]["name"] == "analyze_plant":
                            latest_data = part["function_call"]["args"]["latest_data"]
                            chat_text = analyze_plant(latest_data)
                        elif "text" in part:
                            chat_text += part["text"]
                    chat_placeholder.markdown(f"**You asked:** {user_query}\n\n🤖 **AI Response:**\n{chat_text}")

            with st.spinner("Getting AI response..."):
                asyncio.run(stream_chat_response())


    # Sustainability
    with tab3:
        avg_co2 = df['CO2_emission_kgpt'].mean()
        st.metric("Average CO₂ Intensity (kg/ton)", f"{avg_co2:.1f}")
        fig3 = px.histogram(df, x='CO2_emission_kgpt', nbins=30,
                            title="CO₂ Emission Distribution", template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)

    # Raw Data
    with tab4:
        st.dataframe(df.tail(20), use_container_width=True)

# ---------------- Main ----------------
while st.session_state.simulate:
    # Generate 1 new row
    df_new = generate_data(1)
    df = pd.concat([st.session_state.df_sim, df_new], ignore_index=True)
    df['step'] = range(len(df))
    st.session_state.df_sim = df

    latest = df.iloc[-1]
    with kpi_placeholder.container():
        render_kpis(latest)
    with tab_placeholder.container():
        render_tabs(df)

    # Push to GCS & BigQuery
    gcs_path = upload_to_gcs(LOCAL_CSV, GCS_BUCKET, GCS_DEST_PREFIX)
    load_csv_from_gcs(PROJECT, DATASET, TABLE, gcs_path, write_disposition="WRITE_APPEND")

    # Refresh interval
    for _ in range(refresh_rate):
        if not st.session_state.simulate:
            break
        time.sleep(1)

# Display once for historical data if simulation not running
if not st.session_state.simulate:
    df = st.session_state.df_sim.copy()
    df['step'] = range(len(df))
    latest = df.iloc[-1]
    with kpi_placeholder.container():
        render_kpis(latest)
    with tab_placeholder.container():
        render_tabs(df)
