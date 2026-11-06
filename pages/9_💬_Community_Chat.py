import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from utils.theme import init_theme, inject_theme_css, render_theme_switcher
from utils.supabase_client import (
    fetch_community_reports,
    submit_community_report,
    is_connected,
    save_chat_message,
    fetch_chat_messages,
)
try:
    from components.geolocation import render_location_card, render_location_widget, get_nearest_zone
    _GEO_OK = True
except Exception:
    _GEO_OK = False

current_theme = init_theme()
inject_theme_css(current_theme)

# ── Translation & Knowledge Base ─────────────────────────────────────────────
try:
    from utils.translations import TRANSLATIONS, EVACUATION_ROUTES
except Exception:
    TRANSLATIONS = {}
    EVACUATION_ROUTES = {}

try:
    from models.risk_engine import compute_zone_risks, compute_community_risks, find_community_or_zone
    from config.lagos_communities import LAGOS_COMMUNITY_HOTSPOTS
    from utils.data_loader import load_dataset, get_latest_data
    dataset = load_dataset()
    latest  = get_latest_data(dataset, 1).iloc[-1]
    zone_risks = compute_zone_risks(
        water_level_m=latest.get("water_level_m", 0.5),
        rainfall_mm=latest.get("rainfall_mm", 0),
        wind_speed_ms=latest.get("wind_speed_ms", 0),
        pressure_hpa=latest.get("pressure_hpa", 1013),
    )
    red_zones   = [z["name"] for z in zone_risks if z["level"] == "red"]
    amber_zones = [z["name"] for z in zone_risks if z["level"] == "amber"]
    data_ok = True
except Exception:
    zone_risks  = []
    red_zones   = []
    amber_zones = []
    data_ok     = False

