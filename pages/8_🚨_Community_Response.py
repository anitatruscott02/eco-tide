import sys, os
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from utils.translations import TRANSLATIONS, EVACUATION_ROUTES
from utils.theme import init_theme, render_theme_switcher, inject_theme_css

# ── Dynamic Theme & High-Contrast CSS ───────────────────────────────────────
init_theme()
inject_theme_css()

# ── Language Selector & Sync ──────────────────────────────────────────────────
LANG_OPTIONS = {
    "en": "🇬🇧 English",
    "yo": "🇳🇬 Yoruba",
    "ig": "🇳🇬 Igbo",
    "ha": "🇳🇬 Hausa",
}

if "app_language" not in st.session_state:
    st.session_state.app_language = "en"

with st.sidebar:
    render_theme_switcher()

    st.markdown("### 🌍 Language / Ede / Asusuu / Harshe")
    sidebar_lang = st.selectbox(
        "Select Language", options=list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.keys()).index(st.session_state.app_language),
        format_func=lambda k: LANG_OPTIONS[k],
        key="comm_resp_sidebar_lang",
        label_visibility="collapsed"
    )
    if sidebar_lang != st.session_state.app_language:
        st.session_state.app_language = sidebar_lang
        st.rerun()
    st.markdown("---")

lang_choice = st.session_state.app_language
T = TRANSLATIONS[lang_choice]

# ── Load Risk Data ────────────────────────────────────────────────────────────
try:
    from models.risk_engine import compute_zone_risks, compute_community_risks
    from utils.data_loader import load_dataset, get_latest_data
    from config.settings import LAGOS_ZONES
    from config.lagos_communities import LAGOS_COMMUNITY_HOTSPOTS
    dataset = load_dataset()
    latest = get_latest_data(dataset, 1).iloc[-1]
    cur_wl = latest.get("water_level_m", 0.93)
    cur_rain = latest.get("rainfall_mm", 0)
    cur_wind = latest.get("wind_speed_ms", 8.0)
    cur_pres = latest.get("pressure_hpa", 1013)
    cur_soil = latest.get("soil_moisture", 0.3)
    
    zone_risks = compute_zone_risks(
        water_level_m=cur_wl,
        rainfall_mm=cur_rain,
        wind_speed_ms=cur_wind,
        pressure_hpa=cur_pres,
        soil_moisture=cur_soil
    )
    comm_risks = compute_community_risks(
        water_level_m=cur_wl,
        rainfall_mm=cur_rain,
        wind_speed_ms=cur_wind,
        pressure_hpa=cur_pres,
        soil_moisture=cur_soil
    )
    data_ok = True
except Exception:
    zone_risks = []
    comm_risks = []
    data_ok = False

red_zones   = [z for z in zone_risks if z["level"] == "red"]
amber_zones = [z for z in zone_risks if z["level"] == "amber"]

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding: 18px 0 10px 0;">
  <div style="font-size:2.3rem; font-weight:900; margin-bottom:6px; color:var(--text-primary);">
    🚨 <span style="background:linear-gradient(135deg,#EF4444,#F97316,#0284C7); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{T['page_title']}</span>
  </div>
  <div class="page-subtitle" style="font-size:1.02rem; font-weight:600; color:var(--text-secondary);">{T['page_subtitle']}</div>
