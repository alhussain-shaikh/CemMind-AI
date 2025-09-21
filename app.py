import time
import json
import tempfile
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from simulation.batch_generator import generate_data, upload_to_gcs
from services.cloud.bigquery_client import load_csv_from_gcs, query_sample
from dashboard.kpis import render_kpis
from dashboard.tabs import render_tabs
from config import *

# Streamlit page config
st.set_page_config(layout="wide", page_title="CemMind AI Dashboard", page_icon="🏭")

# Load historical data
@st.cache_data
def load_historical(limit=200):
    df = query_sample(PROJECT, DATASET, TABLE)
    return df.tail(limit)

if "df_sim" not in st.session_state:
    st.session_state.df_sim = load_historical()

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

