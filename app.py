import plotly.graph_objects as go
import streamlit as st

from src.spendable import build_balance_series, first_alert, get_status, load_spendable

st.set_page_config(page_title="Overview")

# Load data and build the 12-month forecast
settings, movements = load_spendable("data/example_portfolio.yaml")
series = build_balance_series(settings, movements, 12)

# Big number: current balance, colored by status
current = series["balance"].iloc[0]
status = get_status(current, settings)
colors = {"ok": "#2E9E6B", "warning": "#D93025", "stop": "#D93025"}
label = "STOP" if status == "stop" else f"€ {current:,.0f}"

st.markdown("### Spendable")
st.markdown(
    f"<h1 style='color:{colors[status]}; font-size:4rem; margin-top:0'>{label}</h1>",
    unsafe_allow_html=True,
)

# Forecast alert: first future month below the thresholds
alert = first_alert(series, settings)
if alert is None:
    st.caption("No alerts in the next 12 months.")
else:
    month, level = alert
    text = "reaches zero" if level == "stop" else "drops below the warning threshold"
    st.warning(f"In {month.strftime('%B %Y')} your balance {text}.")

# Balance over time, with the warning threshold as a dashed line
fig = go.Figure()
fig.add_trace(go.Scatter(x=series["month"], y=series["balance"], mode="lines+markers", name="Balance"))
fig.add_hline(y=settings.warning_threshold, line_dash="dash",line_color="#D93025", annotation_text="Warning threshold")
fig.update_layout(yaxis_title="€", margin=dict(l=0, r=0, t=20, b=0))
st.plotly_chart(fig, use_container_width=True)