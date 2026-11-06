"""
Eco-Tide: Central Theme Engine & Dynamic Dark/Bright Mode Manager
Provides high-contrast conjugate design systems, Streamlit UI overrides, and Plotly theme integration.
"""

import streamlit as st


def init_theme() -> str:
    """Initialize theme in session state and return the active theme ('dark' or 'light')."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    return st.session_state["theme"]


def render_theme_switcher() -> str:
    """
    Render a clean, responsive, segmented Dark / Bright mode toggle in the sidebar.
    Returns the active theme: 'dark' or 'light'.
    """
    current_theme = init_theme()

    st.sidebar.markdown("""
        <div style="font-size: 11px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 8px;">
            APPEARANCE MODE
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        is_dark = (current_theme == "dark")
        btn_dark_type = "primary" if is_dark else "secondary"
        if st.button("🌙 Dark", key="btn_theme_dark_toggle", type=btn_dark_type, use_container_width=True):
            if current_theme != "dark":
                st.session_state["theme"] = "dark"
                st.rerun()

    with col2:
        is_light = (current_theme == "light")
        btn_light_type = "primary" if is_light else "secondary"
        if st.button("☀️ Bright", key="btn_theme_light_toggle", type=btn_light_type, use_container_width=True):
            if current_theme != "light":
                st.session_state["theme"] = "light"
                st.rerun()

    st.sidebar.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
    return current_theme


def get_theme_css(theme: str) -> str:
    """Return the complete CSS string for either dark or light theme with conjugate high contrast."""
    if theme == "light":
        return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg-page: #F8FAFC;
    --bg-page-gradient: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 50%, #E2E8F0 100%);
    --bg-card: #FFFFFF;
    --bg-card-subtle: #F8FAFC;
    --bg-card-hover: #FFFFFF;
    --bg-card-rgb: 255, 255, 255;
    --bg-sidebar: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
    --border-card: #CBD5E1;
    --border-subtle: #E2E8F0;
    --border-sidebar: #CBD5E1;
    --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
    --shadow-card-hover: 0 10px 30px rgba(2, 132, 199, 0.15);
    --primary: #0284C7;
    --primary-rgb: 2, 132, 199;
    --secondary: #0D9488;
    --accent: #6366F1;
    --danger: #DC2626;
    --warning: #D97706;
    --success: #16A34A;
    --text-primary: #0F172A;
    --text-body: #1E293B;
    --text-secondary: #334155;
    --text-muted: #64748B;
    --tab-bg: #E2E8F0;
    --tab-active-bg: #FFFFFF;
    --input-bg: #FFFFFF;
    --input-border: #CBD5E1;
    --divider: linear-gradient(90deg, transparent, rgba(2, 132, 199, 0.3), transparent);
}

/* Base Streamlit App Container */
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] * {
    font-family: 'Inter', -apple-system, sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: var(--bg-page-gradient) !important;
    color: #1E293B !important;
}
[data-testid="stHeader"] {
    background: rgba(248, 250, 252, 0.85) !important;
    backdrop-filter: blur(10px);
}

/* Sidebar Styles */
[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1.5px solid var(--border-sidebar) !important;
}
[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
    color: #1E293B !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #334155 !important;
}
[data-testid="stSidebarNav"] span {
    color: #1E293B !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
[data-testid="stSidebarNav"] a {
    border-radius: 10px !important;
    margin: 3px 8px !important;
    padding: 8px 12px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(2, 132, 199, 0.1) !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: #E0F2FE !important;
    border-left: 4px solid #0284C7 !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span {
    color: #0369A1 !important;
    font-weight: 800 !important;
}

/* Headings & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #0F172A !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
}
p, span, div, li, label {
    color: #1E293B;
}
.section-header {
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 1.35rem !important;
    margin: 20px 0 10px 0;
}
.section-subtitle, .page-subtitle {
    font-size: 0.95rem !important;
    color: #475569 !important;
    font-weight: 500 !important;
    margin-bottom: 18px !important;
    line-height: 1.55 !important;
}

/* Universal Widget Labels */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stMarkdownContainer"] label,
.stSelectbox label, .stSelectbox label p,
.stSlider label, .stSlider label p,
.stTextInput label, .stTextInput label p,
.stTextArea label, .stTextArea label p,
.stNumberInput label, .stNumberInput label p,
.stDateInput label, .stDateInput label p,
.stColorPicker label, .stColorPicker label p,
.stCheckbox label, .stCheckbox label p {
    color: #0F172A !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}

/* Selectbox / Dropdowns */
[data-baseweb="select"],
[data-baseweb="select"] > div,
div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
}
[data-baseweb="select"] * {
    color: #0F172A !important;
}
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"] {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08) !important;
}
li[role="option"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
}
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background: #E0F2FE !important;
    color: #0284C7 !important;
}

