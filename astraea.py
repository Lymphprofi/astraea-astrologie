import streamlit as st
import ephem
from datetime import datetime

# --- KI-BIBLIOTHEKEN IMPORTIEREN ---
try:
    from groq import Groq
    groq_available = True
except ImportError:
    groq_available = False

try:
    import ollama
    ollama_available = True
except ImportError:
    ollama_available = False


# --- SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Astraea – Astrologie & Horoskop",
    page_icon="🌟",
    layout="wide"
)

# Custom Styling (Dunkles mystisches Theme)
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
    }
    .stButton>button {
        background-color: #6a11cb;
        background-image: linear-gradient(225deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# --- HILFSFUNKTIONEN FÜR ASTROLOGIE ---
def get_planet_positions(date_obj, time_obj):
    """Berechnet präzise die Positionsdaten der Planeten für beliebige Geburtsjahre."""
    date_str = f"{date_obj.strftime('%Y/%m/%d')} {time_obj.strftime('%H:%M:%S')}"
    
    observer = ephem.Observer()
    observer.date = date_str

    planets = {
        "Sonne": ephem.Sun(),
        "Mond": ephem.Moon(),
        "Merkur": ephem.Mercury(),
        "Venus": ephem.Venus(),
        "Mars": ephem.Mars(),
        "Jupiter": ephem.Jupiter(),
        "Saturn": ephem.Saturn(),
        "Uranus": ephem.Uranus(),
        "Neptun": ephem.Neptune(),
        "Pluto": ephem.Pluto(),
    }

    zodiac_signs = [
        "Widder", "Stier", "Zwillinge", "Krebs",
        "Löwe", "Jungfrau", "Waage", "Skorpion",
        "Schütze", "Steinbock", "Wassermann", "Fische"
    ]

    positions = {}
    for name, body in planets.items():
        body.compute(observer)
        lon = ephem.Ecliptic(body).lon
        deg_total = float(lon) * (180.0 / 3.141592653589793)
        sign_index = int(deg_total // 30) % 12
        deg_in_sign = deg_total % 30
        positions[name] = f"{zodiac_signs[sign_index]} ({deg_in_sign:.1f}°)"

    return positions


def ask_ai(prompt):
    """KI-Generator mit automatischer Modell-Erkennung für Groq."""
    
    # 1. OPTION: Streamlit Cloud via Groq API
    if "GROQ_API_KEY" in st.secrets:
        if not groq_available:
            yield "⚠️ GROQ_API_KEY gefunden, aber das Python-Paket 'groq' ist nicht installiert."
            return
        
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            available_models = [m.id for m in client.models.list().data]
            
            preferred_models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama3-70b-8192",
                "llama3-8b-8192",
                "mixtral-8x7b-32768"
            ]
            
            selected_model = None
            for model in preferred_models:
                if model in available_models:
                    selected_model = model
                    break
            
            if not selected_model and available_models:
                selected_model = available_models[0]
                
            if not selected_model:
                yield "⚠️ Keine aktiven Modelle für diesen Groq API-Key gefunden."
                return

            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
            
        except Exception as e:
            yield f"⚠️ Fehler beim Groq API-Aufruf: {e}"
            return

    # 2. OPTION: Lokales Ollama auf dem PC
    if ollama_available:
        try:
            stream = ollama.chat(
                model='llama3',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True,
            )
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
            return
        except Exception as e:
            yield f"⚠️ Lokales Ollama nicht erreichbar: {e}"
            return

    yield "⚠️ 'GROQ_API_KEY' wurde in den Streamlit Cloud Secrets nicht gefunden."


# --- OBERFLÄCHE (STREAMLIT APP) ---
st.title("🌟 Astraea – Deinetwegen stehen die Sterne gut")
st.write("Erstelle dein individuelles Horoskop und erhalte präzise astrologische KI-Analysen.")

st.sidebar.header("📋 Geburtsdaten eingeben")
name = st.sidebar.text_input("Name", value="Max Mustermann")

birth_date = st.sidebar.date_input(
    "Geburtsdatum", 
    value=datetime(1993, 1, 1),
    min_value=datetime(1984, 1, 1),
    max_value=datetime(2003, 12, 31)
)

birth_time = st.sidebar.time_input("Geburtszeit", value=datetime.strptime("14:30", "%H:%M").time())
location = st.sidebar.text_input("Geburtsort", value="Berlin")

if st.sidebar.button("🔮 Horoskop Berechnen & Analysieren"):
    st.session_state["positions"] = get_planet_positions(birth_date, birth_time)
    st.session_state["analyzed"] = True

# Wenn ein Horoskop berechnet wurde:
if st.session_state.get("analyzed", False):
    st.header(f"✨ Horoskop für {name}")
    st.caption(f"Geboren am {birth_date.strftime('%d.%m.%Y')} um {birth_time.strftime('%H:%M')} Uhr in {location}")

    positions = st.session_state["positions"]

    # Planetenstände in 2 Spalten
    col1, col2 = st.columns(2)
    items = list(positions.items())
    half = len(items) // 2

    with col1:
        for planet, pos in items[:half]:
            st.metric(label=planet, value=pos)

    with col2:
        for planet, pos in items[half:]:
            st.metric(label=planet, value=pos)

    st.markdown("---")
    st.subheader("📜 KI-Deutung & Horoskop-Interpretation")

    prompt_text = f"""
    Du bist eine professionelle, empathische und tiefgründige Astrologin namens Astraea.
    Erstelle eine ausführliche persönliche astrologische Analyse für {name}, geboren am {birth_date.strftime('%d.%m.%Y')} um {birth_time.strftime('%H:%M')} in {location}.
    
    Hier sind die berechneten Planetenstände:
    {positions}
    
    Bitte strukturiere deine Antwort wie folgt:
    1. Persönlichkeit & Wesenskern (Sonne & Mond Position)
    2. Kommunikation & Beziehungen (Merkur & Venus)
    3. Handlungskraft & Lebensziel (Mars & Jupiter)
    4. Aktuelle Botschaft des Universums (Inspirierender Abschluss)
    """

    with st.spinner("Astraea verbindet sich mit den Sternen..."):
        st.write_stream(ask_ai(prompt_text))

    st.markdown("---")
    
    # NEU: FRAGE-BEREICH FÜR DIE NUTZER
    st.subheader("💬 Stelle Astraea eine persönliche Frage zu deinem Horoskop")
    user_question = st.text_input("Deine Frage an die Sterne (z.B. 'Was bedeutet mein Mars für meine Karriere?'):")
    
    if st.button("🔮 Frage an Astraea stellen"):
        if user_question.strip():
            question_prompt = f"""
            Du bist Astraea, eine empathische und erfahrene Astrologin.
            Nutzer: {name}
            Planetenstände: {positions}
            
            Der Nutzer stellt dir folgende konkrete Frage:
            "{user_question}"
            
            Beantworte die Frage ausführlich, persönlich und astrologisch fundiert auf Basis seiner Planetenstände.
            """
            with st.spinner("Astraea liest in deinen Sternen..."):
                st.write_stream(ask_ai(question_prompt))
        else:
            st.warning("Bitte gib zuerst eine Frage ein.")

st.markdown("---")
st.caption("🔒 Astraea Astrologie App • Hinweis: Astrologische Interpretationen dienen der Reflexion und Unterhaltung.")