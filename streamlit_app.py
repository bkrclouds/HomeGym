import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- SEITEN-SETUP ---
st.set_page_config(page_title="My Fitness Hub", page_icon="🏋️‍♂️", layout="centered")

# --- VERBINDUNG ZU GOOGLE SHEETS ---
# Wir erstellen eine Verbindung zur Tabelle
conn = st.connection("gsheets", type=GSheetsConnection)

# Funktion zum Laden der Daten
def load_data():
    return conn.read(ttl="10m") # ttl=0 sorgt dafür, dass wir immer die neuesten Daten sehen

# Funktion zum Speichern eines neuen Eintrags
def save_entry(new_row_dict):
    try:
        # Wir holen die Daten aus dem Cache (schnell!)
        existing_data = load_data()
        
        # Neue Daten anhängen
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        
        # Einmaliger Schreibvorgang zu Google
        conn.update(data=updated_df)
        
        # WICHTIG: Cache löschen, damit die Historie beim nächsten Mal aktuell ist
        st.cache_data.clear()
        
        st.balloons()
        st.success("Erfolgreich im Sheet gespeichert!")
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            st.error("Google braucht kurz Pause (Limit erreicht). Bitte in 1 Minute nochmal probieren!")
        else:
            st.error(f"Fehler: {e}")

# --- ADVANCED DARK UI (MacroFactory Style) ---
st.markdown("""
    <style>
    /* Hintergrund: Tiefes Anthrazit */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    /* Yazio-Style Cards */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 0 10px 15px rgba(0,0,0,0.3);
    }

    /* Buttons: MacroFactory Blau/Neon */
    .stButton>button {
        border-radius: 15px;
        border: none;
        background: linear-gradient(135deg, #007AFF 0%, #0051AF 100%);
        color: white;
        font-weight: bold;
        height: 3.5em;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0,122,255,0.4);
    }

    /* Eingabefelder im Dark Mode */
    input {
        background-color: #252525 !important;
        border-radius: 10px !important;
        border: 1px solid #444 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER & QUICK METRICS ---
st.title("🦾 Iron Hub")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Tages-Ziel", "Kreatin", "⏳")
with m2:
    st.metric("Gewicht", "82.4 kg", "-0.1 kg")
with m3:
    st.metric("PUMP", "Leg Day", "🔥")

st.write("##")

# --- HAUPTBEREICH (Zwei Spalten wie Yazio) ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown("### 🍎 Daily Habits")
    with st.container(border=True):
        if st.button("💊 Kreatin eingenommen", use_container_width=True):
            # Hier deine save_entry Logik
            st.toast("Kreatin geloggt!", icon="⚡")
        
        st.write("---")
        new_weight = st.number_input("Körpergewicht (kg)", value=82.4, step=0.1)
        if st.button("⚖️ Gewicht speichern", use_container_width=True):
            # Hier deine save_entry Logik
            st.toast("Gewicht aktualisiert!")

with col_right:
    st.markdown("### 🏋️‍♂️ Workout Log")
    with st.container(border=True):
        # Übungsvorgaben nach Kategorien
        kategorie = st.selectbox("Muskelgruppe", ["Brust", "Rücken", "Beine", "Schultern", "Arme"])
        
        uebungen_dict = {
            "Brust": ["Bankdrücken", "Schrägbankdrücken", "Butterfly"],
            "Rücken": ["Klimmzüge", "Rudern (Langhantel)", "Latziehen"],
            "Beine": ["Kniebeugen", "Beinpresse", "Kreuzheben"],
            "Schultern": ["Schulterdrücken", "Seitheben"],
            "Arme": ["Bizeps Curls", "Trizeps Drücken"]
        }
        
        selected_exercise = st.selectbox("Übung wählen", uebungen_dict[kategorie])
        
        c1, c2, c3 = st.columns(3)
        with c1:
            kg = st.number_input("Gewicht", step=2.5)
        with c2:
            sets = st.number_input("Sätze", step=1)
        with c3:
            reps = st.number_input("Reps", step=1)
            
        if st.button("🔥 Satz speichern", type="primary", use_container_width=True):
            # Hier deine save_entry Logik
            st.balloons()
            st.success(f"{selected_exercise} gespeichert!")

# --- HISTORIE ---
st.write("##")
with st.expander("📈 Deine Fortschritte"):
    st.write("Hier folgt bald die grafische Auswertung deiner Daten!")
