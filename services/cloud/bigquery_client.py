from google.cloud import bigquery
from dotenv import load_dotenv
import streamlit as st
import os

# load .env file
load_dotenv()

PROJECT = os.getenv("PROJECT")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
GCS_URI = os.getenv("GCS_URI")

def load_csv_from_gcs(project, dataset_id, table_id, gcs_uri, write_disposition="WRITE_APPEND"):
    client = bigquery.Client(project=project)

    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("kiln_temp_C", "FLOAT"),
        bigquery.SchemaField("mill_power_kW", "FLOAT"),
        bigquery.SchemaField("AF_rate_percent", "FLOAT"),
        bigquery.SchemaField("clinker_free_lime_percent", "FLOAT"),
        bigquery.SchemaField("CO2_emission_kgpt", "FLOAT")
    ]

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=write_disposition,
        allow_quoted_newlines=True,
        field_delimiter=","
    )

    load_job = client.load_table_from_uri(
        gcs_uri,
        table_ref,
        job_config=job_config
    )
    print(f"Starting job {load_job.job_id}")
    load_job.result()
    destination_table = client.get_table(table_ref)
    print(f"Loaded {destination_table.num_rows} rows into {dataset_id}.{table_id}")

def query_sample(project, dataset_id, table_id):
    client = bigquery.Client(project=project)
    sql = f"""
    SELECT
      TIMESTAMP(timestamp) AS ts,
      kiln_temp_C,
      mill_power_kW,
      AF_rate_percent,
      clinker_free_lime_percent,
      CO2_emission_kgpt
    FROM `{project}.{dataset_id}.{table_id}`
    ORDER BY ts DESC
    LIMIT 500
    """
    df = client.query(sql).to_dataframe()
    print(df)
    return df

if __name__ == "__main__":
    load_csv_from_gcs(PROJECT, DATASET, TABLE, GCS_URI, write_disposition="WRITE_APPEND")
    _ = query_sample(PROJECT, DATASET, TABLE)
