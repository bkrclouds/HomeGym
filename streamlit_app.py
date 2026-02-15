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

# --- MODERN CLEAN DESIGN ---
st.markdown("""
    <style>
    /* Hintergrund und Schrift */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Karten-Style für Container */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Buttons wie App-Kacheln */
    .stButton>button {
        border-radius: 12px;
        border: none;
        background-color: #007BFF;
        color: white;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
    }

    /* Eingabefelder verschönern */
    .stNumberInput, .stTextInput, .stSelectbox {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP LAYOUT ---
st.title("☀️ My Fitness Hub")

# Dashboard Bereich
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tages-Ziel", "Kreatin", "⏳ Offen")
    with col2:
        st.metric("Gewicht", "82.4 kg", "-0.1 kg")
    with col3:
        st.metric("Training", "Leg Day", "Heute")

st.write("##") # Abstand

# Haupt-Interaktion
tab1, tab2 = st.tabs(["🚀 Quick Log", "📈 Fortschritt"])

with tab1:
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### Daily Routine")
        with st.container(border=True):
            if st.button("✅ Kreatin eingenommen"):
                # Hier deine Speicher-Funktion aufrufen
                st.toast("Sauber! Kreatin ist drin.")
            
            weight = st.number_input("Gewicht tracken", value=82.4)
            if st.button("⚖️ Gewicht speichern"):
                st.toast("Gewicht gespeichert!")

    with c2:
        st.markdown("### Workout Log")
        with st.container(border=True):
            exercise = st.selectbox("Übung", ["Bankdrücken", "Kniebeugen", "Latzug"])
            col_a, col_b = st.columns(2)
            with col_a:
                kg = st.number_input("kg", step=2.5)
            with col_b:
                reps = st.number_input("Reps", step=1)
            
            if st.button("➕ Satz hinzufügen", type="primary"):
                st.balloons()
