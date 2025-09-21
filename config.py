import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables once

import streamlit as st

PROJECT = st.secrets["PROJECT"]
DATASET = st.secrets["DATASET"]
TABLE = st.secrets["TABLE"]
GCS_BUCKET = st.secrets["GCS_BUCKET"]
GCS_DEST_PREFIX = st.secrets["GCS_DEST_PREFIX"]
LOCAL_CSV = st.secrets["LOCAL_CSV"]
VERTEX_AGENT = st.secrets["VERTEX_AGENT"]
REGION = st.secrets.get("REGION", "us-central1")
GCS_URI = st.secrets["GCS_URI"]
