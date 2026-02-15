import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. SEITEN-SETUP ---
st.set_page_config(page_title="Iron Hub", page_icon="🦾", layout="wide")

# --- 2. VERBINDUNG & FUNKTIONEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl="10m")
def load_data():
    return conn.read()

def save_entry(new_row_dict):
    try:
        existing_data = conn.read(ttl="0s") # Frisch lesen vor dem Schreiben
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear() # Cache leeren für Aktualisierung
        return True
    except Exception as e:
        st.error(f"Fehler: {e}")
        return False

# --- 3. STYLING (MacroFactory Dark Mode) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    div[data-testid="stMetricValue"] { color: #007AFF; font-weight: bold; }
    .stButton>button {
        border-radius: 15px; border: none;
        background: linear-gradient(135deg, #007AFF 0%, #0051AF 100%);
        color: white; font-weight: bold; height: 3.5em; width: 100%;
    }
    input { background-color: #252525 !important; color: white !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATEN LADEN & DASHBOARD LOGIK ---
data = load_data()

# Standardwerte falls Sheet leer
last_weight = 0.0
prev_weight = 0.0
last_workout = "Kein Training"

if not data.empty:
    # Gewicht finden
    weights = data[data['Typ'] == 'Gewicht']
    if len(weights) >= 1:
        last_weight = float(weights['Gewicht'].iloc[-1])
    if len(weights) >= 2:
        prev_weight = float(weights['Gewicht'].iloc[-2])
    
    # Training finden
    trainings = data[data['Typ'] == 'Training']
    if not trainings.empty:
        last_workout = trainings['Übung/Info'].iloc[-1]

# --- 5. UI: HEADER & METRICS ---
st.title("🦾 HomeGym")
m1, m2, m3 = st.columns(3)

with m1:
    st.metric("Tages-Ziel", "Kreatin", "⏳")
with m2:
    # Delta zeigt an, ob man abgenommen hat
    diff = last_weight - prev_weight if prev_weight > 0 else 0
    st.metric("Gewicht", f"{last_weight} kg", delta=f"{diff:.1f} kg", delta_color="inverse")
with m3:
    st.metric("PUMP", last_workout, "🔥")

st.write("##")

# --- 6. HAUPTBEREICH ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("### 🍎 Daily Habits")
        
        # KREATIN
        if st.button("💊 Kreatin eingenommen"):
    success = save_entry({
        "Datum": str(date.today()), "Typ": "Kreatin", 
        "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0
    })
    if success:
        st.balloons() # Jetzt werden sie abgefeuert
        st.toast("Kreatin geloggt!", icon="✅")
        time.sleep(2) # Wir warten 2 Sekunden, damit man die Ballons sieht
        st.rerun()

        st.write("---")
        
        # GEWICHT
        new_w = st.number_input("Körpergewicht (kg)", value=float(last_weight) if last_weight > 0 else 80.0, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
    success = save_entry({
        "Datum": str(date.today()), "Typ": "Gewicht", 
        "Übung/Info": "Körpergewicht", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0
    })
    if success:
        if new_w < last_weight and last_weight > 0:
            st.snow() # Der "Abnehm-Regen"
            st.toast("Abgenommen! ❤️", icon="❤️")
            time.sleep(2)
        else:
            st.toast("Gewicht gespeichert!", icon="⚖️")
            time.sleep(1)
        st.rerun()

with col_right:
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        
        # Übungseingabe
        u_name = st.text_input("Name der Übung", placeholder="z.B. Bankdrücken")
        
        c1, c2, c3 = st.columns(3)
        with c1: u_kg = st.number_input("kg", step=2.5, key="w_kg")
        with c2: u_s = st.number_input("Sätze", step=1, key="w_s")
        with c3: u_r = st.number_input("Reps", step=1, key="w_r")

       if st.button("🚀 Satz speichern"):
    if u_name:
        success = save_entry({
            "Datum": str(date.today()), "Typ": "Training", 
            "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r
        })
        if success:
            # Da Streamlit keinen Blitz-Regen hat, machen wir hier etwas Cooles:
            st.success("⚡ POWER! Satz gespeichert!") 
            st.toast("BOOM! ⚡", icon="⚡")
            time.sleep(1.5)
            st.rerun()

# --- 7. HISTORIE ---
st.write("##")
with st.expander("📈 Deine Historie"):
    if not data.empty:
        st.dataframe(data.sort_values(by="Datum", ascending=False), use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

