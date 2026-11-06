"""
Eco-Tide: Metric Card Components
Glassmorphism stat cards with icons, values, units, and delta indicators.
"""

import streamlit as st


def render_metric_card(title: str, value: str, unit: str,
                       delta: str | None = None, delta_color: str = "normal",
                       icon: str = "📊"):
    """
    Render a single glassmorphism metric card.

    Args:
        title:        small label above the value
        value:        main numeric value (already formatted as string)
        unit:         unit suffix (e.g. 'm', 'hPa')
        delta:        optional delta string like '+0.5' or '-2.3'
        delta_color:  'normal' (green=up), 'inverse' (red=up), 'off'
        icon:         emoji icon
    """
    # Determine delta arrow and CSS class
    delta_html = ""
    if delta is not None and delta != "":
        delta_str = str(delta)
        if delta_str.startswith("+") or delta_str.startswith("-"):
            is_positive = delta_str.startswith("+")
        else:
            try:
                is_positive = float(delta_str) >= 0
            except ValueError:
                is_positive = True

        if delta_color == "off":
            css_class = "neutral"
        elif delta_color == "inverse":
            css_class = "down" if is_positive else "up"
        else:
            css_class = "up" if is_positive else "down"

        arrow = "▲" if is_positive else "▼"
        delta_html = f'<div class="mc-delta {css_class}">{arrow} {delta_str}</div>'

    html = f"""
    <div class="metric-card">
        <div class="mc-icon">{icon}</div>
        <div class="mc-title">{title}</div>
        <div>
            <span class="mc-value">{value}</span>
            <span class="mc-unit">{unit}</span>
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_row(metrics: list[dict]):
    """
    Render a row of metric cards using st.columns.

    Args:
        metrics: list of dicts, each with keys:
                 title, value, unit, icon
                 Optional: delta, delta_color
    """
    cols = st.columns(len(metrics), gap="medium")
    for col, m in zip(cols, metrics):
        with col:
            render_metric_card(
                title=m.get("title", "Metric"),
                value=str(m.get("value", "—")),
                unit=m.get("unit", ""),
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
                icon=m.get("icon", "📊"),
            )