# ── Knowledge Base (multilingual bot responses) ───────────────────────────────
KB = {
    "en": {
        "greeting": (
            "Hello! I am the Eco-Tide Flood Assistant. I can help you with:\n\n"
            "- 🌊 **Current flood risk** in your area\n"
            "- 🚗 **Evacuation routes** from any Lagos LGA\n"
            "- 📞 **Emergency contacts** (NEMA, LASEMA)\n"
            "- ✅ **Flood preparedness tips**\n"
            "- 🌧️ **What to do during a flood**\n\n"
            "Select your preferred language above or type your question below!"
        ),
        "status": lambda: (
            f"🔴 **ACTIVE SURGE WARNING:** {', '.join(red_zones)} {'are' if len(red_zones)>1 else 'is'} at elevated risk!\n\n"
            f"🟡 **ELEVATED CAUTION:** {', '.join(amber_zones)} {'are' if len(amber_zones)>1 else 'is'} under tidal watch.\n\n"
            f"🟢 {20 - len(red_zones) - len(amber_zones)} zones are currently safe."
            if (red_zones or amber_zones) else
            f"🟢 **ALL CLEAR (Normal Conditions):** All 20 Lagos LGAs and 25+ monitored community hotspots are currently safe.\n\n"
            f"• **Current Ocean Water Level:** {latest.get('water_level_m', 0.93):.2f}m (normal daily tide, well within the 2.0m surge danger threshold)\n"
            f"• **Rainfall:** {latest.get('rainfall_mm', 0.0):.1f} mm/hr\n"
            f"• **Wind Setup:** {latest.get('wind_speed_ms', 8.0):.1f} m/s (moderate tropical breeze)\n"
            f"• **Status:** Natural tidal flow within seawalls and canals. Zero flood danger detected anywhere in Lagos."
        ),
        "evacuate": (
            "🚗 **How to evacuate safely:**\n\n"
            "1. Leave **immediately** — do not wait for the flood to reach your door\n"
            "2. Use designated evacuation routes (see Risk Map page)\n"
            "3. **Never** drive or walk through moving floodwater\n"
            "4. Bring your go-bag: water, food, medicines, documents\n"
            "5. Use bridges (Carter, Eko, 3rd Mainland) — avoid low roads\n"
            "6. Keep children and elderly ahead of you\n\n"
            "**Key routes:**\n"
            "- Lekki/Ibeju-Lekki → Epe via Lekki-Epe Expressway\n"
            "- Apapa → Surulere via Apapa-Oshodi Expressway\n"
            "- Lagos Island → Mainland via Carter/Eko Bridge"
        ),
        "contacts": (
            "📞 **Emergency Contacts — Save these NOW:**\n\n"
            "| Agency | Number |\n"
            "|--------|--------|\n"
            "| 🏛 LASEMA | **767** |\n"
            "| 🇳🇬 NEMA | **0800-2255-6362** |\n"
            "| 🔥 Federal Fire | **01-7944927** |\n"
            "| 🏥 Red Cross | **01-8700920** |\n"
            "| 🚔 Police | **112** |\n"
            "| 🚑 Ambulance | **199** |"
        ),
        "prepare": (
            "✅ **72-Hour Flood Preparedness:**\n\n"
            "**Store now:**\n"
            "- 3 litres of water per person per day (72 hrs = 9 litres each)\n"
            "- Non-perishable food (canned goods, biscuits)\n"
            "- Medicines, first aid kit\n"
            "- Torch/lantern + extra batteries\n"
            "- Power bank (fully charged)\n\n"
            "**Protect documents:**\n"
            "- Put NIMC card, land papers, passports in a waterproof bag\n\n"
            "**Know your route:**\n"
            "- Ask a neighbour where the nearest high-ground area is\n"
            "- Tell your family your meeting point"
        ),
        "during": (
            "🌊 **What to do DURING a flood:**\n\n"
            "❌ **DO NOT:**\n"
            "- Walk through moving water (30cm can knock you down)\n"
            "- Drive through flooded roads\n"
            "- Touch electrical equipment near water\n\n"
            "✅ **DO:**\n"
            "- Turn off electricity at the main switch\n"
            "- Move to the highest floor or rooftop\n"
            "- Signal for help with a bright cloth or torch\n"
            "- Call LASEMA: **767** for rescue\n"
            "- Stay calm — help is coming"
        ),
        "fallback": (
            "I am not sure about that. You can ask me about:\n\n"
            "- The **current flood risk** status\n"
            "- **Evacuation routes** from your area\n"
            "- **Emergency phone numbers**\n"
            "- **What to prepare** before a flood\n"
            "- **What to do** during a flood"
        ),
        "quick_btns": ["🌊 Current Risk Status", "🚗 How to Evacuate", "📞 Emergency Numbers", "✅ How to Prepare", "🌧 During a Flood"],
        "input_placeholder": "Type your question here... (e.g. 'Is Apapa safe?' or 'How do I evacuate?')",
        "you": "You",
        "bot": "Eco-Tide Assistant",
        "powered": "Powered by Eco-Tide AI • Responds in your language",
    },
    "yo": {
        "greeting": (
            "Bawo! Emi ni Oluranlowo Ishan-Omi Eco-Tide. Mo le ran e lowo pelu:\n\n"
            "- Ewu ishan-omi lonii ni agbegbe re\n"
            "- Awon oonaa isa lati LGA eyikeyi ni Eko\n"
            "- Awon nombaa afonifoji (NEMA, LASEMA)\n"
            "- Awon imoran lati mura fun ishan-omi\n"
            "- Ohun ti o yee se nigba ishan-omi\n\n"
            "Yan ede re loke tabi beere ibeere re nisalẹ!"
        ),
        "status": lambda: (
            f"Ewu: {', '.join(red_zones)} wa ninu eewu ishan-omi giga - sa lo lesekese!\n\n"
            f"Ikilowo: {', '.join(amber_zones)} wa ninu ewu.\n\n"
            f"{20 - len(red_zones) - len(amber_zones)} agbegbe lo wa ni abo."
            if (red_zones or amber_zones) else
            "Abo: Gbogbo agbegbe 20 ni Eko lo wa ni abo loni. Ko si ewu ishan-omi."
        ),
        "evacuate": (
            "Bawo ni a se le sa ni ailewu:\n\n"
            "1. Fi ile re sile LESEKESE - maree duro de ki omi to de\n"
            "2. Lo awon oonaa isa ti a ti pin\n"
            "3. MA SE wakoo tabi rin ninu omi ishan ti n san\n"
            "4. Fi apo re mu: omi, ounje, oogun, iwe pataki\n"
            "5. Lo afara (Carter, Eko, 3rd Mainland)\n\n"
            "Awon oonaa pataki:\n"
            "- Lekki/Ibeju-Lekki si Epe nipasee Lekki-Epe Expressway\n"
            "- Apapa si Surulere nipasee Apapa-Oshodi Expressway\n"
            "- Lagos Island si Mainland nipasee Carter/Eko Bridge"
        ),
        "contacts": (
            "Awon Nombaa Ijagidijagan - Fi won pamo BAYII:\n\n"
            "LASEMA: 767\n"
            "NEMA: 0800-2255-6362\n"
            "Ina Agbegbe: 01-7944927\n"
            "Red Cross: 01-8700920\n"
            "Olopaa: 112\n"
            "Ambulance: 199"
        ),
        "prepare": (
            "Imurasile fun 72 wakati:\n\n"
            "Fi pamoo:\n"
            "- Lita 3 omi mimu fun eniyan kookan fun ojo\n"
            "- Ounje ti ko ba jee (ounjee akolo, biscuit)\n"
            "- Oogun ati nkan itojuu\n"
            "- Fitila ati batiri afikun\n\n"
            "Dabobo awon iwe:\n"
            "- Fi kaadi NIMC, iwe ile, iwe irin-ajo sinu apo omi-ko-le-wole\n\n"
            "Mo oonaa re:\n"
            "- Beere awon aladugbo nibo ibi giga to sunmo wa"
        ),
        "during": (
            "Ohun ti o yee se NIGBA ishan-omi:\n\n"
            "MA SE:\n"
            "- Rin ninu omi ti n san (30cm le da e sile)\n"
            "- Wakoo ninu iti omi\n"
            "- Fowo kan ero amona nitosi omi\n\n"
            "YEE SE:\n"
            "- Pa amona ni oonaa akookan\n"
            "- Lo si ipo giga tabi orule ile\n"
            "- Pe LASEMA: 767 fun igbaala"
        ),
        "fallback": (
            "Ami ko mo ohun ti o nii. O le beere mi nipa:\n\n"
            "- Ipo ewu ishan-omi lonii\n"
            "- Awon oonaa isa lati agbegbe re\n"
            "- Awon nombaa afonifoji\n"
            "- Bawo ni a se le mura\n"
            "- Ohun ti o yee se nigba ishan-omi"
        ),
        "quick_btns": ["Ipo Ewu Lonii", "Bawo ni a Se Sa", "Nombaa Afonifoji", "Bawo ni a Se Mura", "Nigba Ishan-Omi"],
        "input_placeholder": "Beere ibeere re nibi... (fap. 'Njee Apapa wa ni abo?' tabi 'Bawo ni mo se le sa?')",
        "you": "Iwo",
        "bot": "Oluranlowo Eco-Tide",
        "powered": "Agbara Eco-Tide AI • Dahun ni ede re",
    },
    "ig": {
        "greeting": (
            "Nnoo! Abu m Onye Enyemaka Mmiri Ozuzo nke Eco-Tide. Nwere ike inyere gi aka na:\n\n"
            "- Ihe ize nduu mmiri ozuzo taa n'mpaghara gi\n"
            "- Uzo ipuo si LGA obula na Lagos\n"
            "- Namba mberede (NEMA, LASEMA)\n"
            "- Nduzi idi njikere maka mmiri ozuzo\n"
            "- Ihe i ga-eme n'oge mmiri ozuzo\n\n"
            "Horoo asusuu gi n'elu ma o bu juo ajuuajuu gi n'ala!"
        ),
        "status": lambda: (
            f"Ihere: {', '.join(red_zones)} di na ihere mmiri ozuzo diri elu - puoo ozugbo!\n\n"
            f"Nduzi: {', '.join(amber_zones)} di n'ihe ize ndu.\n\n"
            f"Mpaghara {20 - len(red_zones) - len(amber_zones)} di nchebe."
            if (red_zones or amber_zones) else
            "Odimma: Mpaghara 20 niile na Lagos di nchebe taa. Enyeghi ihe ize ndu mmiri."
        ),
        "evacuate": (
            "Otu esi apuo na nchedo:\n\n"
            "1. Hapuoo OZUGBO - echeghikwa ka mmiri abiakwuo n'uzo gi\n"
            "2. Jiri uzo ipuo e depuutara\n"
            "3. EMEGHII iga ma o bu iqha elu n'ime mmiri na-agbapuo\n"
            "4. Bulie akpa gi: mmiri, nri, ogwu, akwukwo diri mkpa\n"
            "5. Jiri uzo ngwugwu (Carter, Eko, 3rd Mainland)\n\n"
            "Uzo diri mkpa:\n"
            "- Lekki/Ibeju-Lekki gaa Epe site na Lekki-Epe Expressway\n"
            "- Apapa gaa Surulere site na Apapa-Oshodi Expressway"
        ),
        "contacts": (
            "Namba Mberede - Chekwaa Ha UGBU A:\n\n"
            "LASEMA: 767\n"
            "NEMA: 0800-2255-6362\n"
            "Oku Obodo: 01-7944927\n"
            "Red Cross: 01-8700920\n"
            "Ndi Uwe Ojii: 112\n"
            "Ogwu Ochichoo: 199"
        ),
        "prepare": (
            "Idi Njikere Maka Awa 72:\n\n"
            "Chekwaa ugbu a:\n"
            "- Lita 3 mmiri oonuu maka onye obula n'ubochi\n"
            "- Nri nke anaghii ure ngwa ngwa (akolo, biscuit)\n"
            "- Ogwu na ihe odi mma nke mbu\n"
            "- Torchlight na batriii oji\n\n"
            "Chebe akwukwo:\n"
            "- Tinye kaad NIMC, akwukwo ala, paasipoot n'ime akpa mmiri\n\n"
            "Mara uzo gi:\n"
            "- Juo ndukoo gi ebe diri elu nso"
        ),
        "during": (
            "Ihe I Ga-Eme N'OGE Mmiri Ozuzo:\n\n"
            "EMEGHII:\n"
            "- Iga n'ime mmiri na-agbapuo (30cm nwere ike iwepu gi)\n"
            "- Iqha elu n'uzo juputara na mmiri\n"
            "- Idi nso na ihe eletriki n'akuku mmiri\n\n"
            "MEE:\n"
            "- Gbanyuoo oku elektrik n'isi ya\n"
            "- Gaa n'elu ulo ma o bu elu ulo\n"
            "- Kpooo LASEMA: 767 maka izoputa"
        ),
        "fallback": (
            "Amaghim ihe i chee. Nwere ike ijuo ajuuajuu banyere:\n\n"
            "- Nnoo diri ugbu a nke ihe ize ndu mmiri\n"
            "- Uzo ipuo si mpaghara gi\n"
            "- Namba ekwu poghe\n"
            "- Otu esi idi njikere\n"
            "- Ihe i ga-eme n'oge mmiri ozuzo"
        ),
        "quick_btns": ["Nnoo Mmiri Taa", "Otu Esi Apuo", "Namba Mberede", "Otu Esi Di Njikere", "N'oge Mmiri"],
        "input_placeholder": "Juo ajuuajuu gi ebe a... (dika 'Apapa di nchebe?' ma o bu 'Kedu otu m ga-esi apuo?')",
        "you": "Ihe gi",
        "bot": "Onye Enyemaka Eco-Tide",
        "powered": "Eco-Tide AI • Na-aza n'asusuu gi",
    },
    "ha": {
        "greeting": (
            "Sannu! Ni ne Mataimaki na Ambaliyar Ruwa na Eco-Tide. Zan iya taimakawa da:\n\n"
            "- Hadarin ambaliyar ruwa a yankinku yau\n"
            "- Hanyoyin ficewa daga kowane LGA na Lagos\n"
            "- Lambobin gaggawa (NEMA, LASEMA)\n"
            "- Shawarwari don shirye-shirye don ambaliya\n"
            "- Abin da za a yi yayin ambaliyar ruwa\n\n"
            "Zabi yarenku a sama ko danna tambayarka a kasa!"
        ),
        "status": lambda: (
            f"Hadari: {', '.join(red_zones)} {'suna' if len(red_zones)>1 else 'yana'} cikin haɗarin ambaliyar ruwa - fita nan take!\n\n"
            f"Gargaɗi: {', '.join(amber_zones)} {'suna' if len(amber_zones)>1 else 'yana'} cikin haɗari.\n\n"
            f"Yankuna {20 - len(red_zones) - len(amber_zones)} suna lafiya."
            if (red_zones or amber_zones) else
            "Lafiya: Dukkan yankuna 20 na Lagos suna lafiya yau. Ba a gano haɗarin ambaliya ba."
        ),
        "evacuate": (
            "Yadda ake ficewa lafiya:\n\n"
            "1. Fita NAN TAKE - kada ku jira ruwa ya iso ƙofar gida\n"
            "2. Yi amfani da hanyoyin ficewa da aka zaba\n"
            "3. KA DAI KA yi tafiya ko tuka mota a cikin ruwa mai gudana\n"
            "4. Kai jakar ficewa: ruwa, abinci, magunguna, takardun muhimmanci\n"
            "5. Yi amfani da gadoji (Carter, Eko, 3rd Mainland)\n\n"
            "Hanyoyi masu muhimmanci:\n"
            "- Lekki/Ibeju-Lekki zuwa Epe ta Lekki-Epe Expressway\n"
            "- Apapa zuwa Surulere ta Apapa-Oshodi Expressway"
        ),
        "contacts": (
            "Lambobin Gaggawa - Adana Su YANZU:\n\n"
            "LASEMA: 767\n"
            "NEMA: 0800-2255-6362\n"
            "Sabis na Wuta: 01-7944927\n"
            "Giciyar Ja: 01-8700920\n"
            "Yan Sanda: 112\n"
            "Asibiti: 199"
        ),
        "prepare": (
            "Shirye-shiryen Awa 72:\n\n"
            "Adana yanzu:\n"
            "- Lita 3 ruwan sha ga kowane mutum a rana\n"
            "- Abinci wanda bai lalace ba (abinci a akwati, biscuits)\n"
            "- Magunguna da kayan maganin farko\n"
            "- Fitila da batiri na ajiya\n\n"
            "Kare takardun:\n"
            "- Sanya katin NIMC, takardar ƙasa, fasfo a jaka ta ruwa-ta-guje\n\n"
            "San hanyarku:\n"
            "- Tambayi maƙwabci inda wuri mai tsayi ya ke kusa"
        ),
        "during": (
            "Abin da Za a Yi YAYIN Ambaliyar Ruwa:\n\n"
            "KA DAI KA:\n"
            "- Yi tafiya a cikin ruwa mai gudana (cm 30 na iya farkar da ka)\n"
            "- Tuka mota ta hanyar da ruwa ya mamaye\n"
            "- Taɓa kayan wutar lantarki kusa da ruwa\n\n"
            "YI:\n"
            "- Kashe wutar lantarki a maɓalli na farko\n"
            "- Je sama ko rufin gida\n"
            "- Kira LASEMA: 767 don ceto"
        ),
        "fallback": (
            "Ban san game da haka ba. Kuna iya tambayarmu game da:\n\n"
            "- Matsayin haɗarin ambaliyar ruwa yau\n"
            "- Hanyoyin ficewa daga yankinku\n"
            "- Lambobin wayar gaggawa\n"
            "- Yadda ake shirya\n"
            "- Abin da za a yi yayin ambaliya"
        ),
        "quick_btns": ["Haɗarin Yanzu", "Yadda Ake Ficewa", "Lambobin Gaggawa", "Yadda Ake Shirya", "Yayin Ambaliya"],
        "input_placeholder": "Rubuta tambayarka a nan... (misali 'Apapa lafiya yake?' ko 'Yaya zan fice?')",
        "you": "Kai/Ke",
        "bot": "Mataimaki Eco-Tide",
        "powered": "Eco-Tide AI • Yana amsa a yarenku",
    },
}

