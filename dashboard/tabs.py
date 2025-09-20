import streamlit as st
import plotly.express as px
import asyncio
import uuid
from agents.cem_agent import app, analyze_plant, render_process_diagram

def render_tabs(df):
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🤖 AI Copilot", "🌿 Sustainability", "📑 Raw Data"])

    # --- Trends ---
    with tab1:
        fig1 = px.line(df, x='step', y=['kiln_temp_C','mill_power_kW'],
                       title="Kiln Temp & Mill Power", template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
        fig2 = px.line(df, x='step', y=['AF_rate_percent','clinker_free_lime_percent'],
                       title="AF Rate & Free Lime", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

    # --- AI Copilot ---
    with tab2:
        latest_row = df.tail(1).to_dict(orient="records")[0]
        default_prompt = f"Given the latest plant data {latest_row}, suggest 3 optimizations."
        placeholder = st.empty()
        suggestion_text = ""

        async def stream_ai_response(message: str):
            nonlocal suggestion_text
            async for event in app.async_stream_query(user_id="user123", message=message):
                parts = event.get("content", {}).get("parts", [])
                for part in parts:
                    if "function_call" in part and part["function_call"]["name"] == "analyze_plant":
                        latest_data = part["function_call"]["args"]["latest_data"]
                        result = analyze_plant(latest_data)
                        suggestion_text = result["text"]
                        placeholder.markdown(f"🤖 **AI Copilot Suggestion:**\n\n{suggestion_text}")
                        st.graphviz_chart(render_process_diagram(result["severity"]))
                    elif "text" in part:
                        suggestion_text += part["text"]
                        placeholder.markdown(f"🤖 **AI Copilot Suggestion:**\n\n{suggestion_text}")

        with st.spinner("Fetching AI suggestions..."):
            asyncio.run(stream_ai_response(default_prompt))

        # Run streaming for latest metrics

        st.markdown("---")
        st.subheader("💬 Ask CemMind AI Anything")

        # Chat input with unique key
        user_query = st.text_input("Type your question:", "", key=f"chat_input_tab2_{uuid.uuid4()}")

        if st.button("Send Query", key=f"chat_send_button_{uuid.uuid4()}"):
            chat_placeholder = st.empty()
            chat_text = ""

            async def stream_chat_response():
                nonlocal chat_text
                async for event in app.async_stream_query(user_id="user123", message=user_query.strip()):
                    parts = event.get("content", {}).get("parts", [])
                    for part in parts:
                        if "function_call" in part and part["function_call"]["name"] == "analyze_plant":
                            latest_data = part["function_call"]["args"]["latest_data"]
                            chat_text = analyze_plant(latest_data)
                        elif "text" in part:
                            chat_text += part["text"]
                    chat_placeholder.markdown(f"**You asked:** {user_query}\n\n🤖 **AI Response:**\n{chat_text}")

            with st.spinner("Getting AI response..."):
                asyncio.run(stream_chat_response())


    # --- Sustainability ---
    with tab3:
        st.metric("Average CO₂ (kg/ton)", f"{df['CO2_emission_kgpt'].mean():.1f}")
        fig3 = px.histogram(df, x='CO2_emission_kgpt', nbins=30, title="CO₂ Emission Distribution", template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)

    # --- Raw Data ---
    with tab4:
        st.dataframe(df.tail(20), use_container_width=True)
