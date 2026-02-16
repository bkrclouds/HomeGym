import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px
import random

# --- 1. SEITEN-SETUP & CSS (MOBILE OPTIMIZED) ---
st.set_page_config(page_title="Iron Hub 2.0", page_icon="🦾", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF !important; }
    label, p, span, .stMarkdown { color: #FFFFFF !important; font-weight: 500; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 800 !important; }
    div[data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 2.5rem !important; }
    
    /* Buttons Styling */
    .stButton>button {
        border-radius: 12px; border: none; padding: 10px 20px;
        background: linear-gradient(135deg, #007AFF 0%, #00D4FF 100%);
        color: white !important; font-weight: bold; width: 100%;
    }
    
    /* Mobile Navigation Bar */
    .mobile-nav {
        display: flex;
        justify-content: space-around;
        background-color: #1E2129;
        padding: 10px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }

    .onboarding-card {
        background-color: #1E2129; border-radius: 20px; padding: 25px;
        border: 2px solid #00D4FF; text-align: center; margin-bottom: 20px;
    }
    
    div[data-testid="stExpander"] { background-color: #1E2129; border-radius: 12px; }

    /* Roter Button für Löschvorgänge */
    .btn-danger>div>button {
        background: linear-gradient(135deg, #FF4B4B 0%, #B22222 100%) !important;
    }
    
    /* Sidebar Fix für Mobile (optionales visuelles Feedback) */
    section[data-testid="stSidebar"] {
        background-color: #161920 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'tutorial_done' not in st.session_state: st.session_state.tutorial_done = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'selected_ex' not in st.session_state: st.session_state.selected_ex = ""
if 'trigger_balloons' not in st.session_state: st.session_state.trigger_balloons = False
if 'trigger_snow' not in st.session_state: st.session_state.trigger_snow = False
# Neuer State für die Seitenwahl (damit es am Handy ohne Sidebar klappt)
if 'current_page' not in st.session_state: st.session_state.current_page = "Dashboard"

# --- 4. HILFSFUNKTIONEN ---
def save_entry(new_row_dict, user_name):
    try:
        existing_data = conn.read(ttl="0s")
        new_row_dict["Email"] = user_name 
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except: return False

def delete_entire_user(user_name):
    try:
        existing_data = conn.read(ttl="0s")
        updated_df = existing_data[existing_data['Email'] != user_name]
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

# --- 5. LOGIN ---
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
                user_exists = not full_data.empty and name_clean in full_data['Email'].values if 'Email' in full_data.columns else False
                st.session_state.tutorial_done = True if user_exists else False
                st.rerun()
    st.stop()

# --- 6. NAVIGATION (SIDEBAR + MOBILE TOP NAV) ---
# Sidebar bleibt für PC-Nutzer erhalten
with st.sidebar:
    st.title("🦾 Iron Hub")
    choice = st.radio("Menü", ["Dashboard", "Einstellungen"], index=0 if st.session_state.current_page == "Dashboard" else 1)
    st.session_state.current_page = choice
    st.write("---")
    if st.button("Abmelden"):
        st.session_state.user = None
        st.rerun()

# Mobile Top-Nav (Sichtbar auf dem Handy, falls Sidebar zu ist)
if st.session_state.user:
    c_nav1, c_nav2 = st.columns(2)
    if c_nav1.button("🏠 Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
    if c_nav2.button("⚙️ Einstellungen"):
        st.session_state.current_page = "Einstellungen"
        st.rerun()
    st.write("---")

# --- 7. TUTORIAL ---
if not st.session_state.tutorial_done:
    # (Tutorial Logik bleibt identisch...)
    st.title(f"Schön dich kennenzulernen!")
    st.markdown(f'<div class="onboarding-card">Schritt {st.session_state.step} von 5</div>', unsafe_allow_html=True)
    if st.button("Tutorial überspringen"):
        st.session_state.tutorial_done = True
        st.rerun()
    st.stop()

# --- 8. DASHBOARD SEITE ---
if st.session_state.current_page == "Dashboard":
    if st.session_state.trigger_balloons: st.balloons(); st.session_state.trigger_balloons = False
    if st.session_state.trigger_snow: st.snow(); st.session_state.trigger_snow = False

    current_user = st.session_state.user
    data = full_data[full_data['Email'] == current_user] if not full_data.empty else pd.DataFrame()

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

    # DATEN BERECHNEN
    streak = get_kreatin_streak(data)
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
    ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0
    wasser_heute = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()
    mein_plan = data[data['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

    # METRIKEN
    st.title(f"🦾 Iron Hub: {current_user}")
    m1, m2 = st.columns(2)
    m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
    m2.metric("Gewicht", f"{last_weight} kg")
    m3, m4 = st.columns(2)
    m3.metric("Wasser", f"{wasser_heute} L", "💧")
    m4.metric("Ziel", f"{ziel_gewicht} kg", "🎯")

    st.write("---")

    # DASHBOARD CONTENT
    col_l, col_r = st.columns([1, 1.8], gap="small")

    with col_l:
        with st.container(border=True):
            st.subheader("🍎 Daily Habits")
            if st.button("💊 Kreatin genommen"):
                if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                    st.session_state.trigger_balloons = True
                    st.rerun()
            st.write(f"💧 Wasser: {wasser_heute}L / 3L")
            st.progress(min(wasser_heute / 3.0, 1.0))
            if st.button("+ 0.5L Wasser"):
                save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Wasser", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user)
                st.rerun()
            new_w = st.number_input("Gewicht loggen", value=last_weight, step=0.1)
            if st.button("⚖️ Gewicht speichern"):
                if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                    if new_w < last_weight: st.session_state.trigger_snow = True
                    st.rerun()

    with col_r:
        with st.container(border=True):
            st.subheader("🏋️‍♂️ Workout Log")
            with st.expander("📚 Katalog & Plan"):
                tabs = st.tabs(["Push", "Pull", "Legs"])
                katalog = {"Push": ["Bankdrücken", "Schulterdrücken", "Dips"], "Pull": ["Klimmzüge", "Rudern", "Latzug"], "Legs": ["Kniebeugen", "Beinpresse"]}
                for i, (cat, items) in enumerate(katalog.items()):
                    with tabs[i]:
                        for n in items:
                            c1, c2 = st.columns([3, 1])
                            c1.write(n)
                            if c2.button("Log", key=f"l_{n}"): st.session_state.selected_ex = n; st.rerun()

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

# --- 9. EINSTELLUNGEN SEITE ---
elif st.session_state.current_page == "Einstellungen":
    st.title("⚙️ Einstellungen")
    st.write(f"Konto: **{st.session_state.user}**")
    
    st.write("---")
    with st.expander("Konto löschen"):
        st.warning("Dies löscht alle Daten dauerhaft.")
        confirm = st.text_input("Tippe 'LÖSCHEN'")
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        if st.button("JETZT LÖSCHEN"):
            if confirm == "LÖSCHEN":
                delete_entire_user(st.session_state.user)
                st.session_state.user = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