KEYWORDS = {
    "status":   ["risk","danger","safe","status","flood","current","alert","ipo","ewu","abo","hadari","mmiri"],
    "evacuate": ["evacuate","evacuation","escape","route","leave","run","sa","oonaa","isa","fita","ficewa","apuo","uzo"],
    "contacts": ["contact","call","phone","number","nema","lasema","police","ambulance","nombaa","kira","lambda","namba"],
    "prepare":  ["prepare","ready","kit","bag","water","food","before","mura","imurasile","shirya","njikere"],
    "during":   ["during","stuck","trapped","inside","help","rescue","nigba","n'oge","yayin","n'ime"],
}

def get_bot_response(user_msg: str, lang: str) -> str:
    T = KB.get(lang, KB["en"])
    msg_lower = user_msg.lower()
    
    # 1. Greeting check
    if any(g in msg_lower for g in ["hi","hello","hey","bawo","nnoo","sannu","good morning","good evening"]):
        return T["greeting"]

    # 2. Hyper-Local Community / Street / LGA Specific Query FIRST
    try:
        cur_wl = latest.get("water_level_m", 0.93)
        cur_rain = latest.get("rainfall_mm", 0.0)
        cur_wind = latest.get("wind_speed_ms", 8.0)
        cur_pres = latest.get("pressure_hpa", 1013.0)
        cur_soil = latest.get("soil_moisture", 0.3)
        
        match_obj, match_type = find_community_or_zone(msg_lower, cur_wl, cur_rain, cur_wind, cur_pres, cur_soil)
        if match_obj:
            lvl = match_obj.get("level", "green")
            lvl_icon = {"red": "🔴", "amber": "🟡", "green": "🟢"}.get(lvl, "🟢")
            score_pct = int(match_obj.get("score", 0.0) * 100)
            
            if match_type == "community":
                c_name = match_obj.get("community", "")
                streets = match_obj.get("hotspot_streets", "")
                elev = match_obj.get("elevation_m", 2.0)
                safe_pt = match_obj.get("safe_evacuation_point", "Nearest high ground")
                ftype = match_obj.get("flood_type", "Pluvial / Coastal").replace("_", " ").title()
                fcause = match_obj.get("flood_cause", "")
                
                status_desc = (
                    "🚨 **CRITICAL INUNDATION:** High risk of flooding! Evacuate to higher ground immediately."
                    if lvl == "red" else (
                        "⚠️ **ELEVATED ADVISORY:** High tide / rain accumulation. Monitor road conditions."
                        if lvl == "amber" else
                        "✅ **CURRENTLY SAFE:** Normal flow. Zero water pooling detected on roads."
                    )
                )
                
                return (
                    f"📍 **{c_name}** — {lvl_icon} **{match_obj.get('label', 'SAFE').upper()}**\n\n"
                    f"• **Monitored Hotspots:** {streets}\n"
                    f"• **Ground Elevation:** {elev:.1f} m above sea level\n"
                    f"• **Ocean Water Level:** {cur_wl:.2f} m (Safety buffer: {max(0, 2.0 - cur_wl):.2f}m below 2.0m surge threshold)\n"
                    f"• **Rainfall Intensity:** {cur_rain:.1f} mm/hr (Dry roads)\n"
                    f"• **Flood Typology:** {ftype}\n"
                    f"• **Vulnerability Profile:** {fcause}\n"
                    f"• **Safe Evacuation High Ground:** 🏃 {safe_pt}\n\n"
                    f"{status_desc}"
                )
            else:
                # LGA Zone
                z_name = match_obj.get("name", "")
                elev = match_obj.get("elevation_m", 5.0)
                safe_pt, dist, route = EVACUATION_ROUTES.get(z_name, ("Higher ground mainland", "Varies", "Main Highway"))
                if lang == "yo":
                    return (
                        f"📍 **Agbègbè {z_name}** — {lvl_icon} **{match_obj.get('label', 'AABO').upper()}**\n\n"
                        f"• **Ipele Ewu:** **{score_pct}%**\n"
                        f"• **Ijinna si Omi:** {elev:.1f} m\n"
                        f"• **Agbègbè Aabo to Sunmọ:** {safe_pt} ({dist}) nípasẹ̀ {route}\n\n"
                        f"{'🚨 Sa lọ lẹsẹkẹsẹ!' if lvl=='red' else ('⚠️ Mura lati sa.' if lvl=='amber' else '✅ Gbogbo agbègbè ti a n ṣe abojuto ni LGA yii wa ni alaafia.')}"
                    )
                elif lang == "ig":
                    return (
                        f"📍 **Mpaghara {z_name}** — {lvl_icon} **{match_obj.get('label', 'NCHEBE').upper()}**\n\n"
                        f"• **Ọkwa Ihe Ize Ndụ:** **{score_pct}%**\n"
                        f"• **Elu Ala:** {elev:.1f} m\n"
                        f"• **Ebe Nchedo Kasị Nso:** {safe_pt} ({dist}) site na {route}\n\n"
                        f"{'🚨 Pụọ ozugbo!' if lvl=='red' else ('⚠️ Dị njikere ịpu!' if lvl=='amber' else '✅ Mpaghara a dị nchebe ugbu a.')}"
                    )
                elif lang == "ha":
                    return (
                        f"📍 **Yankin {z_name}** — {lvl_icon} **{match_obj.get('label', 'LAFIYA').upper()}**\n\n"
                        f"• **Matsayin Haɗari:** **{score_pct}%**\n"
                        f"• **Tsayin Wuri:** {elev:.1f} m\n"
                        f"• **Wurin Tsaro Mafi Kusa:** {safe_pt} ({dist}) ta {route}\n\n"
                        f"{'🚨 Fita nan take!' if lvl=='red' else ('⚠️ Shirya don ficewa.' if lvl=='amber' else '✅ Wannan yankin yana lafiya a halin yanzu.')}"
                    )
                else:
                    return (
                        f"📍 **{z_name} LGA** — {lvl_icon} **{match_obj.get('label', 'SAFE').upper()}**\n\n"
                        f"• **Average Elevation:** {elev:.1f} m\n"
                        f"• **Current Risk Score:** {score_pct}%\n"
                        f"• **Current Conditions:** {cur_wl:.2f}m water level | {cur_rain:.1f}mm/hr rain\n"
                        f"• **Nearest Safe Zone:** {safe_pt} ({dist}) via {route}\n\n"
                        f"{'⚠️ Evacuate immediately!' if lvl=='red' else ('⚠️ Prepare to evacuate.' if lvl=='amber' else '✅ All monitored communities in this LGA are currently safe.')}"
                    )
    except Exception as e:
        pass

    # 3. Keyword matching for general guidance
    for intent, kws in KEYWORDS.items():
        if any(k in msg_lower for k in kws):
            val = T[intent]
            return val() if callable(val) else val
    try:
        from config.settings import LAGOS_ZONES
        for zone_cfg in LAGOS_ZONES:
            if zone_cfg["name"].lower() in msg_lower:
                match = next((z for z in zone_risks if z["name"] == zone_cfg["name"]), None)
                if match:
                    safe, dist, route = EVACUATION_ROUTES.get(match["name"], ("Highland area","Varies","Main road"))
                    lvl_icon = {"red":"🔴","amber":"🟡","green":"🟢"}.get(match["level"],"🟢")
                    if lang == "yo":
                        return (
                            f"**{match['name']}** — {lvl_icon} {match.get('label','').upper()}\n\n"
                            f"- Ipele Ewu: **{int(match['score']*100)}%**\n"
                            f"- Ijinna si ile giga: **{match['elevation_m']:.1f} m**\n"
                            f"- Agbegbe Aabo to Sunmo: **{safe}** ({dist})\n"
                            f"- Oonaa Isapadaa: **{route}**\n\n"
                            f"{'⚠️ Sa lo lesekese!' if match['level']=='red' else ('⚠️ Mura lati sa.' if match['level']=='amber' else '✅ Agbegbe naa wa ni abo.')}"
                        )
                    elif lang == "ig":
                        return (
                            f"**{match['name']}** — {lvl_icon} {match.get('label','').upper()}\n\n"
                            f"- Okwa Ihe Ize Ndu: **{int(match['score']*100)}%**\n"
                            f"- Elu ala: **{match['elevation_m']:.1f} m**\n"
                            f"- Ebe Nchedo Kachasi Nso: **{safe}** ({dist})\n"
                            f"- Uzo Ipuo: **{route}**\n\n"
                            f"{'⚠️ Puoo ozugbo!' if match['level']=='red' else ('⚠️ Di njikere ipuo.' if match['level']=='amber' else '✅ Mpaghara a di nchebe.')}"
                        )
                    elif lang == "ha":
                        return (
                            f"**{match['name']}** — {lvl_icon} {match.get('label','').upper()}\n\n"
                            f"- Matsayin Hadari: **{int(match['score']*100)}%**\n"
                            f"- Tsayi: **{match['elevation_m']:.1f} m**\n"
                            f"- Mafi Kusa da Wurin Aminci: **{safe}** ({dist})\n"
                            f"- Hanyar Ficewa: **{route}**\n\n"
                            f"{'⚠️ Fita nan take!' if match['level']=='red' else ('⚠️ Shirya don fita.' if match['level']=='amber' else '✅ Yankin yana lafiya yanzu.')}"
                        )
                    else:
                        return (
                            f"**{match['name']}** — {lvl_icon} {match.get('label','').upper()}\n\n"
                            f"- Risk Score: **{int(match['score']*100)}%**\n"
                            f"- Elevation: **{match['elevation_m']:.1f} m**\n"
                            f"- Nearest safe zone: **{safe}** ({dist})\n"
                            f"- Evacuation route: **{route}**\n\n"
                            f"{'⚠️ Evacuate immediately!' if match['level']=='red' else ('⚠️ Prepare to evacuate.' if match['level']=='amber' else '✅ Currently safe.')}"
                        )
    except Exception:
        pass
    return T["fallback"]

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE UI & LANGUAGE SELECTION
# ═══════════════════════════════════════════════════════════════════════════════
LANG_OPTIONS = {"en":"🇬🇧 English","yo":"🇳🇬 Yoruba","ig":"🇳🇬 Igbo","ha":"🇳🇬 Hausa"}

