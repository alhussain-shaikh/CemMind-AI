# Simplified generative controller that takes latest readings and returns an action suggestion
from services.cloud.vertex_ai_client import call_genai

def suggest_action(latest_reading):
    # Build a prompt for GenAI (mocked in this POC)
    prompt = f"Given the latest plant reading: {latest_reading}, suggest minimal safe setpoint changes to reduce energy while keeping quality stable."
    response = call_genai(prompt)
    return response
