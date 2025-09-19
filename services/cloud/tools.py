from vertexai.preview.agents import tool

@tool
def fetch_latest_sensor_data(limit: int = 10) -> str:
    """
    Fetch last N rows from BigQuery cement_prop.simulated_plant
    """
    from google.cloud import bigquery
    client = bigquery.Client()
    query = f"""
    SELECT *
    FROM `cemmind.cement_prop.simulated_plant`
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    rows = client.query(query).to_dataframe()
    return rows.to_json(orient="records")