if "app_language" not in st.session_state:
    st.session_state.app_language = "en"

def switch_language(target_lang):
    if target_lang in LANG_OPTIONS:
        st.session_state.app_language = target_lang
        st.session_state.chat_lang = target_lang
        st.session_state.messages = [
            {"role": "assistant", "content": KB[target_lang]["greeting"], "time": datetime.now().strftime("%H:%M")}
        ]

# ── Sidebar Language Selector ─────────────────────────────────────────────────
with st.sidebar:
    render_theme_switcher()
    st.markdown("---")
    st.markdown("### 🌍 Language / Ede / Asusuu / Harshe")
    curr_lang = st.session_state.app_language

    # High-contrast 2x2 language buttons for instant selection
    sb_col1, sb_col2 = st.columns(2)
    with sb_col1:
        if st.button("🇬🇧 English", key="sb_btn_en", use_container_width=True, type="primary" if curr_lang=="en" else "secondary"):
            if curr_lang != "en":
                switch_language("en")
                st.rerun()
        if st.button("🇳🇬 Igbo", key="sb_btn_ig", use_container_width=True, type="primary" if curr_lang=="ig" else "secondary"):
            if curr_lang != "ig":
                switch_language("ig")
                st.rerun()
    with sb_col2:
        if st.button("🇳🇬 Yoruba", key="sb_btn_yo", use_container_width=True, type="primary" if curr_lang=="yo" else "secondary"):
            if curr_lang != "yo":
                switch_language("yo")
                st.rerun()
        if st.button("🇳🇬 Hausa", key="sb_btn_ha", use_container_width=True, type="primary" if curr_lang=="ha" else "secondary"):
            if curr_lang != "ha":
                switch_language("ha")
                st.rerun()

    sidebar_lang = st.selectbox(
        "Select Language", options=list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.keys()).index(curr_lang),
        format_func=lambda k: LANG_OPTIONS[k],
        key=f"sidebar_lang_selector_{curr_lang}",
        label_visibility="collapsed"
    )
    if sidebar_lang != curr_lang:
        switch_language(sidebar_lang)
        st.rerun()

    st.markdown("---")
    # Live risk summary sidebar card - 100% High Contrast Custom Card
    if red_zones:
        st.markdown(f'''
        <div style="background:rgba(239, 68, 68, 0.22); border:1.5px solid #EF4444; border-radius:12px; padding:12px 14px; margin-top:8px;">
            <div style="color:#EF4444; font-weight:800; font-size:0.92rem; margin-bottom:4px;">🚨 Active Flood Alert</div>
            <div style="color:#FFFFFF; font-size:0.86rem; font-weight:600;">{', '.join(red_zones[:2])}</div>
        </div>
        ''', unsafe_allow_html=True)
    elif amber_zones:
        st.markdown(f'''
        <div style="background:rgba(245, 158, 11, 0.22); border:1.5px solid #F59E0B; border-radius:12px; padding:12px 14px; margin-top:8px;">
            <div style="color:#F59E0B; font-weight:800; font-size:0.92rem; margin-bottom:4px;">⚠️ Elevated Watch</div>
            <div style="color:#FFFFFF; font-size:0.86rem; font-weight:600;">{', '.join(amber_zones[:2])}</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div style="background:rgba(16, 185, 129, 0.22); border:1.5px solid #10B981; border-radius:12px; padding:12px 14px; margin-top:8px;">
            <div style="color:#34D399; font-weight:800; font-size:0.95rem; margin-bottom:4px;">🟢 All Zones Safe</div>
            <div style="color:#FFFFFF; font-size:0.86rem; font-weight:600;">Normal tidal conditions in Lagos</div>
        </div>
        ''', unsafe_allow_html=True)

