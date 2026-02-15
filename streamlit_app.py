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

# --- STYLING ---
st.set_page_config(page_title="Iron Hub", page_icon="🏋️‍♂️", layout="wide")

# Custom CSS für den Yazio-Look (Abgerundete Ecken, Schatten)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #ff4b4b; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #262730; color: white; border: 1px solid #444; }
    .stButton>button:hover { border-color: #ff4b4b; color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏋️‍♂️ Iron Hub")

# --- OBEN: ÜBERSICHT (METRICS) ---
# Hier simulieren wir die Yazio-Kacheln für den schnellen Check
m1, m2, m3, m4 = st.columns(4)
m1.metric("Status", "🔥 5 Tage Streak")
m2.metric("Gewicht", "82.5 kg", "-0.2 kg")
m3.metric("Kreatin", "✅ Ja")
m4.metric("Workouts", "12", "Monat")

st.divider()

# --- MITTE: INTERAKTION ---
col_left, col_right = st.columns([1, 2]) # Links schmal für Daily, rechts breit für Log

with col_left:
    with st.container(border=True):
        st.subheader("🍎 Daily Routine")
        kreatin = st.button("💊 Kreatin geloggt")
        if kreatin:
            # Hier deine save_entry Logik für Kreatin
            st.toast("Kreatin gespeichert!", icon="✅")
        
        st.write("---")
        
        weight_input = st.number_input("Aktuelles Gewicht (kg)", min_value=0.0, format="%.1f")
        if st.button("⚖️ Gewicht speichern"):
            # Hier deine save_entry Logik für Gewicht
            st.toast("Gewicht aktualisiert!")

with col_right:
    with st.container(border=True):
        st.subheader("📝 Workout Log")
        
        c1, c2 = st.columns(2)
        with c1:
            uebung = st.selectbox("Übung", ["Bankdrücken", "Kniebeugen", "Kreuzheben", "Schulterdrücken"])
        with c2:
            st.text_input("Notiz", placeholder="Gutes Gefühl heute...")
            
        c3, c4, c5 = st.columns(3)
        with c3:
            gew = st.number_input("Gewicht (kg)", step=2.5)
        with c4:
            saetze = st.number_input("Sätze", step=1)
        with c5:
            wiederh = st.number_input("Reps", step=1)
            
        if st.button("🚀 Satz speichern", type="primary"):
            # Hier deine save_entry Logik für das Workout
            st.balloons()

# --- UNTEN: HISTORIE ---
st.divider()
with st.expander("📊 Deine Historie & Fortschritt", expanded=False):
    # Hier lädst du deine Daten wie bisher
    # data = load_data()
    # st.line_chart(data.set_index('Datum')['Gewicht'])
    st.info("Hier erscheinen bald deine Fortschritts-Graphen!")
