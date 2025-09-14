import pandas as pd
import numpy as np
import datetime as dt
from google.cloud import storage
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Read configs
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_DEST_PREFIX = os.getenv("GCS_DEST_PREFIX")
LOCAL_CSV = os.getenv("LOCAL_CSV")
NUM_ROWS = int(os.getenv("NUM_ROWS", 1440))  # fallback 1440 if missing

def generate_data(n=NUM_ROWS):
    start = dt.datetime.utcnow()
    timestamps = [start + dt.timedelta(minutes=i) for i in range(n)]
    df = pd.DataFrame({
        "timestamp": timestamps,
        "kiln_temp_C": np.random.normal(1450, 15, n),
        "mill_power_kW": np.random.normal(4200, 150, n),
        "AF_rate_percent": np.clip(np.random.normal(15, 5, n), 0, 40),
        "clinker_free_lime_percent": np.random.normal(1.5, 0.3, n),
        "CO2_emission_kgpt": np.random.normal(850, 30, n)
    })
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.to_csv(LOCAL_CSV, index=False)
    print(f"✅ Generated dataset with {n} rows → {LOCAL_CSV}")
    return df


def upload_to_gcs(local_file, bucket_name, dest_prefix):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    dest_blob = f"{dest_prefix}/{os.path.basename(local_file)}"
    blob = bucket.blob(dest_blob)
    blob.upload_from_filename(local_file)
    print(f"📤 Uploaded {local_file} → gs://{bucket_name}/{dest_blob}")
    return f"gs://{bucket_name}/{dest_blob}"

if __name__ == "__main__":
    df = generate_data()
    gcs_path = upload_to_gcs(LOCAL_CSV, GCS_BUCKET, GCS_DEST_PREFIX)
    print(f"Data available at: {gcs_path}")