/* Sliders */
[data-testid="stSlider"] div,
[data-testid="stSlider"] span,
[data-testid="stSlider"] p,
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"],
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    color: #0F172A !important;
    font-weight: 700 !important;
}

/* Text Inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    color: #0F172A !important;
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 10px !important;
}

/* Expanders */
[data-testid="stExpander"],
[data-testid="stExpander"] details,
.streamlit-expanderHeader,
.streamlit-expanderContent {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    background: #F8FAFC !important;
    border-radius: 11px 11px 0 0 !important;
    border-bottom: 1px solid #E2E8F0 !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #F1F5F9 !important;
}
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #0F172A !important;
    font-weight: 700 !important;
}
[data-testid="stExpander"] summary svg {
    fill: #0284C7 !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background: #FFFFFF !important;
    padding: 16px !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {
    color: #1E293B !important;
}

/* Primary Button */
button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0284C7, #0D9488) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25) !important;
}
button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4) !important;
    transform: translateY(-1px) !important;
}
button[data-testid="baseButton-primary"] * {
    color: #FFFFFF !important;
}

/* Secondary & Download Buttons */
[data-testid="stDownloadButton"] button,
.stDownloadButton button,
button[data-testid="baseButton-secondary"],
.stButton > button[kind="secondary"],
.stButton > button:not([kind="primary"]) {
    background: #FFFFFF !important;
    color: #0284C7 !important;
    border: 1.5px solid #0284C7 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 10px 18px !important;
    box-shadow: 0 2px 8px rgba(2, 132, 199, 0.1) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] button:hover,
.stDownloadButton button:hover,
button[data-testid="baseButton-secondary"]:hover,
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover {
    background: #E0F2FE !important;
    color: #0369A1 !important;
    border-color: #0369A1 !important;
    transform: translateY(-1px) !important;
}
[data-testid="stDownloadButton"] button *,
.stDownloadButton button *,
button[data-testid="baseButton-secondary"] *,
.stButton > button[kind="secondary"] * {
    color: inherit !important;
    fill: currentColor !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #F1F5F9 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 6px !important;
    border: 1px solid #E2E8F0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 9px 20px !important;
    font-weight: 600 !important;
    color: #475569 !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #0F172A !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0284C7 !important;
    font-weight: 800 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
}

/* Cards & Studio Components */
.glass-card, .section-card, .zone-card, .perf-card, .source-card, .step-card, .studio-card {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 16px !important;
    padding: 24px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
    color: #1E293B !important;
}
.glass-card p, .section-card p, .zone-card p, .step-card p, .studio-card p {
    color: #334155 !important;
    line-height: 1.6 !important;
}
.sat-hero-box {
    background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%) !important;
    border: 1.5px solid #BAE6FD !important;
    border-radius: 16px !important;
    padding: 28px 30px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 6px 24px rgba(2, 132, 199, 0.08) !important;
}
.sat-hero-box * {
    color: #0F172A !important;
}
.sat-badge-tag {
    display: inline-block !important;
    background: #E0F2FE !important;
    border: 1px solid #0284C7 !important;
    color: #0369A1 !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 4px 14px !important;
    border-radius: 20px !important;
    margin-bottom: 10px !important;
}

