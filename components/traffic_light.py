"""
Eco-Tide: Traffic Light Component
Animated 3-light risk indicator with pulsing glow, label, score, and action text.
"""

import streamlit as st


def render_traffic_light(level: str = "green", label: str = "Safe",
                         action: str = "Normal operations.", score: float = 0.2):
    """
    Render a visually stunning traffic-light risk indicator.

    Args:
        level:  'green', 'amber', or 'red'
        label:  human-readable risk label
        action: recommended action text
        score:  composite risk score 0-1
    """
    theme = st.session_state.get("theme", "dark")
    # Map levels to conjugate colours
    colors = {
        "green":  "#059669" if theme == "light" else "#00C853",
        "amber":  "#D97706" if theme == "light" else "#FFD600",
        "red":    "#DC2626" if theme == "light" else "#FF1744",
    }
    active_color = colors.get(level, colors["green"])
    off_color = "rgba(0,0,0,0.08)" if theme == "light" else "rgba(255,255,255,0.07)"

    # Build active/inactive state per light
    def _light(light_level: str) -> str:
        is_active = light_level == level
        c = colors[light_level]
        if is_active:
            return f"""
                background: {c};
                box-shadow: 0 0 18px 6px {c}88, 0 0 40px 12px {c}44;
                animation: tl-pulse-{light_level} 1.8s ease-in-out infinite;
            """
        return f"""
            background: {off_color};
            box-shadow: none;
        """

    score_pct = max(0, min(score, 1)) * 100

    html = f"""
    <style>
        @keyframes tl-pulse-red {{
            0%, 100% {{ box-shadow: 0 0 18px 6px #FF174488, 0 0 40px 12px #FF174444; }}
            50%      {{ box-shadow: 0 0 28px 10px #FF1744AA, 0 0 56px 18px #FF174466; }}
        }}
        @keyframes tl-pulse-amber {{
            0%, 100% {{ box-shadow: 0 0 18px 6px #FFD60088, 0 0 40px 12px #FFD60044; }}
            50%      {{ box-shadow: 0 0 28px 10px #FFD600AA, 0 0 56px 18px #FFD60066; }}
        }}
        @keyframes tl-pulse-green {{
            0%, 100% {{ box-shadow: 0 0 18px 6px #00C85388, 0 0 40px 12px #00C85344; }}
            50%      {{ box-shadow: 0 0 28px 10px #00C853AA, 0 0 56px 18px #00C85366; }}
        }}
        .tl-wrapper {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }}
        .tl-housing {{
            background: var(--bg-card, linear-gradient(180deg, #1A1F3D 0%, #0D1025 100%));
            border: 1px solid var(--border-card, rgba(255,255,255,0.06));
            border-radius: 28px;
            padding: 18px 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 14px;
            box-shadow: var(--shadow-card, 0 8px 32px rgba(0,0,0,0.5));
        }}
        .tl-light {{
            width: 52px;
            height: 52px;
            border-radius: 50%;
            transition: all 0.4s ease;
        }}
        .tl-label {{
            font-size: 18px;
            font-weight: 700;
            color: {active_color};
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 8px;
        }}
        .tl-score-bar-bg {{
            width: 100%;
            max-width: 140px;
            height: 5px;
            background: var(--border-card, rgba(255,255,255,0.1));
            border-radius: 3px;
            overflow: hidden;
            margin-top: 2px;
        }}
        .tl-score-bar-fill {{
            width: {score_pct}%;
            height: 100%;
            background: linear-gradient(90deg, #00C853, #FFD600, #FF1744);
            border-radius: 3px;
            transition: width 0.6s ease;
        }}
        .tl-score-text {{
            font-size: 11px;
            color: var(--text-muted, rgba(139,149,178,0.7));
            letter-spacing: 0.5px;
        }}
        .tl-action {{
            font-size: 12px;
            color: var(--text-secondary, rgba(139,149,178,0.8));
            text-align: center;
            line-height: 1.5;
            max-width: 180px;
            margin-top: 4px;
            padding: 8px 12px;
            background: var(--bg-card, rgba(19,24,55,0.6));
            border-radius: 10px;
            border: 1px solid var(--border-card, rgba(255,255,255,0.04));
        }}
    </style>

    <div class="tl-wrapper">
        <div class="tl-housing">
            <div class="tl-light" style="{_light('red')}"></div>
            <div class="tl-light" style="{_light('amber')}"></div>
            <div class="tl-light" style="{_light('green')}"></div>
        </div>
        <div class="tl-label">{label}</div>
        <div class="tl-score-bar-bg"><div class="tl-score-bar-fill"></div></div>
        <div class="tl-score-text">Risk Score: {score:.2f}</div>
        <div class="tl-action">{action}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
