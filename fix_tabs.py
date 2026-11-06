# -*- coding: utf-8 -*-
"""Patch chat page: add geolocation 3-tab layout and My Location tab."""
import sys

PAGE = "pages/9_\U0001f4ac_Community_Chat.py"

with open(PAGE, encoding="utf-8") as f:
    src = f.read()

# ────────────────────────────────────────────────────────────────────────────
# PATCH 1 – Replace tab definition to support optional 3rd tab
# ────────────────────────────────────────────────────────────────────────────
MARK_TABS = "tab_chat, tab_reports = st.tabs(["

if MARK_TABS not in src:
    print("ERROR: tab definition marker not found")
    sys.exit(1)

# Find start of the full comment + assignment block
comment_marker = "\u2500\u2500 Navigation Tabs"
comment_start = src.rfind("#", 0, src.index(MARK_TABS))
# Find closing "])" of st.tabs
close_tabs = src.index("])", src.index(MARK_TABS)) + 2

OLD_BLOCK = src[comment_start:close_tabs]
print("OLD_BLOCK found, length:", len(OLD_BLOCK))

NEW_BLOCK = (
    "# \u2500\u2500 Navigation Tabs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "if _GEO_OK:\n"
    "    tab_chat, tab_location, tab_reports = st.tabs([\n"
    "        f\"\U0001f916 AI Emergency Assistant ({LANG_OPTIONS[lang]})\",\n"
    "        \"\U0001f4cd My Location \u0026 Local Risk\",\n"
    "        \"\U0001f4e2 Community Incident Reports\",\n"
    "    ])\n"
    "else:\n"
    "    tab_chat, tab_reports = st.tabs([\n"
    "        f\"\U0001f916 AI Emergency Assistant ({LANG_OPTIONS[lang]})\",\n"
    "        \"\U0001f4e2 Community Incident Reports\",\n"
    "    ])\n"
    "    tab_location = None"
)

src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
print("PATCH 1 OK")

# ────────────────────────────────────────────────────────────────────────────
# PATCH 2 – Insert My Location tab block before "with tab_reports:"
# ────────────────────────────────────────────────────────────────────────────
INSERT_BEFORE = "\nwith tab_reports:\n"
if INSERT_BEFORE not in src:
    print("ERROR: 'with tab_reports:' not found")
    sys.exit(1)

