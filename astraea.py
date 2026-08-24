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

# Custom Styling
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


def ask_ai_text(prompt):
    if "GROQ_API_KEY" in st.secrets:
        if not groq_available:
            return "⚠️ GROQ_API_KEY gefunden, aber das Python-Paket 'groq' ist nicht installiert."
        
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
                return "⚠️ Keine aktiven Modelle für diesen Groq API-Key gefunden."

            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"⚠️ Fehler beim Groq API-Aufruf: {e}"

    if ollama_available:
        try:
            response = ollama.chat(
                model='llama3',
                messages=[{'role': 'user', 'content': prompt}],
                stream=False,
            )
            return response['message']['content']
        except Exception as e:
            return f"⚠️ Lokales Ollama nicht erreichbar: {e}"

    return "⚠️ 'GROQ_API_KEY' wurde in den Streamlit Cloud Secrets nicht gefunden."


# --- SPEICHER (SESSION STATE) SCHUTZ ---
if "positions" not in st.session_state:
    st.session_state["positions"] = None
if "initial_analysis" not in st.session_state:
    st.session_state["initial_analysis"] = None
if "answers" not in st.session_state:
    st.session_state["answers"] = []


# --- OBERFLÄCHE ---
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

# Klick auf Berechnen
if st.sidebar.button("🔮 Horoskop Berechnen & Analysieren"):
    st.session_state["positions"] = get_planet_positions(birth_date, birth_time)
    st.session_state["initial_analysis"] = None
    st.session_state["answers"] = []

# Wenn ein Horoskop berechnet wurde
if st.session_state["positions"] is not None:
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

    # Erst-Analyse generieren (falls noch nicht vorhanden)
    if st.session_state["initial_analysis"] is None:
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
            st.session_state["initial_analysis"] = ask_ai_text(prompt_text)

    st.write(st.session_state["initial_analysis"])

    st.markdown("---")
    
    # --- TEXTFELD FÜR FRAGEN (FEST VERANKERT) ---
    st.subheader("💬 Stelle Astraea eine Frage zu deinem Horoskop")
    
    with st.form(key="question_form", clear_on_submit=True):
        user_question = st.text_input(
            "Deine Frage an Astraea:", 
            placeholder="z.B. Was bedeutet mein Mars-Stand für meine Karriere?"
        )
        submit_button = st.form_submit_button(label="🔮 Frage stellen")

    if submit_button and user_question.strip():
        question_prompt = f"""
        Du bist Astraea, eine empathische und erfahrene Astrologin.
        Nutzer: {name}
        Planetenstände: {positions}
        
        Frage des Nutzers: "{user_question}"
        
        Beantworte die Frage präzise, empathisch und astrologisch fundiert auf Basis seiner Planetenstände.
        """
        with st.spinner("Astraea liest in deinen Sternen..."):
            answer_text = ask_ai_text(question_prompt)
            st.session_state["answers"].append((user_question, answer_text))

    # Verlauf anzeigen
    if st.session_state["answers"]:
        for q, a in reversed(st.session_state["answers"]):
            st.markdown(f"**❓ Deine Frage:** {q}")
            st.markdown(f"**🌟 Astraeas Antwort:**\n{a}")
            st.markdown("---")

st.markdown("---")
st.caption("🔒 Astraea Astrologie App • Hinweis: Astrologische Interpretationen dienen der Reflexion und Unterhaltung.")