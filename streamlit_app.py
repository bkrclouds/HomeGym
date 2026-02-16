import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px
import random

# --- 1. SEITEN-SETUP & CSS ---
st.set_page_config(page_title="Iron Hub 2.0", page_icon="🦾", layout="wide")

# Modernes CSS Design mit Mobile Fix für Textfarbe
st.markdown("""
    <style>
    /* Erzwingt helle Textfarbe auf dunklem Hintergrund für alle Geräte */
    .stApp, .stApp p, .stApp label, .stApp div, .stApp span {
        background-color: #0E1117;
        color: #E0E0E0 !important; 
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important; /* Helles Weiß für Überschriften */
        font-family: 'Inter', sans-serif;
    }
    /* Metrik-Werte in Neon-Blau */
    div[data-testid="stMetricValue"] { color: #00D4FF !important; font-weight: 800; }
    /* Buttons im modernen Gradient-Look */
    .stButton>button {
        border-radius: 12px; border: none; transition: 0.3s;
        background: linear-gradient(135deg, #007AFF 0%, #00D4FF 100%); color: white !important;
        font-weight: bold;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,212,255,0.4); }
    /* Styling für Onboarding-Karten und Expander */
    .onboarding-card {
        background-color: #1E2129; border-radius: 20px; padding: 30px; border: 1px solid #00D4FF;
        text-align: center; margin-bottom: 20px;
    }
    div[data-testid="stExpander"] { border-radius: 12px; border: 1px solid #262730; background-color: #1E2129; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION STATE & EFFEKT-LOGIK ---
if 'tutorial_done' not in st.session_state: st.session_state.tutorial_done = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'selected_ex' not in st.session_state: st.session_state.selected_ex = ""
# Neue States für zuverlässigere Effekte auf Mobile
if 'trigger_balloons' not in st.session_state: st.session_state.trigger_balloons = False
if 'trigger_snow' not in st.session_state: st.session_state.trigger_snow = False
if 'trigger_toast' not in st.session_state: st.session_state.trigger_toast = ""

# --- 4. TUTORIAL (ONBOARDING MIT BILDERN) ---
if not st.session_state.tutorial_done:
    st.title("🦾 Willkommen bei Iron Hub")
    
    with st.container():
        st.markdown('<div class="onboarding-card">', unsafe_allow_html=True)
        
        if st.session_state.step == 1:
            # Bild 1: Willkommen
            st.image("image_3.png", use_container_width=True)
            st.header("Dein neuer Gym-Buddy")
            st.write("Hey! Ich bin dein digitaler Coach. Iron Hub hilft dir, deine Ziele nicht nur zu setzen, sondern auch zu erreichen.")
            
        elif st.session_state.step == 2:
            # Bild 2: Workout Log
            st.image("image_4.png", use_container_width=True)
            st.header("Einfaches Workout-Logging")
            st.write("Vergiss Zettel und Stift. Tracke deine Sätze und Wiederholungen mit nur zwei Klicks – blitzschnell und präzise.")
            
        elif st.session_state.step == 3:
            # Bild 3: Mein Plan
            st.image("image_5.png", use_container_width=True)
            st.header("Dein Plan, deine Regeln")
            st.write("Erstelle aus über 30 Übungen deinen ganz persönlichen Trainingsplan und starte sofort durch.")
            
        elif st.session_state.step == 4:
            # Bild 4: Kreatin USP
            st.image("image_6.png", use_container_width=True)
            st.header("Das Highlight: Kreatin-Tracker 💊")
            st.write("**Wusstest du?** Keine andere Fitness-App bietet dir einen so intuitiven Kreatin-Habit-Tracker mit Streak-Funktion und visueller Belohnung. Bleib am Ball!")
            
        elif st.session_state.step == 5:
            # Bild 5: Startklar
            st.image("image_7.png", use_container_width=True)
            st.header("Bereit für die Gains?")
            st.write("Alles ist bereit. Lass uns gemeinsam an deiner Bestform arbeiten!")

        st.markdown('</div>', unsafe_allow_html=True)

        # Navigation
        col_back, col_next = st.columns([1, 1])
        if st.session_state.step > 1:
            if col_back.button("Zurück"):
                st.session_state.step -= 1
                st.rerun()
        
        if st.session_state.step < 5:
            if col_next.button("Weiter"):
                st.session_state.step += 1
                st.rerun()
        else:
            if col_next.button("Jetzt starten! 🚀"):
                st.session_state.tutorial_done = True
                st.rerun()
    st.stop()

# --- 5. HAUPT-APP LOGIK ---
# Effekte am Anfang des Skripts auslösen (Mobile Fix)
if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False

if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False

if st.session_state.trigger_toast:
    st.toast(st.session_state.trigger_toast, icon="⚡")
    st.session_state.trigger_toast = ""

# Daten laden
full_data = conn.read(ttl="5m")

# Funktionen
def save_entry(new_row_dict, user_name):
    try:
        existing_data = conn.read(ttl="0s")
        new_row_dict["Email"] = user_name 
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except: return False

def delete_specific_plan_entry(user_name, exercise_name):
    try:
        existing_data = conn.read(ttl="0s")
        updated_df = existing_data[~((existing_data['Email'] == user_name) & 
                                     (existing_data['Typ'] == 'Plan') & 
                                     (existing_data['Übung/Info'] == exercise_name))]
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

# ANMELDUNG
if "user" not in st.session_state or not st.session_state.user:
    st.title("🦾 Iron Hub")
    with st.container(border=True):
        st.subheader("Anmeldung")
        user_input = st.text_input("Name eingeben", placeholder="Wer trainiert heute?")
        if st.button("Einloggen"):
            if user_input:
                st.session_state.user = user_input.strip()
                st.rerun()
    st.stop()

current_user = st.session_state.user

# Onboarding (User-Profil)
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False
if not user_exists:
    st.header(f"Willkommen im Team, {current_user}! 🦾")
    with st.form("user_onboarding"):
        c1, c2 = st.columns(2)
        groesse = c1.number_input("Größe (cm)", value=180)
        s_weight = c1.number_input("Startgewicht (kg)", value=80.0)
        z_weight = c2.number_input("Zielgewicht (kg)", value=75.0)
        if st.form_submit_button("Profil anlegen"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Start: {groesse}cm", "Gewicht": s_weight, "Sätze": 0, "Wiederholungen": 0, "Ziel": z_weight}, current_user)
            st.session_state.trigger_balloons = True # State für Ballons setzen
            st.rerun()
    st.stop()

# --- DATEN FILTERN ---
data = full_data[full_data['Email'] == current_user]
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0
wasser_heute = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()
mein_plan = data[data['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

# Motivation
quotes = ["Schweiß ist Fett, das weint.", "Disziplin schlägt Talent.", "Wer nicht anfängt, hat schon verloren.", "Eat big, lift big.", "Der einzige schlechte Workout ist der, den du nicht gemacht hast."]
st.caption(f"✨ {random.choice(quotes)}")

# --- UI DASHBOARD ---
st.title(f"🦾 Dashboard: {current_user}")
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
        # Kreatin Button mit neuer State-Logik
        if st.button("💊 Kreatin genommen", use_container_width=True):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                st.session_state.trigger_balloons = True
                st.rerun()
        st.write("---")
        progress = min(wasser_heute / 3.0, 1.0)
        st.write(f"💧 Wasser: {wasser_heute}L / 3L")
        st.progress(progress)
        if st.button("+ 0.5L Wasser", use_container_width=True):
            save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Wasser", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.rerun()
        st.write("---")
        new_w = st.number_input("Gewicht (kg)", value=last_weight, step=0.1)
        if st.button("⚖️ Gewicht speichern", use_container_width=True):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                if new_w < last_weight:
                    st.session_state.trigger_snow = True # State für Schnee setzen
                st.rerun()

    with st.container(border=True):
        st.subheader("📋 Mein Plan")
        for ex in mein_plan:
            cl1, cl2 = st.columns([4,1])
            if cl1.button(f"🏋️ {ex}", key=f"pl_{ex}", use_container_width=True):
                st.session_state.selected_ex = ex; st.rerun()
            if cl2.button("❌", key=f"rm_{ex}"):
                delete_specific_plan_entry(current_user, ex); st.rerun()

with col_r:
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Workout Log")
        with st.expander("📚 Katalog & Plan"):
            tabs = st.tabs(["Push", "Pull", "Legs/Core"])
            katalog = {
                "Push": ["Bankdrücken", "Schulterdrücken", "Dips", "Seitheben", "Schrägbank"],
                "Pull": ["Klimmzüge", "Rudern (LH)", "Latzug", "Bizeps Curls", "Kreuzheben"],
                "Legs/Core": ["Kniebeugen", "Beinpresse", "Wadenheben", "Plank", "Beinheben"]
            }
            def render_cat(lst):
                for n in lst:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    if c2.button("Log", key=f"l_{n}"): st.session_state.selected_ex = n; st.rerun()
                    if c3.button("📌 Plan", key=f"a_{n}"):
                        save_entry({"Datum": "PLAN", "Typ": "Plan", "Übung/Info": n, "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
                        st.session_state.trigger_toast = f"{n} im Plan!"
                        st.rerun()
            with tabs[0]: render_cat(katalog["Push"])
            with tabs[1]: render_cat(katalog["Pull"])
            with tabs[2]: render_cat(katalog["Legs/Core"])

        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        c_kg, c_s, c_r = st.columns(3)
        u_kg = c_kg.number_input("kg", step=2.5, value=0.0)
        u_s = c_s.number_input("Sätze", step=1, value=3)
        u_r = c_r.number_input("Reps", step=1, value=10)
        if st.button("🚀 SATZ SPEICHERN", use_container_width=True):
            if u_name:
                save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
                st.session_state.trigger_toast = "Starkes Set!"
                st.session_state.selected_ex = ""
                st.rerun()

    if not weights.empty:
        df_p = weights.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#00D4FF'])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

with st.sidebar:
    st.write(f"👤 **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = ""; st.rerun()
