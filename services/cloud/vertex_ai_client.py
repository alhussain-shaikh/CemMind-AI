# Vertex AI client stubs for POC
from google.cloud import aiplatform
import os

def init_vertex_ai(project, region="us-central1"):
    """
    Initialize Vertex AI environment
    """
    aiplatform.init(project=project, location=region)
    print(f"✅ Vertex AI initialized for project {project} in {region}")

def predict_vertex_ai(model_name, instances):
    """
    model_name: full Vertex AI resource name
    instances: list of dicts, e.g., [{"kiln_temp_C": 1450, ...}]
    """
    endpoint = aiplatform.Endpoint(model_name)
    predictions = endpoint.predict(instances=instances)
    return predictions