lang = st.session_state.app_language
T = KB.get(lang, KB["en"])

# ── High Contrast Chat Input CSS ──────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar Selectbox & Inputs High Contrast */
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] div,
[data-testid="stSidebar"] div[data-baseweb="select"] * {
    background-color: #131D31 !important;
    background: #131D31 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    border: 1.5px solid rgba(56, 189, 248, 0.6) !important;
    border-radius: 10px !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #38BDF8 !important;
    color: #38BDF8 !important;
}

/* BaseWeb Dropdown Options */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
ul[role="listbox"],
li[role="option"] {
    background-color: #131D31 !important;
    background: #131D31 !important;
    color: #FFFFFF !important;
}

li[role="option"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background-color: #0284C7 !important;
    background: #0284C7 !important;
    color: #FFFFFF !important;
}

/* Fix chat input text visibility in all modes */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div[data-baseweb="textarea"],
[data-testid="stChatInput"] div[data-baseweb="textarea"] > div,
[data-testid="stChatInput"] div[data-baseweb="input"],
.stChatFloatingInputContainer,
.stChatFloatingInputContainer > div {
    background-color: #131D31 !important;
    background: #131D31 !important;
    border: 1.5px solid rgba(56, 189, 248, 0.5) !important;
    border-radius: 12px !important;
}

