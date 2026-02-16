import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px
import random

# --- 1. SEITEN-SETUP & CSS (HIGH CONTRAST) ---
st.set_page_config(page_title="Iron Hub 2.0", page_icon="🦾", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF !important; }
    label, p, span, .stMarkdown { color: #FFFFFF !important; font-weight: 500; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 800 !important; }
    div[data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 2.5rem !important; }
    .stButton>button {
        border-radius: 12px; border: none; padding: 10px 20px;
        background: linear-gradient(135deg, #007AFF 0%, #00D4FF 100%);
        color: white !important; font-weight: bold; width: 100%;
    }
    .onboarding-card {
        background-color: #1E2129; border-radius: 20px; padding: 25px;
        border: 2px solid #00D4FF; text-align: center; margin-bottom: 20px;
    }
    div[data-testid="stExpander"] { background-color: #1E2129; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION STATE INITIALISIERUNG ---
if 'user' not in st.session_state: st.session_state.user = None
if 'tutorial_done' not in st.session_state: st.session_state.tutorial_done = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'selected_ex' not in st.session_state: st.session_state.selected_ex = ""
if 'trigger_balloons' not in st.session_state: st.session_state.trigger_balloons = False
if 'trigger_snow' not in st.session_state: st.session_state.trigger_snow = False

# --- 4. LOGIN & GERÄTE-ERKENNUNG (ÜBER DB) ---
full_data = conn.read(ttl="5m")

if st.session_state.user is None:
    st.title("🦾 Iron Hub")
    with st.container(border=True):
        st.subheader("Willkommen zurück!")
        name_input = st.text_input("Wie ist dein Name?", placeholder="Dein Name...")
        
        if st.button("Einloggen"):
            if name_input:
                name_clean = name_input.strip()
                st.session_state.user = name_clean
                
                # Check ob User bereits in der Tabelle existiert
                user_exists = not full_data.empty and name_clean in full_data['Email'].values if 'Email' in full_data.columns else False
                
                if user_exists:
                    # User bekannt -> Intro überspringen
                    st.session_state.tutorial_done = True
                else:
                    # Neuer User -> Tutorial starten
                    st.session_state.tutorial_done = False
                st.rerun()
    st.stop()

# --- 5. TUTORIAL (NUR FÜR NEUE NUTZER) ---
if not st.session_state.tutorial_done:
    st.title(f"Schön dich kennenzulernen, {st.session_state.user}!")
    
    with st.container():
        st.markdown('<div class="onboarding-card">', unsafe_allow_html=True)
        
        images = [
            "https://images.unsplash.com/photo-1594381898411-846e7d193883?q=80&w=800",
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=800",
            "https://images.unsplash.com/photo-1434682881908-b43d0467b798?q=80&w=800",
            "https://images.unsplash.com/photo-1593079831268-3381b0db4a77?q=80&w=800",
            "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=800"
        ]
        
        st.image(images[st.session_state.step - 1], use_container_width=True)
        
        if st.session_state.step == 1:
            st.header("Dein neuer Coach")
            st.write("Ich begleite dich ab jetzt bei jeder Einheit. Iron Hub ist dein digitaler Trainingspartner.")
        elif st.session_state.step == 2:
            st.header("Blitzschnelles Logging")
            st.write("Tracke deine Sätze in Sekunden. So bleibt der Fokus auf den Gains, nicht auf dem Handy.")
        elif st.session_state.step == 3:
            st.header("Dein individueller Plan")
            st.write("Stell dir deinen Plan zusammen. Deine Lieblingsübungen sind immer griffbereit.")
        elif st.session_state.step == 4:
            st.header("Der Kreatin-Tracker 💊")
            st.write("Unser Herzstück! Keine andere App trackt deinen Kreatin-Streak so motivierend.")
        elif st.session_state.step == 5:
            st.header("Bereit?")
            st.write("Dein Profil wird gleich erstellt. Let's go!")

        st.markdown('</div>', unsafe_allow_html=True)

        c_back, c_next = st.columns(2)
        if st.session_state.step > 1:
            if c_back.button("Zurück"):
                st.session_state.step -= 1
                st.rerun()
        if st.session_state.step < 5:
            if c_next.button("Weiter"):
                st.session_state.step += 1
                st.rerun()
        else:
            if c_next.button("TUTORIAL BEENDEN & STARTEN 🚀"):
                st.session_state.tutorial_done = True
                st.rerun()
    st.stop()

# --- 6. HILFSFUNKTIONEN ---
def save_entry(new_row_dict, user_name):
    try:
        existing_data = conn.read(ttl="0s")
        new_row_dict["Email"] = user_name 
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except: return False

def get_kreatin_streak(df):
    if df.empty: return 0
    kreatin_data = df[df['Typ'] == 'Kreatin']
    if kreatin_data.empty: return 0
    kreatin_dates = pd.to_datetime(kreatin_data['Datum']).dt.date.unique()
    kreatin_dates = sorted(kreatin_dates, reverse=True)
    streak, today, check_date = 0, date.today(), date.today()
    if kreatin_dates[0] < today:
        check_date = today - pd.Timedelta(days=1)
        if kreatin_dates[0] < check_date: return 0
    for d in kreatin_dates:
        if d == check_date:
            streak += 1
            check_date -= pd.Timedelta(days=1)
        elif d < check_date: break
    return streak

# --- 7. DASHBOARD LOGIK ---

# Animationen
if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False
if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False

current_user = st.session_state.user
data = full_data[full_data['Email'] == current_user] if not full_data.empty else pd.DataFrame()

# Erstmaliges Einrichten des Profils (falls neu)
if data.empty:
    st.header(f"Dein Profil einrichten 🦾")
    with st.form("first_setup"):
        c1, c2 = st.columns(2)
        groesse = c1.number_input("Größe (cm)", value=180)
        s_weight = c1.number_input("Gewicht (kg)", value=80.0)
        z_weight = c2.number_input("Ziel (kg)", value=75.0)
        if st.form_submit_button("Profil speichern"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Start: {groesse}cm", "Gewicht": s_weight, "Sätze": 0, "Wiederholungen": 0, "Ziel": z_weight}, current_user)
            st.session_state.trigger_balloons = True
            st.rerun()
    st.stop()

# --- DATEN BERECHNEN ---
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0
wasser_heute = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()
mein_plan = data[data['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

# --- UI DASHBOARD ---
st.title(f"🦾 Iron Hub: {current_user}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
m2.metric("Gewicht", f"{last_weight} kg")
m3.metric("Wasser", f"{wasser_heute} L", "💧")
m4.metric("Ziel", f"{ziel_gewicht} kg", "🎯")

st.write("---")

col_l, col_r = st.columns([1, 1.8], gap="large")

with col_l:
    with st.container(border=True):
        st.subheader("🍎 Daily Habits")
        if st.button("💊 Kreatin genommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                st.session_state.trigger_balloons = True
                st.rerun()
        
        st.write("---")
        st.write(f"💧 Wasser: {wasser_heute}L / 3L")
        st.progress(min(wasser_heute / 3.0, 1.0))
        if st.button("+ 0.5L Wasser"):
            save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Wasser", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.rerun()
        
        st.write("---")
        new_w = st.number_input("Körpergewicht", value=last_weight, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                if new_w < last_weight: st.session_state.trigger_snow = True
                st.rerun()

    with st.container(border=True):
        st.subheader("📋 Mein Plan")
        for ex in mein_plan:
            cl1, cl2 = st.columns([4,1])
            if cl1.button(f"🏋️ {ex}", key=f"pl_{ex}"):
                st.session_state.selected_ex = ex
                st.rerun()
            if cl2.button("❌", key=f"rm_{ex}"):
                # Einfache Delete-Logik (hier könnte man noch optimieren)
                st.rerun()

with col_r:
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Workout Log")
        with st.expander("📚 Katalog & Plan"):
            tabs = st.tabs(["Push", "Pull", "Legs/Core"])
            katalog = {"Push": ["Bankdrücken", "Schulterdrücken", "Dips", "Seitheben"], "Pull": ["Klimmzüge", "Rudern", "Latzug", "Bizeps"], "Legs/Core": ["Kniebeugen", "Beinpresse", "Plank"]}
            
            for i, (cat, items) in enumerate(katalog.items()):
                with tabs[i]:
                    for n in items:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{n}**")
                        if c2.button("Log", key=f"l_{n}"): st.session_state.selected_ex = n; st.rerun()
                        if c3.button("📌 Plan", key=f"a_{n}"):
                            save_entry({"Datum": "PLAN", "Typ": "Plan", "Übung/Info": n, "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
                            st.toast(f"{n} im Plan!"); time.sleep(0.5); st.rerun()

        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        c_kg, c_s, c_r = st.columns(3)
        u_kg = c_kg.number_input("kg", step=2.5, value=0.0)
        u_s = c_s.number_input("Sätze", step=1, value=3)
        u_r = c_r.number_input("Reps", step=1, value=10)
        if st.button("🚀 SATZ SPEICHERN"):
            if u_name:
                save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
                st.session_state.selected_ex = ""
                st.rerun()

with st.sidebar:
    st.write(f"👤 **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = None
        st.rerun()