LOC_TAB = (
    "\n"
    "# \u2500\u2500 My Location Tab \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "if _GEO_OK and tab_location is not None:\n"
    "    with tab_location:\n"
    "        from config.settings import LAGOS_ZONES\n"
    "        st.markdown(\n"
    "            \"<div style='font-size:0.88rem; color:var(--text-secondary); margin-bottom:14px; line-height:1.6;'>\"\n"
    "            \"\U0001f510 <b>Privacy first</b> &mdash; GPS is only used to find your nearest LGA. \"\n"
    "            \"Coordinates are <b>never</b> shared unless you submit a GPS report.\"\n"
    "            \"</div>\",\n"
    "            unsafe_allow_html=True\n"
    "        )\n"
    "        _col_l, _col_r = st.columns([1, 1], gap=\"large\")\n"
    "        with _col_l:\n"
    "            st.markdown(\"#### \U0001f4cd Enable Location\")\n"
    "            user_loc = render_location_card(\n"
    "                zone_risks=zone_risks,\n"
    "                zones=LAGOS_ZONES,\n"
    "                theme=current_theme,\n"
    "            )\n"
    "            if not user_loc:\n"
    "                st.markdown(\n"
    "                    \"<div style='margin-top:16px; font-size:0.82rem; color:var(--text-muted); line-height:1.9;'>\"\n"
    "                    \"<b style='color:var(--text-secondary)'>How it works on mobile:</b><br>\"\n"
    "                    \"1. Tap <b>Share My Location</b><br>\"\n"
    "                    \"2. Tap <b>Allow</b> when prompted<br>\"\n"
    "                    \"3. Your nearest LGA and flood risk appear instantly<br>\"\n"
    "                    \"4. Optionally submit a GPS-tagged report\"\n"
    "                    \"</div>\",\n"
    "                    unsafe_allow_html=True\n"
    "                )\n"
    "        with _col_r:\n"
    "            st.markdown(\"#### \U0001f30a Your Area Risk\")\n"
    "            if user_loc:\n"
    "                _nn = st.session_state.get(\"user_nearest_zone\")\n"
    "                _nz = next((z for z in LAGOS_ZONES if z[\"name\"] == _nn), None)\n"
    "                if _nz:\n"
    "                    _rm = next((z for z in zone_risks if z[\"name\"] == _nn), None)\n"
    "                    _lv = _rm[\"level\"] if _rm else \"green\"\n"
    "                    _acts = {\n"
    "                        \"red\":   (\"\U0001f6a8 EVACUATE NOW\",  \"#FF6B6B\", \"Move to high ground. Call LASEMA: 767\"),\n"
    "                        \"amber\": (\"\u26a0\ufe0f PREPARE NOW\",   \"#FBBF24\", \"Prepare go-bag. Monitor closely.\"),\n"
    "                        \"green\": (\"\u2705 CURRENTLY SAFE\", \"#4ADE80\", \"No immediate flood risk.\"),\n"
    "                    }\n"
    "                    _al, _ac, _ad = _acts.get(_lv, _acts[\"green\"])\n"
    "                    st.markdown(\n"
    "                        f\"<div style='background:var(--bg-card); border:1px solid var(--border-card); \"\n"
    "                        f\"border-radius:14px; padding:20px; margin-bottom:16px;'>\"\n"
    "                        f\"<div style='font-size:0.72rem; color:var(--text-muted); font-weight:700; \"\n"
    "                        f\"text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>Recommended Action</div>\"\n"
    "                        f\"<div style='font-size:1.2rem; font-weight:900; color:{_ac}; margin-bottom:6px;'>{_al}</div>\"\n"
    "                        f\"<div style='font-size:0.9rem; color:var(--text-secondary); line-height:1.55;'>{_ad}</div>\"\n"
    "                        f\"<hr style='border-color:var(--border-card); margin:14px 0;'>\"\n"
    "                        f\"<div style='font-size:0.82rem; color:var(--text-muted); line-height:1.8;'>\"\n"
    "                        f\"\U0001f3d9 <b>Notable:</b> {_nz.get('notable_areas','')}<br>\"\n"
    "                        f\"\U0001f4ca <b>Population:</b> {_nz.get('population', 0):,}<br>\"\n"
    "                        f\"\U0001f4a7 <b>Drainage:</b> {int(_nz.get('drainage_capacity', 0)*100)}%<br>\"\n"
    "                        f\"\U0001f30a <b>About:</b> {_nz.get('description','')}\"\n"
    "                        \"</div></div>\",\n"
    "                        unsafe_allow_html=True\n"
    "                    )\n"
    "                    if _lv in (\"red\", \"amber\"):\n"
    "                        st.error(\"\U0001f4de LASEMA: 767  |  NEMA: 0800-2255-6362\", icon=\"\U0001f6a8\")\n"
    "            else:\n"
    "                st.markdown(\n"
    "                    \"<div style='background:var(--bg-card); border:1px solid var(--border-card); \"\n"
    "                    \"border-radius:14px; padding:28px; text-align:center;'>\"\n"
    "                    \"<div style='font-size:3rem; margin-bottom:10px;'>\U0001f4cd</div>\"\n"
    "                    \"<div style='font-size:1rem; font-weight:700; color:var(--text-secondary);'>Waiting for location...</div>\"\n"
    "                    \"<div style='font-size:0.82rem; color:var(--text-muted); margin-top:6px;'>Enable GPS on the left</div>\"\n"
    "                    \"</div>\",\n"
    "                    unsafe_allow_html=True\n"
    "                )\n"
    "        if user_loc:\n"
    "            st.markdown(\"---\")\n"
    "            st.markdown(\"#### \U0001f4e1 Submit GPS-Tagged Flood Report\")\n"
    "            st.markdown(\n"
    "                f\"<div style='font-size:0.83rem; color:var(--text-secondary); margin-bottom:12px;'>\"\n"
    "                f\"Tagged: <b>({user_loc['lat']:.4f}\u00b0N, {user_loc['lon']:.4f}\u00b0E)</b> \u2014 \"\n"
    "                f\"linked to <b>{st.session_state.get('user_nearest_zone', 'your area')}</b>.\"\n"
    "                \"</div>\",\n"
    "                unsafe_allow_html=True,\n"
    "            )\n"
    "            with st.form(\"geo_report_form\", clear_on_submit=True):\n"
    "                from config.settings import LAGOS_ZONES as _lz2\n"
    "                _lga_n = [z[\"name\"] for z in _lz2]\n"
    "                _auto2 = st.session_state.get(\"user_nearest_zone\", _lga_n[0])\n"
    "                _idx2  = _lga_n.index(_auto2) if _auto2 in _lga_n else 0\n"
    "                gr_lga  = st.selectbox(\"LGA (GPS auto-detected \u2713)\", _lga_n, index=_idx2)\n"
    "                gr_name = st.text_input(\"Your Name / Alias (optional)\")\n"
    "                gr_sev  = st.select_slider(\"Severity\", options=[\"Low\",\"Medium\",\"High\",\"Critical\"], value=\"Medium\")\n"
    "                gr_dep  = st.number_input(\"Water depth (cm)\", 0, 300, 10)\n"
    "                gr_msg  = st.text_area(\"What are you seeing?\",\n"
    "                                       placeholder=\"e.g. Road flooded at junction, cars stranded...\")\n"
    "                gr_go   = st.form_submit_button(\"\U0001f4e1 Send GPS Report\", type=\"primary\", use_container_width=True)\n"
    "                if gr_go and gr_msg.strip():\n"
    "                    _ok2, _fb2 = submit_community_report({\n"
    "                        \"lga\":       gr_lga,\n"
    "                        \"reporter\":  gr_name.strip() or \"GPS Reporter (Anonymous)\",\n"
    "                        \"severity\":  gr_sev,\n"
    "                        \"water_cm\":  f\"{gr_dep} cm\",\n"
    "                        \"msg\":       gr_msg.strip(),\n"
    "                        \"lat\":       user_loc[\"lat\"],\n"
    "                        \"lon\":       user_loc[\"lon\"],\n"
    "                        \"accuracy_m\": user_loc.get(\"accuracy_m\"),\n"
    "                    })\n"
    "                    if _ok2:\n"
    "                        st.success(_fb2)\n"
    "                        st.balloons()\n"
    "                    else:\n"
    "                        st.error(_fb2)\n"
)

src = src.replace(INSERT_BEFORE, LOC_TAB + INSERT_BEFORE, 1)
print("PATCH 2 OK")

with open(PAGE, "w", encoding="utf-8") as f:
    f.write(src)

print("File written. Verifying syntax...")
import py_compile
try:
    py_compile.compile(PAGE, doraise=True)
    print("SYNTAX OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