[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    background: transparent !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    caret-color: #38BDF8 !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(255, 255, 255, 0.65) !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.65) !important;
}

[data-testid="stChatInput"] button {
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header Banner ─────────────────────────────────────────────────────────────
_db_badge = (
    '<span style="background:rgba(0,200,150,0.18);color:#00C896;border:1px solid rgba(0,200,150,0.4);'
    'border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:700;margin-left:8px;'
    'vertical-align:middle;">☁ Live DB</span>'
    if is_connected() else
    '<span style="background:rgba(255,200,0,0.15);color:#C07B00;border:1px solid rgba(255,200,0,0.35);'
    'border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:700;margin-left:8px;'
    'vertical-align:middle;">💾 Local</span>'
)
st.markdown(f"""
<div style="background:var(--bg-card);
            border-radius:16px; padding:22px 26px; margin-bottom:18px;
            border:1.5px solid var(--border-card);
            box-shadow:var(--shadow-card);">
  <div style="font-size:1.85rem; font-weight:900; color:var(--text-primary);
              line-height:1.2; margin-bottom:6px;">
    💬 Eco-Tide Community &amp; Emergency Hub {_db_badge}
  </div>
  <div style="font-size:0.95rem; color:var(--text-secondary); font-weight:600;">
    {LANG_OPTIONS[lang]} &bull; {T['powered']}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Language Selector Controls in Main Page ─────────────────────────────────
st.markdown("<div style='font-size:0.85rem; font-weight:700; color:var(--text-secondary); margin-bottom:8px;'>🌍 SELECT COMMUNICATION LANGUAGE / YAN EDE / HOROO ASUSUU / ZABI YARENKU:</div>", unsafe_allow_html=True)

lang_cols = st.columns(4)
for col, (l_key, l_label) in zip(lang_cols, LANG_OPTIONS.items()):
    with col:
        is_active = (l_key == lang)
        btn_label = f"✓ {l_label}" if is_active else l_label
        btn_type = "primary" if is_active else "secondary"
        if st.button(btn_label, key=f"top_lang_btn_{l_key}", use_container_width=True, type=btn_type):
            if st.session_state.app_language != l_key:
                switch_language(l_key)
                st.rerun()

st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

# ── Navigation Tabs ──────────────────────────────────────────────
if _GEO_OK:
    tab_chat, tab_location, tab_reports = st.tabs([
        f"🤖 AI Emergency Assistant ({LANG_OPTIONS[lang]})",
        "📍 My Location & Local Risk",
        "📢 Community Incident Reports",
    ])
else:
    tab_chat, tab_reports = st.tabs([
        f"🤖 AI Emergency Assistant ({LANG_OPTIONS[lang]})",
        "📢 Community Incident Reports",
    ])
    tab_location = None

with tab_chat:
    # ── Chat History (Loaded dynamically from Supabase Cloud) ────────────────
    if "messages" not in st.session_state or st.session_state.get("chat_lang") != lang:
        saved_history = fetch_chat_messages(limit=25, language=lang)
        if saved_history:
            formatted_history = []
            for m in saved_history:
                _t = m.get("created_at", "")
                _t_str = datetime.now().strftime("%H:%M")
                if _t and len(str(_t)) >= 16:
                    try:
                        _dt = datetime.fromisoformat(str(_t).replace("Z", "+00:00"))
                        _t_str = _dt.strftime("%H:%M")
                    except Exception:
                        _t_str = str(_t)[11:16]
                formatted_history.append({
                    "role": m.get("role", "assistant"),
                    "content": m.get("content", ""),
                    "time": _t_str
                })
            st.session_state.messages = formatted_history
        else:
            st.session_state.messages = [
                {"role": "assistant", "content": T["greeting"], "time": datetime.now().strftime("%H:%M")}
            ]
        st.session_state.chat_lang = lang

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🌊" if msg["role"]=="assistant" else "🧑"):
            st.markdown(msg["content"])
            st.caption(msg["time"])

    # ── Quick Action Buttons (3 + 2 layout to prevent truncation) ───────────
    st.markdown("<div style='margin:12px 0 6px 0; font-size:0.82rem; color:var(--text-secondary); font-weight:600;'>⚡ Quick Questions / Ibeere Kankan:</div>", unsafe_allow_html=True)
    intents = ["status", "evacuate", "contacts", "prepare", "during"]
    _all_btns = list(zip(T["quick_btns"], intents))
    # Row 1: first 3 buttons
    _row1 = st.columns(3)
    for i, col in enumerate(_row1):
        label, intent = _all_btns[i]
        with col:
            if st.button(label, key=f"qbtn_{i}_{lang}", use_container_width=True):
                bot_text = KB[lang][intent]
                bot_text = bot_text() if callable(bot_text) else bot_text
                now = datetime.now().strftime("%H:%M")
                st.session_state.messages.append({"role": "user", "content": label, "time": now})
                st.session_state.messages.append({"role": "assistant", "content": bot_text, "time": now})
                save_chat_message("user", label, lang)
                save_chat_message("assistant", bot_text, lang)
                st.rerun()
    # Row 2: last 2 buttons
    _row2_left, _row2_mid, _ = st.columns([1, 1, 1])
    for j, col in enumerate([_row2_left, _row2_mid]):
        i = j + 3
        label, intent = _all_btns[i]
        with col:
            if st.button(label, key=f"qbtn_{i}_{lang}", use_container_width=True):
                bot_text = KB[lang][intent]
                bot_text = bot_text() if callable(bot_text) else bot_text
                now = datetime.now().strftime("%H:%M")
                st.session_state.messages.append({"role": "user", "content": label, "time": now})
                st.session_state.messages.append({"role": "assistant", "content": bot_text, "time": now})
                save_chat_message("user", label, lang)
                save_chat_message("assistant", bot_text, lang)
                st.rerun()

    # ── Chat Input ───────────────────────────────────────────────────────────
    user_input = st.chat_input(T["input_placeholder"])
    if user_input:
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role":"user","content":user_input,"time":now})
        response = get_bot_response(user_input, lang)
        st.session_state.messages.append({"role":"assistant","content":response,"time":now})
        save_chat_message("user", user_input, lang)
        save_chat_message("assistant", response, lang)
        st.rerun()

    # ── Clear Chat ───────────────────────────────────────────────────────────
    if len(st.session_state.messages) > 2:
        if st.button("🗑 Clear Chat", type="secondary"):
            st.session_state.messages = [
                {"role":"assistant","content":T["greeting"],"time":datetime.now().strftime("%H:%M")}
            ]
            st.rerun()

# ── My Location Tab ─────────────────────────────────────────────
if _GEO_OK and tab_location is not None:
    with tab_location:
        from config.settings import LAGOS_ZONES
        st.markdown(
            "<div style='font-size:0.9rem; color:var(--text-secondary); margin-bottom:14px; line-height:1.6;'>"
            "🔐 <b>Privacy Guaranteed:</b> Your GPS location is computed locally in your browser to match your nearest LGA "
            "and display hyper-local flood risk. Coordinates are only submitted if you send an incident report."
            "</div>",
            unsafe_allow_html=True
        )

        _col_l, _col_r = st.columns([1, 1], gap="large")
        with _col_l:
            st.markdown("#### 📍 Device Location & LGA Detection")
            user_loc = render_location_widget(
                key_prefix="community",
                zones=LAGOS_ZONES,
            )

            st.markdown("<div style='margin-top:14px; font-weight:700; font-size:0.9rem; color:var(--text-primary);'>🏙️ Select / Confirm Your LGA:</div>", unsafe_allow_html=True)
            _lga_names = [z["name"] for z in LAGOS_ZONES]
            _auto_zone = st.session_state.get("user_nearest_zone")
            _default_idx = _lga_names.index(_auto_zone) if _auto_zone in _lga_names else 0

            active_lga = st.selectbox(
                "LGA Selection",
                options=_lga_names,
                index=_default_idx,
                label_visibility="collapsed",
                key="location_tab_active_lga_select"
            )

            if user_loc and active_lga == _auto_zone:
                st.caption(f"🎯 Auto-matched from GPS ({user_loc['lat']:.4f}°N, {user_loc['lon']:.4f}°E)")
            elif user_loc:
                st.caption(f"ℹ️ Manually viewing {active_lga} (GPS nearest is {_auto_zone})")
            else:
                st.caption("💡 Tap 'Auto-Detect My Location' above or select any LGA manually.")

        with _col_r:
            st.markdown("#### 🌊 Real-Time Area Flood Risk")
            _nz = next((z for z in LAGOS_ZONES if z["name"] == active_lga), None)
            if _nz:
                _rm = next((z for z in zone_risks if z["name"] == active_lga), None)
                _lv = _rm["level"] if _rm else "green"
                _score = int((_rm.get("score", 0.15) if _rm else 0.15) * 100)
                _acts = {
                    "red":   ("🚨 EVACUATE NOW",  "#EF4444", "Urgent risk! Move valuables to higher ground. Follow official evacuation directives.", "rgba(239,68,68,0.12)", "#EF4444"),
                    "amber": ("⚠️ PREPARE NOW",   "#F59E0B", "Elevated risk. Pack 72-hour emergency go-bag and keep devices charged.", "rgba(245,158,11,0.12)", "#F59E0B"),
                    "green": ("✅ CURRENTLY SAFE", "#10B981", "Normal conditions. Keep drains clear and monitor live updates.", "rgba(16,185,129,0.12)", "#10B981"),
                }
                _al, _ac, _ad, _abg, _aborder = _acts.get(_lv, _acts["green"])

                # Fetch route info
                _safe, _dist, _route = EVACUATION_ROUTES.get(active_lga, ("Higher ground mainland", "Varies", "Expressway"))

                st.markdown(
                    f"""<div style='background:var(--bg-card); border:1.5px solid {_aborder};
                                border-radius:14px; padding:20px; margin-bottom:14px; box-shadow:0 4px 20px rgba(0,0,0,0.06);'>
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                            <span style='font-size:1.3rem; font-weight:900; color:var(--text-primary);'>📍 {active_lga}</span>
                            <span style='background:{_abg}; color:{_ac}; font-weight:800; font-size:0.85rem; padding:4px 12px; border-radius:20px; border:1px solid {_aborder};'>
                                {_al} ({_score}%)
                            </span>
                        </div>
                        <div style='font-size:0.92rem; color:var(--text-secondary); line-height:1.55; margin-bottom:12px;'>
                            {_ad}
                        </div>
                        <hr style='border:none; border-top:1px solid var(--border-card); margin:10px 0;'>
                        <div style='font-size:0.84rem; color:var(--text-muted); line-height:1.8;'>
                            🚗 <b>Evacuation Haven:</b> {_safe} ({_dist}) via {_route}<br>
                            🌊 <b>Elevation:</b> {_nz.get('elevation_m', 5):.1f}m &nbsp;|&nbsp; <b>Water Distance:</b> {_nz.get('distance_to_water_km', 1)} km<br>
                            💧 <b>Drainage Capacity:</b> {int(_nz.get('drainage_capacity', 0.5)*100)}% &nbsp;|&nbsp; 👥 <b>Population:</b> {_nz.get('population', 0):,}
                        </div>
                    </div>""",
                    unsafe_allow_html=True
                )
                if _lv in ("red", "amber"):
                    st.error("🚨 Emergency Rescue Hotlines: **LASEMA: 767** | **NEMA: 0800-2255-6362**")

        st.markdown("---")
        st.markdown("#### 📡 Submit Instant Flood Report for " + active_lga)
        if user_loc:
            st.markdown(
                f"<div style='font-size:0.83rem; color:var(--text-secondary); margin-bottom:12px;'>"
                f"Tagged with GPS: <b>({user_loc['lat']:.4f}°N, {user_loc['lon']:.4f}°E)</b> — "
                f"linked to <b>{active_lga}</b>."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='font-size:0.83rem; color:var(--text-secondary); margin-bottom:12px;'>"
                f"Reporting for LGA: <b>{active_lga}</b> (Coordinates optional &mdash; auto-added if GPS is enabled above)."
                "</div>",
                unsafe_allow_html=True,
            )

        with st.form("geo_report_form", clear_on_submit=True):
            gr_col1, gr_col2 = st.columns([1, 1])
            with gr_col1:
                gr_name = st.text_input("Your Name / Alias (optional)", placeholder="e.g. Resident / Community Leader")
            with gr_col2:
                gr_sev = st.selectbox("Severity Level", options=["Low", "Medium", "High", "Critical"], index=1)

            gr_dep = st.number_input("Estimated Water Depth (cm)", min_value=0, max_value=300, value=15, step=5)
            gr_msg = st.text_area("What are you observing?", placeholder="e.g. Street impassable near landmark, drain overflowing...")
            gr_go = st.form_submit_button("📡 Submit Incident Report", type="primary", use_container_width=True)

            if gr_go and gr_msg.strip():
                _report_payload = {
                    "lga": active_lga,
                    "reporter": gr_name.strip() or "Community Observer (Anonymous)",
                    "severity": gr_sev,
                    "water_cm": f"{gr_dep} cm",
                    "msg": gr_msg.strip(),
                }
                if user_loc:
                    _report_payload["lat"] = user_loc["lat"]
                    _report_payload["lon"] = user_loc["lon"]
                    _report_payload["accuracy_m"] = user_loc.get("accuracy_m")

                _ok2, _fb2 = submit_community_report(_report_payload)
                if _ok2:
                    st.success(_fb2)
                    st.balloons()
                else:
                    st.error(_fb2)


with tab_reports:

    st.markdown("### 📢 Community Flood Incident Reporting")
    st.markdown("Share real-time flood observations from your local government area to keep fellow Lagosians safe.")

    # Default seed reports (only used when no DB records exist)
    _SEED_REPORTS = [
        {
            "lga": "Eti-Osa",
            "reporter": "Adebayo K. (Lekki Phase 1)",
            "time": "10 mins ago",
            "severity": "High",
            "water_cm": "25 cm",
            "msg": "Water rising rapidly near Admiralty Way roundabout after heavy morning tide.",
            "status": "Verified by LASEMA",
        },
        {
            "lga": "Apapa",
            "reporter": "Chidi O. (Wharf Rd)",
            "time": "35 mins ago",
            "severity": "Medium",
            "water_cm": "15 cm",
            "msg": "Heavy runoff along commercial avenue. Commercial vehicles navigating slowly.",
            "status": "Monitoring",
        },
        {
            "lga": "Ibeju-Lekki",
            "reporter": "Folake A. (Eleko)",
            "time": "1 hour ago",
            "severity": "High",
            "water_cm": "40 cm",
            "msg": "Omi ti n san wole ni titi Eleko. Otito ni ki gbogbo eniyan mura lati sa.",
            "status": "Alert Broadcasted",
        }
    ]

    # Load reports from Supabase or local fallback
    _fetched = fetch_community_reports(limit=30)
    _reports_to_show = _fetched if _fetched else _SEED_REPORTS

    c_form, c_feed = st.columns([1, 1], gap="large")

    with c_form:
        st.markdown("#### 📝 Submit Live Incident Report")
        with st.form("community_report_form", clear_on_submit=True):
            from config.settings import LAGOS_ZONES
            lga_list = [z["name"] for z in LAGOS_ZONES]
            rep_lga      = st.selectbox("Select Your LGA", options=lga_list)
            rep_name     = st.text_input("Your Name / Area (e.g., Tunde from Victoria Island)")
            rep_severity = st.select_slider("Observed Flood Severity", options=["Low", "Medium", "High", "Critical"])
            rep_water    = st.number_input("Estimated Water Depth (cm)", min_value=0, max_value=200, value=15)
            rep_msg      = st.text_area(
                "Observation Details (Describe roads, drainage, or trapped vehicles)",
                placeholder="e.g. Drainage overflowed onto major road..."
            )
            submit_btn = st.form_submit_button("📡 Broadcast Report to Community", type="primary", use_container_width=True)

            if submit_btn and rep_msg.strip():
                ok, feedback_msg = submit_community_report({
                    "lga":      rep_lga,
                    "reporter": rep_name.strip() or "Anonymous Resident",
                    "severity": rep_severity,
                    "water_cm": f"{rep_water} cm",
                    "msg":      rep_msg.strip(),
                })
                if ok:
                    st.success(feedback_msg)
                else:
                    st.error(feedback_msg)
                st.rerun()

    with c_feed:
        st.markdown("#### 📡 Live Resident Broadcast Feed")
        for r in _reports_to_show:
            sev_color = {"Low": "#00C853", "Medium": "#FFD600", "High": "#FF1744", "Critical": "#D50000"}.get(r.get("severity", "Low"), "#0A84FF")
            _time_label = r.get("time") or r.get("created_at", "")
            if _time_label and len(str(_time_label)) > 20:  # looks like ISO timestamp
                try:
                    from datetime import timezone
                    _dt = datetime.fromisoformat(str(_time_label).replace("Z", "+00:00"))
                    _time_label = _dt.strftime("%d %b, %H:%M UTC")
                except Exception:
                    _time_label = str(_time_label)[:16]
            st.markdown(f"""
            <div style="background:var(--bg-card); border:1px solid var(--border-card); border-left:4px solid {sev_color};
                        border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:var(--shadow-card);">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-weight:800; font-size:1.05rem; color:var(--text-primary);">📍 {r.get('lga','')}</span>
                <span style="font-size:0.75rem; background:rgba(10,132,255,0.1); color:var(--primary); padding:2px 8px; border-radius:10px;">{_time_label}</span>
              </div>
              <div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:8px;">
                <b>Reporter:</b> {r.get('reporter','')} | <b>Water Depth:</b> {r.get('water_cm','')} | <span style="color:{sev_color}; font-weight:700;">{r.get('severity','')} Severity</span>
              </div>
              <div style="font-size:0.92rem; color:var(--text-primary); line-height:1.5;">
                &ldquo;{r.get('msg','')}&rdquo;
              </div>
              <div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">
                Status: <b>{r.get('status','Community Broadcasted')}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding:20px 0 4px; font-size:0.75rem; color:var(--text-muted);">
  Eco-Tide Chat & Communication Hub • Not a substitute for official emergency services<br>
  In a life-threatening emergency, call LASEMA: <b>767</b>
</div>
""", unsafe_allow_html=True)
