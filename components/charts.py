"""
Eco-Tide: Reusable Plotly Chart Components
Charts adapt to the user's OS color scheme preference (light / dark).
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

# ── Shared Palette & Layout Defaults ────────────────────────────────────────
PALETTE = [
    "#0A84FF", "#00C7BE", "#FF6B35", "#FF1744",
    "#FFD600", "#00C853", "#7C4DFF", "#FF4081",
]

RISK_COLOR_MAP = {
    "green":  "#00C853",
    "amber":  "#FFD600",
    "red":    "#FF1744",
}


def _is_dark_mode() -> bool:
    """Detect OS dark mode. Falls back to False (light) if unable to detect."""
    try:
        import darkdetect
        return darkdetect.isDark()
    except Exception:
        return False


import streamlit as st


def _theme_colors() -> dict:
    """Return color tokens dynamically based on st.session_state['theme']."""
    current_theme = st.session_state.get("theme", "dark") if hasattr(st, "session_state") else "dark"
    if current_theme == "light":
        return {
            "paper_bg": "#FFFFFF",
            "plot_bg": "#F8FAFC",
            "text": "#0F172A",
            "text_secondary": "#334155",
            "grid": "rgba(0,0,0,0.06)",
            "line": "rgba(0,0,0,0.10)",
            "hover_bg": "#0F172A",
            "hover_border": "#0284C7",
            "slider_bg": "#E2E8F0",
            "donut_line": "#FFFFFF",
        }
    else:
        return {
            "paper_bg": "#131D31",
            "plot_bg": "#0F172A",
            "text": "#F8FAFC",
            "text_secondary": "#CBD5E1",
            "grid": "rgba(255,255,255,0.10)",
            "line": "rgba(255,255,255,0.15)",
            "hover_bg": "#0F172A",
            "hover_border": "rgba(56,189,248,0.4)",
            "slider_bg": "#1E293B",
            "donut_line": "#131D31",
        }


def _base_layout(**overrides) -> dict:
    """Return a base Plotly layout dict with high-contrast text and wide margins."""
    tc = _theme_colors()
    current_theme = st.session_state.get("theme", "dark") if hasattr(st, "session_state") else "dark"
    legend_bg = "rgba(255,255,255,0.9)" if current_theme == "light" else "rgba(15,23,42,0.85)"
    layout = dict(
        paper_bgcolor=tc["paper_bg"],
        plot_bgcolor=tc["plot_bg"],
        font=dict(family="Inter, sans-serif", color=tc["text"], size=12),
        margin=dict(l=160, r=40, t=50, b=50),
        legend=dict(
            bgcolor=legend_bg,
            bordercolor=tc["line"],
            borderwidth=1,
            font=dict(size=12, color=tc["text"]),
        ),
        xaxis=dict(
            gridcolor=tc["grid"],
            zerolinecolor=tc["grid"],
            linecolor=tc["line"],
            tickfont=dict(size=12, color=tc["text"]),
            title=dict(font=dict(size=13, color=tc["text"])),
        ),
        yaxis=dict(
            gridcolor=tc["grid"],
            zerolinecolor=tc["grid"],
            linecolor=tc["line"],
            tickfont=dict(size=12, color=tc["text"]),
            title=dict(font=dict(size=13, color=tc["text"])),
            automargin=True,
        ),
        hoverlabel=dict(
            bgcolor=tc["hover_bg"],
            bordercolor=tc["hover_border"],
            font=dict(family="Inter, sans-serif", color="#FFFFFF", size=12),
        ),
    )
    layout.update(overrides)
    return layout


# ═════════════════════════════════════════════════════════════════════════════
# 1. Water Level Time-Series Chart
# ═════════════════════════════════════════════════════════════════════════════
def create_water_level_chart(df: pd.DataFrame,
                             show_components: bool = False) -> go.Figure:
    """
    Time-series chart of water level, optionally showing tidal & surge components.

    Expected columns:
        - water_level_m (required)
        - tidal_prediction_m (optional, used when show_components=True)
        - surge_residual_m   (optional, used when show_components=True)

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Main water level trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["water_level_m"],
        mode="lines",
        name="Total Water Level",
        line=dict(color=PALETTE[0], width=2.2),
        fill="tozeroy",
        fillcolor="rgba(10,132,255,0.08)",
        hovertemplate="<b>%{x|%Y-%m-%d %H:%M}</b><br>Water Level: %{y:.3f} m<extra></extra>",
    ))

    if show_components:
        if "tidal_prediction_m" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["tidal_prediction_m"],
                mode="lines",
                name="Tidal Component",
                line=dict(color=PALETTE[1], width=1.5, dash="dot"),
                hovertemplate="Tidal: %{y:.3f} m<extra></extra>",
            ))
        if "surge_residual_m" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["surge_residual_m"],
                mode="lines",
                name="Surge Residual",
                line=dict(color=PALETTE[2], width=1.5, dash="dash"),
                hovertemplate="Surge: %{y:.3f} m<extra></extra>",
            ))

    tc = _theme_colors()
    fig.update_layout(**_base_layout(
        title=dict(text="Water Level", font=dict(size=16, color=tc["text"])),
        yaxis_title="Height (m)",
        xaxis_title="",
        height=380,
        hovermode="x unified",
    ))

    # Add range slider
    fig.update_xaxes(
        rangeslider=dict(visible=True, bgcolor=tc["slider_bg"], thickness=0.04),
    )

    return fig


