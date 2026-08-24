import streamlit as st
import ollama
from datetime import datetime, date, time
import ephem
import math

# ---------------------------------------------------------
# 1. PAGE CONFIG & MODERN UI DESIGN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Astraea – Kosmischer Rechner & Deuter", 
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Styles & Background */
    html, body, .stApp, div, p, span, label, input, textarea {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e153e 0%, #0c0919 60%, #05040a 100%) !important;
        color: #f1f5f9 !important;
    }
    
    /* Header Styling */
    .hero-container {
        text-align: center;
        padding: 1.5rem 0 2rem 0;
    }
    
    .hero-title {
        font-family: 'Cinzel', serif !important;
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #fef3c7 40%, #d97706 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 6px;
        margin-bottom: 0.3rem;
        filter: drop-shadow(0 0 20px rgba(217, 119, 6, 0.25));
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 400;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* Glassmorphism Cards */
    .astrology-card {
        background: rgba(23, 18, 43, 0.55);
        border: 1px solid rgba(217, 119, 6, 0.2);
        border-radius: 24px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        transition: border 0.3s ease;
    }
    
    .astrology-card:hover {
        border-color: rgba(217, 119, 6, 0.4);
    }
    
    .card-header {
        font-family: 'Cinzel', serif !important;
        font-size: 1.35rem;
        color: #fbbf24;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Result Metric Cards */
    .planet-badge {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s ease, background 0.2s ease;
    }
    
    .planet-badge:hover {
        background: rgba(255, 255, 255, 0.06);
        transform: translateX(4px);
    }

    .planet-name {
        font-weight: 600;
        color: #e2e8f0;
    }

    .planet-position {
        color: #fbbf24;
        font-weight: 500;
        font-size: 0.95rem;
    }

    /* Action Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        padding: 1rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 10px 30px rgba(180, 83, 9, 0.35) !important;
        width: 100%;
        font-size: 1.1rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 15px 35px rgba(217, 119, 6, 0.5) !important;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    }

    /* Input overrides */
    .stTextInput input, .stDateInput input, .stTimeInput input, .stSelectbox > div > div {
        background-color: rgba(10, 8, 20, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
    }

    .stTextInput input:focus, .stDateInput input:focus {
        border-color: #fbbf24 !important;
        box-shadow: 0 0 12px rgba(251, 191, 36, 0.2) !important;
    }
    
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
        margin: 2.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MATHEMATISCHE PLANETENBERECHNUNG (EPHEM)
# ---------------------------------------------------------
ZODIAC_DE = [
    "Widder ♈", "Stier ♉", "Zwillinge ♊", "Krebs ♋", 
    "Löwe ♌", "Jungfrau ♍", "Waage ♎", "Skorpion ♏", 
    "Schütze ♐", "Steinbock ♑", "Wassermann ♒", "Fische ♓"
]

def get_zodiac_sign(lon_degrees):
    idx = int((lon_degrees % 360) // 30)
    deg = (lon_degrees % 360) % 30
    return ZODIAC_DE[idx], deg

def calculate_chart(dt):
    date_ephem = ephem.Date(dt)
    bodies = {
        "Sonne ☉": ephem.Sun(date_ephem),
        "Mond ☽": ephem.Moon(date_ephem),
        "Merkur ☿": ephem.Mercury(date_ephem),
        "Venus ♀": ephem.Venus(date_ephem),
        "Mars ♂": ephem.Mars(date_ephem),
        "Jupiter ♃": ephem.Jupiter(date_ephem),
        "Saturn ♄": ephem.Saturn(date_ephem),
        "Uranus ♅": ephem.Uranus(date_ephem),
        "Neptun ♆": ephem.Neptune(date_ephem),
        "Pluto ♇": ephem.Pluto(date_ephem)
    }
    
    results = []
    for name, body in bodies.items():
        ecl = ephem.Ecliptic(body)
        lon_deg = math.degrees(ecl.lon) % 360
        sign_name, deg = get_zodiac_sign(lon_deg)
        results.append((name, sign_name, deg))
    return results

# ---------------------------------------------------------
# 3. HEADER & INPUT FORM
# ---------------------------------------------------------
st.markdown("""
<div class='hero-container'>
    <div class='hero-title'>ASTRAEA</div>
    <div class='hero-subtitle'>Präziser Astrologie-Rechner & KI-Deutung</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("<div class='astrology-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>👤 Geburtshoroskop (Radix)</div>", unsafe_allow_html=True)
    
    geburts_datum = st.date_input(
        "Geburtsdatum",
        value=date(1995, 5, 15),
        min_value=date(1900, 1, 1),
        max_value=date(2100, 12, 31)
    )
    geburts_zeit = st.time_input("Geburtszeit", value=time(12, 0))
    geburts_ort = st.text_input("Geburtsort", value="Berlin")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='astrology-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>📅 Ziel-Datum & Anliegen</div>", unsafe_allow_html=True)
    
    ziel_datum = st.date_input(
        "Datum der Analyse / Entscheidung",
        value=date.today(),
        min_value=date(1900, 1, 1),
        max_value=date(2100, 12, 31)
    )
    ziel_zeit = st.time_input("Uhrzeit der Analyse", value=time(12, 0))
    anliegen = st.selectbox(
        "Fokus der Auswertung",
        ["Allgemeiner Überblick", "Beruf & Karriere", "Liebe & Beziehungen", "Finanzen & Timing", "Neuanfang & Entscheidungen"]
    )
    st.markdown("</div>", unsafe_allow_html=True)

konkrete_frage = st.text_input("Zusätzliche Frage (Optional)", placeholder="z. B. Soll ich das Jobangebot für diesen Monat annehmen?")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. CALCULATION & INTERPRETATION DISPLAY
# ---------------------------------------------------------
if st.button("✨ Horoskop berechnen & kosmisch deuten"):
    dt_birth = datetime.combine(geburts_datum, geburts_zeit)
    dt_target = datetime.combine(ziel_datum, ziel_zeit)
    
    radix_planets = calculate_chart(dt_birth)
    target_planets = calculate_chart(dt_target)
    
    # Styled Planet Cards Output
    res_col1, res_col2 = st.columns(2, gap="large")
    
    radix_text_list = []
    target_text_list = []
    
    with res_col1:
        st.markdown(f"### 🌟 Radix ({geburts_datum.strftime('%d.%m.%Y')})")
        for name, sign_name, deg in radix_planets:
            st.markdown(f"""
            <div class='planet-badge'>
                <span class='planet-name'>{name}</span>
                <span class='planet-position'>{deg:.1f}° {sign_name}</span>
            </div>
            """, unsafe_allow_html=True)
            radix_text_list.append(f"{name}: {deg:.1f}° {sign_name}")
            
    with res_col2:
        st.markdown(f"### 🪐 Transite am {ziel_datum.strftime('%d.%m.%Y')}")
        for name, sign_name, deg in target_planets:
            st.markdown(f"""
            <div class='planet-badge'>
                <span class='planet-name'>{name}</span>
                <span class='planet-position'>{deg:.1f}° {sign_name}</span>
            </div>
            """, unsafe_allow_html=True)
            target_text_list.append(f"{name}: {deg:.1f}° {sign_name}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🔮 Astrologische Auswertung durch Astraea")
    
    prompt_content = f"""
    Hier sind die von Python mathematisch EXAKT berechneten Planetenstände.
    Verändere NIEMALS diese Stellungen oder Zeichen:

    GEBURTHSKOROSKOP (RADIX) VOM {geburts_datum.strftime('%d.%m.%Y')}:
    {", ".join(radix_text_list)}

    TRANSITE AM ZIELDATUM {ziel_datum.strftime('%d.%m.%Y')}:
    {", ".join(target_text_list)}

    ANLIEGEN DES NUTZERS: {anliegen}
    ZUSÄTZLICHE FRAGE: {konkrete_frage if konkrete_frage else 'Keine'}

    STRIKTE STIL- UND FORMULIERUNGSREGELN:
    1. Nutze AUSSCHLIESSLICH deutsche Sternzeichen-Namen.
    2. Schreibe verständlich, praxisnah und lösungsorientiert.
    3. VERBOTENE FLOSKELN: Verwende NIEMALS Phrasen wie "Lass dich nicht von Ängsten leiten", "Verliere dich nicht in Illusionen" oder "Höre auf dein Herz".
    4. Formuliere "Do's & Don'ts" als KONKRETE VERHALTENSTIPPS (z. B. "Verträge vor Unterschrift juristisch prüfen", statt "Verliere dich nicht in Illusionen").

    ANTWORTSTRUKTUR:
    - **Persönliche Radix-Stärke** (Welche Grundvoraussetzungen bringt der Nutzer für {anliegen} mit?)
    - **Kosmische Zeit-Tendenz am {ziel_datum.strftime('%d.%m.%Y')}** (Was bedeuten die Transite konkret für das gewählte Thema?)
    - **Empfohlener Fokus (Do's)** (2-3 konkrete, aktive Handlungsschritte)
    - **Zu vermeiden (Don'ts)** (2-3 konkrete Handlungswarnungen für Alltag, Beruf oder Beziehungsentscheidungen)
    - **Konkretes Fazit zum Timing**
    """
    
    response_placeholder = st.empty()
    full_response = ""
    
    with st.spinner("Astraea wertet deine Konstellation aus..."):
        stream = ollama.chat(
            model="gemma2:9b", 
            messages=[{"role": "system", "content": "Du bist Astraea, eine professionelle und pragmatische Astrologin."},
                      {"role": "user", "content": prompt_content}], 
            stream=True
        )
        
        for chunk in stream:
            full_response += chunk['message']['content']
            response_placeholder.markdown(full_response + "▌")
            
        response_placeholder.markdown(full_response)

    # Rechtlicher Disclaimer
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.caption("""
    **⚖️ Rechtlicher Hinweis & Haftungsausschluss:**  
    Die von Astraea bereitgestellten Analysen und Auswertungen dienen ausschließlich Unterhaltungs-, Orientierungs- und Informationszwecken. 
    Sie stellen keine medizinische, juristische, finanzielle oder psychologische Beratung dar. Für Entscheidungen, die auf Basis 
    dieser Inhaltsanalysen getroffen werden, wird keine Haftung übernommen. Bei gesundheitlichen, rechtlichen oder finanziellen Notlagen 
    wenden Sie sich bitte an entsprechende Fachkräfte oder Behörden.
    """)