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
        
        st.toast()
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

# --- Daily Habits Bereich ---
with st.container(border=True):
    st.markdown("### 🍎 Daily Habits")
    
    # Beispiel Kreatin-Button
    if st.button("💊 Kreatin eingenommen", use_container_width=True):
        save_entry({
            "Datum": str(date.today()), "Typ": "Kreatin", 
            "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0
        })
        st.toast("Kreatin geloggt!", icon="✅")
    
    st.write("---")
    
# --- DATEN LOGIK FÜR DASHBOARD ---
if not data.empty:
    # Letztes Gewicht finden
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = weights['Gewicht'].iloc[-1] if not weights.empty else 0.0
    
    # Letztes Training finden
    trainings = data[data['Typ'] == 'Training']
    last_workout = trainings['Übung/Info'].iloc[-1] if not trainings.empty else "Kein Training"
else:
    last_weight = 0.0
    last_workout = "Kein Training"

# --- DASHBOARD ANZEIGE ---
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Tages-Ziel", "Kreatin", "⏳")
with m2:
    # Hier nutzen wir jetzt die Variable 'last_weight'
    st.metric("Gewicht", f"{last_weight} kg") 
with m3:
    # Hier nutzen wir 'last_workout'
    st.metric("PUMP", last_workout)
            
data = load_data()

# Den aktuellsten Gewichtswert finden
if not data.empty and "Gewicht" in data['Typ'].values:
    # Filtert nach 'Gewicht' und nimmt den letzten Eintrag
    aktuelle_last_weight = data[data['Typ'] == 'Gewicht']['Gewicht'].iloc[-1]
else:
    aktuelle_last_weight = 0.0

# Jetzt die Metrik mit dem echten Wert füttern
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Tages-Ziel", "Kreatin", "⏳")
with m2:
    # Hier wird jetzt automatisch der Wert aus dem Sheet angezeigt!
    st.metric("Gewicht", f"{aktuelle_last_weight} kg")
with m3:
    st.metric("PUMP", "Leg Day", "🔥")
    
    success = save_entry
    
    if success:
        st.toast(f"Gespeichert: {new_weight} kg", icon="⚖️")
        st.rerun() # Damit die Anzeige oben sofort springt
    
    # 2. In Google Sheets speichern
    save_entry(new_data)
    
    # 3. WICHTIG: Den Cache leeren, damit die App die neuen Daten sofort lädt
    st.cache_data.clear()
    
    # 4. Feedback für dich
    st.toast(f"{new_weight} kg erfolgreich gespeichert!")

with col_right:
    st.markdown("### 🏋️‍♂️ Workout Log")
    with st.container(border=True):
    st.markdown("### 🏋️‍♂️ Workout Log")
    
    # Option A: Freitext-Eingabe für eigene Übungen
    custom_exercise = st.text_input("Übung (z.B. Bankdrücken oder eigene)")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        kg = st.number_input("kg", step=2.5)
    with col_b:
        sets = st.number_input("Sätze", step=1)
    with col_c:
        reps = st.number_input("Reps", step=1)

    if st.button("🔥 Satz speichern", use_container_width=True):
        if custom_exercise:
            save_entry({
                "Datum": str(date.today()),
                "Typ": "Training",
                "Übung/Info": custom_exercise,
                "Gewicht": kg,
                "Sätze": sets,
                "Wiederholungen": reps
            })
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("Bitte gib den Namen der Übung ein!")
        
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
