# ═════════════════════════════════════════════════════════════════════════════
# 2. Environmental Factor Heatmap (Correlation Matrix)
# ═════════════════════════════════════════════════════════════════════════════
def create_factor_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Correlation heatmap of numeric environmental factors.

    Args:
        df: DataFrame with numeric columns to correlate.

    Returns:
        plotly.graph_objects.Figure
    """
    tc = _theme_colors()
    numeric_df = df.select_dtypes(include=[np.number])
    corr = numeric_df.corr()

    # Custom blue-teal-orange diverging colorscale
    colorscale = [
        [0.0,  "#FF1744"],
        [0.25, "#FF6B35"],
        [0.5,  "#1A2147"],
        [0.75, "#00C7BE"],
        [1.0,  "#0A84FF"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.index,
        colorscale=colorscale,
        zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=10, color=tc["text"]),
        hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>",
        colorbar=dict(
            title=dict(text="r", font=dict(color=tc["text_secondary"], size=12)),
            tickfont=dict(color=tc["text_secondary"]),
            outlinecolor=tc["line"],
            outlinewidth=1,
        ),
    ))

    fig.update_layout(**_base_layout(
        title=dict(text="Factor Correlation Matrix", font=dict(size=16, color=tc["text"])),
        height=520,
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=10, color=tc["text_secondary"]),
            gridcolor=tc["grid"],
        ),
        yaxis=dict(
            tickfont=dict(size=10, color=tc["text_secondary"]),
            gridcolor=tc["grid"],
            autorange="reversed",
        ),
    ))

    return fig


# ═════════════════════════════════════════════════════════════════════════════
# 3. Risk Timeline (Horizontal Coloured Bars)
# ═════════════════════════════════════════════════════════════════════════════
def create_risk_timeline(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart coloured by risk level over time.

    Expected columns:
        - risk_level  (str: 'green', 'amber', 'red')
        - risk_score  (float 0-1)

    Returns:
        plotly.graph_objects.Figure
    """
    if "risk_level" not in df.columns or "risk_score" not in df.columns:
        # Return empty placeholder
        fig = go.Figure()
        fig.update_layout(**_base_layout(
            title="Risk Timeline (no data)",
            height=260,
        ))
        return fig

    colors = df["risk_level"].map(RISK_COLOR_MAP).fillna("#8B95B2")

    fig = go.Figure(go.Bar(
        x=df.index,
        y=df["risk_score"],
        marker=dict(
            color=colors,
            line=dict(width=0),
            opacity=0.85,
        ),
        hovertemplate=(
            "<b>%{x|%Y-%m-%d %H:%M}</b><br>"
            "Risk Score: %{y:.3f}<extra></extra>"
        ),
    ))

    # Threshold reference lines
    fig.add_hline(y=0.3, line_dash="dot", line_color="#FFD60066",
                  annotation_text="Amber", annotation_font_color="#FFD600",
                  annotation_font_size=10, annotation_position="top left")
    fig.add_hline(y=0.6, line_dash="dot", line_color="#FF174466",
                  annotation_text="Red", annotation_font_color="#FF1744",
                  annotation_font_size=10, annotation_position="top left")

    tc = _theme_colors()
    fig.update_layout(**_base_layout(
        title=dict(text="Risk Level Timeline", font=dict(size=16, color=tc["text"])),
        yaxis_title="Risk Score",
        xaxis_title="",
        height=300,
        bargap=0.05,
        showlegend=False,
    ))

    return fig


# ═════════════════════════════════════════════════════════════════════════════
# 4. Factor Contribution Donut Chart
# ═════════════════════════════════════════════════════════════════════════════
def create_factor_contribution_chart(factor_scores: dict) -> go.Figure:
    """
    Donut / pie chart showing weighted contribution of each risk factor.

    Args:
        factor_scores: dict like {"Water Level": 0.35, "Rainfall": 0.15, ...}

    Returns:
        plotly.graph_objects.Figure
    """
    labels = list(factor_scores.keys())
    values = list(factor_scores.values())
    chart_colors = PALETTE[:len(labels)]

    tc = _theme_colors()
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(
            colors=chart_colors,
            line=dict(color=tc["donut_line"], width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=12, color=tc["text"]),
        hovertemplate="<b>%{label}</b><br>Score: %{value:.3f}<br>Share: %{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    ))

    # Center annotation
    total = sum(values)
    fig.add_annotation(
        text=f"<b>{total:.2f}</b><br><span style='font-size:10px;color:{tc['text_secondary']}'>composite</span>",
        showarrow=False,
        font=dict(size=20, color=tc["text"], family="Inter, sans-serif"),
        x=0.5, y=0.5, xref="paper", yref="paper",
    )

    fig.update_layout(**_base_layout(
        title=dict(text="Factor Contributions", font=dict(size=16, color=tc["text"])),
        height=380,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=tc["text_secondary"]),
        ),
    ))

    return fig