/* Metric Cards */
.metric-card {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px !important;
    padding: 20px 22px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}
.metric-card .mc-title { color: #64748B !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; }
.metric-card .mc-value { color: #0F172A !important; font-weight: 800 !important; font-size: 30px !important; }
.metric-card .mc-unit { color: #64748B !important; font-size: 16px !important; }

/* Border Container */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px !important;
}

/* Emergency Contacts Card */
.emergency-card {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px !important;
    padding: 20px 16px !important;
    text-align: center !important;
    margin-bottom: 14px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
}
.emergency-card .ec-name { font-size: 1.0rem !important; font-weight: 800 !important; color: #0F172A !important; }
.emergency-card .ec-number { font-size: 1.65rem !important; font-weight: 900 !important; }
.emergency-card .ec-badge { background: #F1F5F9 !important; color: #475569 !important; border: 1px solid #CBD5E1 !important; }

/* Evacuation Guide & Multi-lang */
.evac-guide-card, .multi-lang-card {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 12px !important;
    padding: 18px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
}
.evac-guide-card .eg-title, .multi-lang-card .ml-title { font-weight: 800 !important; color: #0F172A !important; }
.evac-guide-card .eg-body, .multi-lang-card .ml-body { color: #334155 !important; line-height: 1.6 !important; }

/* Alert Banners */
.alert-banner-red { background: #FEF2F2 !important; border: 2px solid #EF4444 !important; border-radius: 12px !important; padding: 20px !important; }
.alert-banner-red .ab-title { color: #B91C1C !important; font-weight: 900 !important; }
.alert-banner-red .ab-body { color: #7F1D1D !important; font-weight: 600 !important; }
.alert-banner-amber { background: #FFFBEB !important; border: 2px solid #F59E0B !important; border-radius: 12px !important; padding: 20px !important; }
.alert-banner-amber .ab-title { color: #B45309 !important; font-weight: 900 !important; }
.alert-banner-amber .ab-body { color: #78350F !important; font-weight: 600 !important; }
.alert-banner-green { background: #F0FDF4 !important; border: 2px solid #10B981 !important; border-radius: 12px !important; padding: 20px !important; }
.alert-banner-green .ab-title { color: #047857 !important; font-weight: 900 !important; }
.alert-banner-green .ab-body { color: #064E3B !important; font-weight: 600 !important; }

/* Chat Messages */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04) !important;
}
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span {
    color: #1E293B !important;
    font-size: 0.98rem !important;
    line-height: 1.65 !important;
}
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px !important;
}
[data-testid="stChatInput"] textarea {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}
</style>
"""
    else:
        # Dark Theme (Universal High-Contrast Dark Slate)
        return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg-page: #0B0F19;
    --bg-page-gradient: radial-gradient(circle at top right, #1E293B 0%, #0F172A 50%, #080D1A 100%);
    --bg-card: #131D31;
    --bg-card-subtle: rgba(255, 255, 255, 0.04);
    --bg-card-hover: #1E293B;
    --bg-card-rgb: 19, 29, 49;
    --bg-sidebar: linear-gradient(180deg, #0F172A 0%, #0B0F19 100%);
    --border-card: rgba(255, 255, 255, 0.14);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-sidebar: rgba(56, 189, 248, 0.22);
    --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.45);
    --shadow-card-hover: 0 16px 48px rgba(56, 189, 248, 0.22);
    --primary: #38BDF8;
    --primary-rgb: 56, 189, 248;
    --secondary: #2DD4BF;
    --accent: #818CF8;
    --danger: #FF1744;
    --warning: #FFD600;
    --success: #00C853;
    --text-primary: #FFFFFF;
    --text-body: #F1F5F9;
    --text-secondary: #CBD5E1;
    --text-muted: #94A3B8;
    --tab-bg: rgba(15, 23, 42, 0.7);
    --tab-active-bg: rgba(56, 189, 248, 0.22);
    --input-bg: #131D31;
    --input-border: rgba(56, 189, 248, 0.35);
    --divider: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.3), transparent);
}

/* Base Streamlit App Container */
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] * {
    font-family: 'Inter', -apple-system, sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: var(--bg-page-gradient) !important;
    color: #F1F5F9 !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}

/* Sidebar Styles */
[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1.5px solid var(--border-sidebar) !important;
}
[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #CBD5E1 !important;
}
[data-testid="stSidebarNav"] span {
    color: #F8FAFC !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
[data-testid="stSidebarNav"] a {
    border-radius: 10px !important;
    margin: 3px 8px !important;
    padding: 8px 12px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(56, 189, 248, 0.15) !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(56, 189, 248, 0.22) !important;
    border-left: 4px solid #38BDF8 !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span {
    color: #38BDF8 !important;
    font-weight: 800 !important;
}

/* Headings & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
}
p, span, div, li, label {
    color: #F1F5F9;
}
.section-header {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 1.35rem !important;
    margin: 20px 0 10px 0;
}
.section-subtitle, .page-subtitle {
    font-size: 0.95rem !important;
    color: #CBD5E1 !important;
    font-weight: 500 !important;
    margin-bottom: 18px !important;
    line-height: 1.55 !important;
}

/* Universal Widget Labels - 100% Bright Crisp White */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stMarkdownContainer"] label,
.stSelectbox label, .stSelectbox label p,
.stSlider label, .stSlider label p,
.stTextInput label, .stTextInput label p,
.stTextArea label, .stTextArea label p,
.stNumberInput label, .stNumberInput label p,
.stDateInput label, .stDateInput label p,
.stColorPicker label, .stColorPicker label p,
.stCheckbox label, .stCheckbox label p {
    color: #F8FAFC !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}

/* Selectbox / Dropdowns */
[data-baseweb="select"],
[data-baseweb="select"] > div,
div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] div {
    background: #131D31 !important;
    background-color: #131D31 !important;
    border: 1.5px solid rgba(56, 189, 248, 0.45) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
}
[data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #38BDF8 !important;
    color: #38BDF8 !important;
}
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"] {
    background: #131D31 !important;
    background-color: #131D31 !important;
    border: 1.5px solid rgba(56, 189, 248, 0.45) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6) !important;
}
li[role="option"] {
    background: #131D31 !important;
    background-color: #131D31 !important;
    color: #FFFFFF !important;
}
li[role="option"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background: #0284C7 !important;
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
}

/* Universal High-Contrast Alert Callouts */
[data-testid="stAlert"] {
    background-color: #131D31 !important;
    background: #131D31 !important;
    border-radius: 12px !important;
    border: 1.5px solid rgba(56, 189, 248, 0.45) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
}
[data-testid="stAlert"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Sliders */
[data-testid="stSlider"] div,
[data-testid="stSlider"] span,
[data-testid="stSlider"] p,
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"],
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    color: #F8FAFC !important;
    font-weight: 700 !important;
}

/* Text Inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    color: #FFFFFF !important;
    background: #131D31 !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 10px !important;
}

/* Expanders - NO WHITE BOXES IN DARK MODE */
[data-testid="stExpander"],
[data-testid="stExpander"] details,
.streamlit-expanderHeader,
.streamlit-expanderContent {
    background: #131D31 !important;
    border: 1.5px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    background: #1E293B !important;
    border-radius: 11px 11px 0 0 !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] summary:hover {
    background: rgba(56, 189, 248, 0.15) !important;
}
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
[data-testid="stExpander"] summary svg {
    fill: #38BDF8 !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background: #131D31 !important;
    padding: 16px !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {
    color: #CBD5E1 !important;
}

/* Primary Button */
button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0A84FF, #00C7BE) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 14px rgba(10, 132, 255, 0.3) !important;
}
button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(10, 132, 255, 0.45) !important;
    transform: translateY(-1px) !important;
}
button[data-testid="baseButton-primary"] * {
    color: #FFFFFF !important;
}

/* Secondary & Download Buttons - NO WHITE BUTTONS IN DARK MODE */
[data-testid="stDownloadButton"] button,
.stDownloadButton button,
button[data-testid="baseButton-secondary"],
.stButton > button[kind="secondary"],
.stButton > button:not([kind="primary"]) {
    background: #1E293B !important;
    color: #38BDF8 !important;
    border: 1.5px solid rgba(56, 189, 248, 0.45) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 10px 18px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] button:hover,
.stDownloadButton button:hover,
button[data-testid="baseButton-secondary"]:hover,
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover {
    background: #0284C7 !important;
    color: #FFFFFF !important;
    border-color: #38BDF8 !important;
    transform: translateY(-1px) !important;
}
[data-testid="stDownloadButton"] button *,
.stDownloadButton button *,
button[data-testid="baseButton-secondary"] *,
.stButton > button[kind="secondary"] * {
    color: inherit !important;
    fill: currentColor !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.7) !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 9px 20px !important;
    font-weight: 600 !important;
    color: #CBD5E1 !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #FFFFFF !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(56, 189, 248, 0.2) !important;
    color: #38BDF8 !important;
    font-weight: 800 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

/* Cards & Studio Components */
.glass-card, .section-card, .zone-card, .perf-card, .source-card, .step-card, .studio-card {
    background: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
    color: #F1F5F9 !important;
}
.glass-card p, .section-card p, .zone-card p, .step-card p, .studio-card p {
    color: #F1F5F9 !important;
    line-height: 1.6 !important;
}
.sat-hero-box {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95)) !important;
    border: 1.5px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 16px !important;
    padding: 28px 30px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4) !important;
}
.sat-hero-box * {
    color: #F8FAFC !important;
}
.sat-badge-tag {
    display: inline-block !important;
    background: rgba(56, 189, 248, 0.2) !important;
    border: 1px solid rgba(56, 189, 248, 0.5) !important;
    color: #38BDF8 !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 4px 14px !important;
    border-radius: 20px !important;
    margin-bottom: 10px !important;
}

/* Metric Cards */
.metric-card {
    background: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 14px !important;
    padding: 20px 22px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
}
.metric-card .mc-title { color: #94A3B8 !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; }
.metric-card .mc-value { color: #FFFFFF !important; font-weight: 800 !important; font-size: 30px !important; }
.metric-card .mc-unit { color: #94A3B8 !important; font-size: 16px !important; }

/* Border Container */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 14px !important;
}

/* Emergency Contacts Card */
.emergency-card {
    background: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 14px !important;
    padding: 20px 16px !important;
    text-align: center !important;
    margin-bottom: 14px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
}
.emergency-card .ec-name { font-size: 1.0rem !important; font-weight: 800 !important; color: #FFFFFF !important; }
.emergency-card .ec-number { font-size: 1.65rem !important; font-weight: 900 !important; }
.emergency-card .ec-badge { background: rgba(255, 255, 255, 0.08) !important; color: #CBD5E1 !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; }

/* Evacuation Guide & Multi-lang */
.evac-guide-card, .multi-lang-card {
    background: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 12px !important;
    padding: 18px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
}
.evac-guide-card .eg-title, .multi-lang-card .ml-title { font-weight: 800 !important; color: #FFFFFF !important; }
.evac-guide-card .eg-body, .multi-lang-card .ml-body { color: #F1F5F9 !important; line-height: 1.6 !important; }

/* Alert Banners */
.alert-banner-red { background: rgba(220, 38, 38, 0.22) !important; border: 2px solid #EF4444 !important; border-radius: 12px !important; padding: 20px !important; }
.alert-banner-red .ab-title { color: #FCA5A5 !important; font-weight: 900 !important; }
.alert-banner-red .ab-body { color: #FEE2E2 !important; font-weight: 600 !important; }
.alert-banner-amber { background: rgba(217, 119, 6, 0.22) !important; border: 2px solid #F59E0B !important; border-radius: 12px !important; padding: 20px !important; }
.alert-banner-amber .ab-title { color: #FCD34D !important; font-weight: 900 !important; }
.alert-banner-amber .ab-body { color: #FEF3C7 !important; font-weight: 600 !important; }
.alert-banner-green { background: rgba(5, 150, 105, 0.22) !important; border: 2px solid #10B981 !important; border-radius: 12px !important; padding: 20px !important; }
.alert-banner-green .ab-title { color: #6EE7B7 !important; font-weight: 900 !important; }
.alert-banner-green .ab-body { color: #D1FAE5 !important; font-weight: 600 !important; }

/* Chat Messages */
[data-testid="stChatMessage"] {
    background: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
}
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span {
    color: #F1F5F9 !important;
    font-size: 0.98rem !important;
    line-height: 1.65 !important;
}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div[data-baseweb="textarea"],
[data-testid="stChatInput"] div[data-baseweb="textarea"] > div,
.stChatFloatingInputContainer,
.stChatFloatingInputContainer > div {
    background: #131D31 !important;
    background-color: #131D31 !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    background-color: transparent !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #38BDF8 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(255, 255, 255, 0.6) !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.6) !important;
}
</style>
"""


def inject_theme_css(theme: str = None):
    """Inject the active theme's CSS into the current Streamlit page."""
    if theme is None:
        theme = init_theme()
    css_content = get_theme_css(theme)
    st.markdown(css_content, unsafe_allow_html=True)


def get_plotly_layout(theme: str = None, **overrides) -> dict:
    """
    Return a Plotly layout dictionary optimized for the given or active theme.
    Ensures high contrast, legible axis labels, and theme-matching backgrounds.
    """
    if theme is None:
        theme = st.session_state.get("theme", "dark")

    if theme == "light":
        layout = dict(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(family="Inter, sans-serif", color="#0F172A", size=12),
            margin=dict(l=160, r=40, t=50, b=50),
            legend=dict(
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor="#CBD5E1",
                borderwidth=1,
                font=dict(size=12, color="#0F172A"),
            ),
            xaxis=dict(
                gridcolor="rgba(0,0,0,0.06)",
                zerolinecolor="rgba(0,0,0,0.12)",
                tickfont=dict(size=12, color="#1E293B", family="Inter, sans-serif"),
                title=dict(font=dict(size=13, color="#0F172A")),
            ),
            yaxis=dict(
                gridcolor="rgba(0,0,0,0.06)",
                zerolinecolor="rgba(0,0,0,0.12)",
                tickfont=dict(size=12, color="#1E293B", family="Inter, sans-serif"),
                title=dict(font=dict(size=13, color="#0F172A")),
                automargin=True,
            ),
            hoverlabel=dict(
                bgcolor="#0F172A",
                bordercolor="#0284C7",
                font=dict(family="Inter, sans-serif", color="#FFFFFF", size=12),
            ),
        )
    else:
        layout = dict(
            paper_bgcolor="#131D31",
            plot_bgcolor="#0F172A",
            font=dict(family="Inter, sans-serif", color="#FFFFFF", size=12),
            margin=dict(l=160, r=40, t=50, b=50),
            legend=dict(
                bgcolor="rgba(15,23,42,0.85)",
                bordercolor="rgba(255,255,255,0.15)",
                borderwidth=1,
                font=dict(size=12, color="#FFFFFF"),
            ),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.1)",
                zerolinecolor="rgba(255,255,255,0.15)",
                tickfont=dict(size=12, color="#F8FAFC", family="Inter, sans-serif"),
                title=dict(font=dict(size=13, color="#FFFFFF")),
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.1)",
                zerolinecolor="rgba(255,255,255,0.15)",
                tickfont=dict(size=12, color="#F8FAFC", family="Inter, sans-serif"),
                title=dict(font=dict(size=13, color="#FFFFFF")),
                automargin=True,
            ),
            hoverlabel=dict(
                bgcolor="#0F172A",
                bordercolor="#38BDF8",
                font=dict(family="Inter, sans-serif", color="#FFFFFF", size=12),
            ),
        )

    layout.update(overrides)
    return layout