</div>
""", unsafe_allow_html=True)

# Top language selector bar
lang_cols = st.columns(4)
for col, (l_key, l_label) in zip(lang_cols, LANG_OPTIONS.items()):
    with col:
        is_active = (l_key == lang_choice)
        btn_label = f"✓ {l_label}" if is_active else l_label
        if st.button(btn_label, key=f"top_resp_lang_btn_{l_key}", use_container_width=True):
            if st.session_state.app_language != l_key:
                st.session_state.app_language = l_key
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
# Direct backend cloud synchronization

# ── Section 1: Alert Banner ───────────────────────────────────────────────────
if red_zones:
    names_str = ", ".join([z["name"] for z in red_zones[:3]])
    st.markdown(f"""
    <div class="alert-banner-red">
      <div class="ab-title">🚨 {T['alert_red_title']}</div>
      <div class="ab-body"><b>{names_str}</b> {T['alert_red_body']}</div>
    </div>
    """, unsafe_allow_html=True)
elif amber_zones:
    names_str = ", ".join([z["name"] for z in amber_zones[:3]])
    st.markdown(f"""
    <div class="alert-banner-amber">
      <div class="ab-title">⚠️ {T['alert_amber_title']}</div>
      <div class="ab-body"><b>{names_str}</b> {T['alert_amber_body']}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alert-banner-green">
      <div class="ab-title">{T['alert_green_title']}</div>
      <div class="ab-body">{T['alert_green_body']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="eco-divider" style="margin: 14px 0 20px 0;"></div>', unsafe_allow_html=True)

# ── Section 2: Evacuation Guide ───────────────────────────────────────────────
st.markdown(f"""
<div style="font-size:1.4rem; font-weight:800; color:var(--accent-orange); margin-bottom:4px;">
  🚗 {T['evac_title']}
</div>
<div class="section-subtitle">{T['evac_subtitle']}</div>
""", unsafe_allow_html=True)

col_map, col_cards = st.columns([3, 2], gap="large")

with col_map:
    evac_view = st.radio(
        "Evacuation Scope:",
        options=["🏘️ Specific Street & Community Hotspots", "🏛️ Local Government Area (LGA) Overview"],
        index=0,
        horizontal=True,
        key="evac_scope_radio"
    )
    
    if "Community Hotspots" in evac_view and comm_risks:
        c_rows = []
        for c in comm_risks:
            c_rows.append({
                "Community": f"{c['community']} ({c['parent_lga']})",
                "Hotspot Streets": c["hotspot_streets"],
                "Risk": f"{c.get('icon','')} {c.get('label','')}",
                "Elevation": f"{c['elevation_m']:.1f} m",
                "Safe Evacuation Point": c["safe_evacuation_point"]
            })
        df_c = pd.DataFrame(c_rows)
        st.dataframe(
            df_c, use_container_width=True, hide_index=True,
            height=420,
            column_config={
                "Risk": st.column_config.TextColumn(width="small"),
                "Elevation": st.column_config.TextColumn(width="small"),
            }
        )
    else:
        rows = []
        for z in zone_risks if zone_risks else []:
            safe, dist, route = EVACUATION_ROUTES.get(
                z["name"], ("Nearest Mainland", "Varies", "Main Highway"))
            rows.append({
                T["table_lga"]:       z["name"],
                T["table_risk"]:      f"{z.get('icon','')} {z.get('label','')}",
                T["table_safe_zone"]: safe,
                T["table_distance"]:  dist,
                T["table_route"]:     route,
            })
        if rows:
            df_evac = pd.DataFrame(rows)
            st.dataframe(
                df_evac, use_container_width=True, hide_index=True,
                height=420,
                column_config={
                    T["table_risk"]: st.column_config.TextColumn(width="small"),
                    T["table_distance"]: st.column_config.TextColumn(width="small"),
                }
            )
        else:
            st.info("Loading evacuation data...")

with col_cards:
    for icon, title, body, clr in [
        ("🏃", T["when_evac_title"], T["when_evac_body"], "var(--danger)"),
        ("🚗", T["how_evac_title"], T["how_evac_body"], "var(--warning)"),
        ("📞", T["who_call_title"], T["who_call_body"], "var(--primary)"),
    ]:
        st.markdown(f"""
        <div class="evac-guide-card" style="border-left: 4px solid {clr};">
          <div class="eg-title" style="color:{clr};">{icon} {title}</div>
          <div class="eg-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="eco-divider" style="margin: 14px 0 20px 0;"></div>', unsafe_allow_html=True)

# ── Section 3: Emergency Contacts ────────────────────────────────────────────
st.markdown(f"""
<div style="font-size:1.4rem; font-weight:800; color:var(--primary); margin-bottom:4px;">
  📞 {T['contacts_title']}
</div>
<div class="section-subtitle">{T['contacts_subtitle']}</div>
""", unsafe_allow_html=True)

contacts = [
    ("🏛", "LASEMA",             "767",              "#E11D48"),
    ("🇳🇬", "NEMA",              "0800-2255-6362",   "#EA580C"),
    ("🔥", "Federal Fire",       "01-7944927",       "#D97706"),
    ("🏥", "Nigerian Red Cross", "01-8700920",       "#DC2626"),
    ("🚔", "Police Emergency",   "112",              "#0284C7"),
    ("🚑", "Ambulance",         "199",              "#16A34A"),
]

cols = st.columns(3)
for i, (icon, name, number, color) in enumerate(contacts):
    with cols[i % 3]:
        st.markdown(f"""
        <div class="emergency-card" style="border-top: 3px solid {color};">
          <div class="ec-icon">{icon}</div>
          <div class="ec-name">{name}</div>
          <div class="ec-number" style="color:{color};">{number}</div>
          <div class="ec-badge">📋 Save this number</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="eco-divider" style="margin: 14px 0 20px 0;"></div>', unsafe_allow_html=True)

# ── Section 4: 72-Hour Checklist ─────────────────────────────────────────────
st.markdown(f"""
<div style="font-size:1.4rem; font-weight:800; color:var(--accent-purple); margin-bottom:4px;">
  ✅ {T['checklist_title']}
</div>
<div class="section-subtitle">{T['checklist_subtitle']}</div>
""", unsafe_allow_html=True)

col_b, col_d = st.columns(2, gap="large")
checked_total = 0
total_items = len(T["before_items"]) + len(T["during_items"])

with col_b:
    st.markdown(f"**{T['before_flood']}**")
    for item in T["before_items"]:
        if st.checkbox(item, key=f"chk_b_{item[:20]}_{lang_choice}"):
            checked_total += 1

with col_d:
    st.markdown(f"**{T['during_flood']}**")
    for item in T["during_items"]:
        if st.checkbox(item, key=f"chk_d_{item[:20]}_{lang_choice}"):
            checked_total += 1

pct = checked_total / total_items if total_items > 0 else 0
st.progress(pct, text=f"{T['progress_label']}: {checked_total}/{total_items} ({int(pct*100)}%)")

if pct == 1.0:
    st.success(f"💪 {T['well_done']}")
elif pct >= 0.7:
    st.warning(T["almost"])
elif pct >= 0.3:
    st.info(T["getting_there"])
else:
    st.error(f"⚠️ {T['start_now']}")

st.markdown('<div class="eco-divider" style="margin: 14px 0 20px 0;"></div>', unsafe_allow_html=True)

# ── Section 5: Multi-language Alert Panel ────────────────────────────────────
st.markdown(f"""
<div style="font-size:1.4rem; font-weight:800; color:var(--accent-green); margin-bottom:4px;">
  📢 {T['lang_title']}
</div>
<div class="section-subtitle">{T['lang_subtitle']}</div>
""", unsafe_allow_html=True)

lang_cards = [
    ("🇬🇧", "English",  TRANSLATIONS["en"]["alert_msg"], "#0284C7"),
    ("🇳🇬", "Yoruba",   TRANSLATIONS["yo"]["alert_msg"], "#EA580C"),
    ("🇳🇬", "Igbo",     TRANSLATIONS["ig"]["alert_msg"], "#7C3AED"),
    ("🇳🇬", "Hausa",    TRANSLATIONS["ha"]["alert_msg"], "#059669"),
]

c1, c2 = st.columns(2)
for i, (flag, name, msg, color) in enumerate(lang_cards):
    col = c1 if i % 2 == 0 else c2
    with col:
        st.markdown(f"""
        <div class="multi-lang-card" style="border-left: 4px solid {color};">
          <div class="ml-title">{flag} <b style="color:{color};">{name}</b></div>
          <div class="ml-body">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center; padding:24px 0 8px 0; font-size:0.8rem; color:var(--text-muted);">
  Eco-Tide Community Response System &middot; Powered by AI + Copernicus Satellite Data<br>
  In an emergency, always follow official NEMA / LASEMA instructions.
</div>
""", unsafe_allow_html=True)
