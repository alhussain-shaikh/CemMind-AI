import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables once

PROJECT = os.getenv("PROJECT")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_DEST_PREFIX = os.getenv("GCS_DEST_PREFIX")
LOCAL_CSV = os.getenv("LOCAL_CSV")
VERTEX_AGENT = os.getenv("VERTEX_AGENT")
REGION = os.getenv("REGION", "us-central1")
GCS_URI = os.getenv("GCS_URI")