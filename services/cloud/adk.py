# Vertex AI ADK
from google.adk.agents import Agent
from vertexai import agent_engines
import vertexai

# ... after loading .env etc

# --- Vertex AI Init ---
def init_vertex_ai(project: str, region: str = "us-central1", staging_bucket: str = None):
    if not staging_bucket:
        raise ValueError("Must set staging_bucket for Vertex AI init (used for Agent Engine deployments).")
    vertexai.init(
        project=project,
        location=region,
        staging_bucket=staging_bucket
    )
    print(f"✅ Vertex AI initialized for {project} in {region}, staging bucket: {staging_bucket}")

def ask_vertex_ai(agent_name: str, message: str) -> str:
    runtime = Agent(agent_name)
    response = runtime.chat(messages=[{"content": message}])
    if response.candidates:
        return response.candidates[0].content[0].text
    else:
        return "⚠️ No response"


