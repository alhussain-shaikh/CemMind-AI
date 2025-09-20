from google.genai import types
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp
from dashboard.kpis import render_kpis  # optional if needed
from graphviz import Digraph

# ---- AI Agent Setup ----
safety_settings = [types.SafetySetting(
    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
    threshold=types.HarmBlockThreshold.OFF
)]

generate_content_config = types.GenerateContentConfig(
    safety_settings=safety_settings,
    temperature=0.28,
    max_output_tokens=1000,
    top_p=0.95
)

cemmind_agent = Agent(
    name="cemmind_agent_v1",
    model="gemini-2.0-flash",
    description="Cement plant AI assistant",
    generate_content_config=generate_content_config,
    instruction="You are a helpful cement plant AI assistant. Use 'analyze_plant' tool for insights.",
    tools=[]
)

app = AdkApp(agent=cemmind_agent)


def analyze_plant(latest_data: dict) -> dict:
    """Analyze cement plant data and return suggestions + stage severities."""
    kiln_temp = latest_data.get("kiln_temp_C")
    mill_power = latest_data.get("mill_power_kW")
    af_rate = latest_data.get("AF_rate_percent")
    free_lime = latest_data.get("clinker_free_lime_percent")
    co2 = latest_data.get("CO2_emission_kgpt")

    report = (
        f"Kiln Temp: {kiln_temp}°C\n"
        f"Mill Power: {mill_power} kW\n"
        f"AF Rate: {af_rate}%\n"
        f"Free Lime: {free_lime}%\n"
        f"CO₂ Emission: {co2} kg/ton\n"
    )

    suggestions = []
    severity = {stage: "normal" for stage in ["Raw", "Preheat", "Clinker", "Grind", "Sustain"]}

    # Kiln temp
    if kiln_temp > 1500:
        suggestions.append("🔥 Kiln temperature is critical! Reduce fuel immediately.")
        severity["Preheat"] = "critical"
    elif kiln_temp > 1450:
        suggestions.append("⚠️ Kiln temperature is high, monitor fuel closely.")
        severity["Preheat"] = "warning"

    # AF rate
    if af_rate < 3:
        suggestions.append("Critical low AF rate; sustainability compromised.")
        severity["Sustain"] = "critical"
    elif af_rate < 5:
        suggestions.append("Increase alternative fuel rate to improve sustainability.")
        severity["Sustain"] = "warning"

    # Free lime
    if free_lime > 4:
        suggestions.append("Clinker free lime is critically high; poor quality risk.")
        severity["Clinker"] = "critical"
    elif free_lime > 2.5:
        suggestions.append("Free lime is high; adjust kiln process.")
        severity["Clinker"] = "warning"

    # CO₂
    if co2 > 1000:
        suggestions.append("Critical CO₂ emissions; energy optimization needed.")
        severity["Sustain"] = "critical"
    elif co2 > 800:
        suggestions.append("High CO₂ emission; consider process efficiency improvements.")
        severity["Sustain"] = "warning"

    # Mill power
    if mill_power > 6000:
        suggestions.append("Critical grinding load; immediate action required.")
        severity["Grind"] = "critical"
    elif mill_power > 5000:
        suggestions.append("Mill power is high; check grinding efficiency.")
        severity["Grind"] = "warning"

    return {
        "text": report + ("\n".join(suggestions) if suggestions else "\nAll metrics within normal range."),
        "severity": severity
    }


def render_process_diagram(severity: dict):
    """Graphviz diagram with color-coded severities"""
    process = Digraph()
    process.attr(rankdir="LR", size="8,5")
    process.attr("node", shape="box", style="rounded,filled")
    color_map = {"normal":"palegreen","warning":"gold","critical":"lightcoral"}
    for stage, label in [
        ("Raw","🪨 Raw Material Prep"), ("Preheat","🔥 Preheating & Calcination"),
        ("Clinker","🧱 Clinker Formation"), ("Grind","⚙️ Grinding & Cooling"),
        ("Sustain","🌿 Sustainability")
    ]:
        level = severity.get(stage,"normal")
        process.node(stage,label,fillcolor=color_map.get(level,"lightgrey"))
    process.edges([("Raw","Preheat"),("Preheat","Clinker"),("Clinker","Grind"),("Grind","Sustain")])
    return process
