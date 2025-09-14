import os
import sys
import time
import random
import pandas as pd
import numpy as np
import datetime as dt
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

# Add project root to sys.path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Imports
from simulation.batch_generator import generate_data, upload_to_gcs
from services.cloud.bigquery_client import load_csv_from_gcs, query_sample

# Load environment variables
load_dotenv()
PROJECT = os.getenv("PROJECT")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_DEST_PREFIX = os.getenv("GCS_DEST_PREFIX")
LOCAL_CSV = os.getenv("LOCAL_CSV")

# --------------------
# Page Config
# --------------------
st.set_page_config(layout='wide', page_title='CemMind AI Dashboard', page_icon="🏭")
st.markdown("""
<style>
div[data-testid="stMetricLabel"] { color: black !important; font-weight: 600; }
div[data-testid="stMetricValue"] { color: black !important; font-size: 1.4em; }
</style>
""", unsafe_allow_html=True)

# --------------------
# Sidebar
# --------------------
st.sidebar.header("⚙️ Controls")
rows = st.sidebar.slider("Rows to Generate", 100, 2000, 500, step=100)
history_points = st.sidebar.slider("History Points", 50, 500, 200, step=50)
refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 10, 3)

if st.sidebar.button("🚀 Generate + Upload + Load"):
    with st.spinner("Generating synthetic plant data..."):
        generate_data(rows)
    with st.spinner("Uploading to GCS..."):
        gcs_path = upload_to_gcs(LOCAL_CSV, GCS_BUCKET, GCS_DEST_PREFIX)
    with st.spinner("Loading into BigQuery..."):
        load_csv_from_gcs(PROJECT, DATASET, TABLE, gcs_path, write_disposition="WRITE_APPEND")
    st.sidebar.success("✅ Data pushed to BigQuery")

# --------------------
# Main Layout
# --------------------
st.title("🏭 CemMind AI – Smart Cement Plant Dashboard")
kpi_placeholder = st.empty()
tab_placeholder = st.empty()

# --------------------
# Session State
# --------------------
if "update_id" not in st.session_state:
    st.session_state.update_id = 0

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

# --------------------
# Live Data Loop
# --------------------
for _ in range(200):
    st.session_state.update_id += 1
    update_id = st.session_state.update_id

    # Generate 1 new row and push to BigQuery
    df_new = generate_data(1)
    gcs_path = upload_to_gcs(LOCAL_CSV, GCS_BUCKET, GCS_DEST_PREFIX)
    load_csv_from_gcs(PROJECT, DATASET, TABLE, gcs_path, write_disposition="WRITE_APPEND")

    # Fetch latest data
    try:
        df = query_sample(PROJECT, DATASET, TABLE).tail(history_points)
        st.session_state.df = df
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        break

    if df.empty:
        st.warning("⚠️ No data found. Please generate data first.")
        break

    latest = df.iloc[-1]

    # ---------------- KPIs ----------------
    with kpi_placeholder.container():
        k1, k2, k3, k4, k5 = st.columns(5)
        kpi_data = [
            ("🔥 Kiln Temp (°C)", f"{latest['kiln_temp_C']:.1f}", "#ffe5e5"),
            ("⚡ Mill Power (kW)", f"{latest['mill_power_kW']:.0f}", "#e6f0ff"),
            ("🌱 AF Rate (%)", f"{latest['AF_rate_percent']:.1f}", "#e8fbe6"),
            ("🧪 Free Lime (%)", f"{latest['clinker_free_lime_percent']:.2f}", "#fff5e6"),
            ("🌍 CO₂ Emission (kg/ton)", f"{latest['CO2_emission_kgpt']:.1f}", "#f0f0f0")
        ]
        for col, (title, val, color) in zip([k1,k2,k3,k4,k5], kpi_data):
            with col:
                st.markdown(
                    f"""<div style="background-color:{color}; border-radius:12px; padding:15px;">
                    <h5 style="color:black;">{title}</h5>
                    <p style="font-size:22px; font-weight:bold; color:black;">{val}</p>
                    </div>""",
                    unsafe_allow_html=True
                )

    # ---------------- Tabs ----------------
    with tab_placeholder.container():
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📈 Trends", "🤖 AI Copilot", "🌿 Sustainability", "📑 Raw Data"]
        )

        # Trends
        with tab1:
            fig1 = px.line(df, x='ts', y=['kiln_temp_C','mill_power_kW'],
                           title="Kiln Temperature & Mill Power", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True, key=f"fig1_{update_id}")

            fig2 = px.line(df, x='ts', y=['AF_rate_percent','clinker_free_lime_percent'],
                           title="Alternative Fuel Rate & Free Lime", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True, key=f"fig2_{update_id}")

        # AI Copilot
        with tab2:
            st.success("✅ Reduce ID fan by 3% → Estimated energy savings **2.3%**")
            st.warning("⚠️ Increase AF by 2% → TSR +1.5% (check coating risk)")
            st.info("💡 Suggest running optimization on grinding schedule")

        # Sustainability
        with tab3:
            avg_co2 = df['CO2_emission_kgpt'].mean()
            st.metric("Average CO₂ Intensity (kg/ton)", f"{avg_co2:.1f}")
            fig3 = px.histogram(df, x='CO2_emission_kgpt', nbins=30,
                                title="CO₂ Emission Distribution", template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True, key=f"fig3_{update_id}")

        # Raw Data
        with tab4:
            st.dataframe(df.tail(20), use_container_width=True, key=f"raw_{update_id}")

    # ---------------- Refresh ----------------
    time.sleep(refresh_rate)
