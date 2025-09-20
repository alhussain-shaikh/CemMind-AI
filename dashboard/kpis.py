import streamlit as st

def render_kpis(latest):
    """Render KPI cards with modern tooltips and severity icons."""
    k1, k2, k3, k4, k5 = st.columns(5)

    kpi_data = [
        ("🔥 Kiln Temp (°C)", latest['kiln_temp_C'], "#ffe5e5",
        "Maintaining optimal kiln temperature (~1450°C) is crucial for clinker quality."),
        ("⚡ Mill Power (kW)", latest['mill_power_kW'], "#e6f0ff",
        "Mill power reflects energy consumed in grinding. High values indicate heavy load or inefficiency."),
        ("🌱 AF Rate (%)", latest['AF_rate_percent'], "#e8fbe6",
        "Alternative Fuel Rate measures % of traditional fuel replaced with sustainable options."),
        ("🧪 Free Lime (%)", latest['clinker_free_lime_percent'], "#fff5e6",
        "Free lime shows how complete clinker reactions are."),
        ("🌍 CO₂ Emission (kg/ton)", latest['CO2_emission_kgpt'], "#f0f0f0",
        "Represents carbon intensity of cement production. Lower CO₂ = more sustainable process.")
    ]

    def get_severity_icon(title, value):
        if "Kiln" in title:
            if 1430 <= value <= 1470: return "🟢"
            elif 1400 <= value < 1430 or 1470 < value <= 1500: return "🟠"
            else: return "🔴"

        if "Mill" in title:
            if value < 4200: return "🟢"
            elif value < 4600: return "🟠"
            else: return "🔴"

        if "AF Rate" in title:
            if value >= 15: return "🟢"
            elif value >= 10: return "🟠"
            else: return "🔴"

        if "Free Lime" in title:
            if value < 1.5: return "🟢"
            elif value < 2.5: return "🟠"
            else: return "🔴"

        if "CO₂" in title:
            if value < 850: return "🟢"
            elif value < 900: return "🟠"
            else: return "🔴"

        return "❓"

    # Modern tooltip CSS
    st.markdown(
        """
        <style>
        .tooltip {position: relative; display: inline-block; cursor: pointer; margin-left: 12px;}
        .tooltip .tooltiptext {visibility: hidden; width: 240px; background-color: #222; color: #fff;
            text-align: left; border-radius: 8px; padding: 10px; position: absolute; z-index: 1;
            bottom: 130%; left: 50%; transform: translateX(-50%); opacity: 0;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.25); font-size: 13px; line-height: 1.4;
            transition: opacity 0.25s ease, transform 0.25s ease;}
        .tooltip:hover .tooltiptext {visibility: visible; opacity: 1; transform: translateX(-50%) translateY(-4px);}
        </style>
        """, unsafe_allow_html=True
    )

    # Render KPI cards
    for col, (title, val, color, tooltip) in zip([k1, k2, k3, k4, k5], kpi_data):
        icon = get_severity_icon(title, val)
        with col:
            st.markdown(
                f"""
                <div style="background-color:{color}; border-radius:12px; padding:15px;">
                    <h5 style="color:black; display:flex; justify-content:space-between; align-items:center;">
                        {title}
                        <span class="tooltip">ⓘ
                            <span class="tooltiptext">{tooltip}</span>
                        </span>
                    </h5>
                    <p style="font-size:22px; font-weight:bold; color:black; margin:0;">{val:.1f} {icon}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
