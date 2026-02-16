import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px
import random

# --- 1. SEITEN-SETUP ---
st.set_page_config(page_title="Iron Hub 2.0", page_icon="🦾", layout="wide")

# Modernes CSS Design
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { color: #00D4FF; font-family: 'Inter', sans-serif; font-weight: 800; }
    .stButton>button {
        border-radius: 12px; border: none; transition: 0.3s;
        background: linear-gradient(135deg, #007AFF 0%, #00D4FF 100%); color: white;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,212,255,0.4); }
    div[data-testid="stExpander"] { border-radius: 12px; border: 1px solid #262730; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. FUNKTIONEN ---
@st.cache_data(ttl="5m")
def load_data():
    return conn.read()

def save_entry(new_row_dict, user_name):
    try:
        existing_data = conn.read(ttl="0s")
        new_row_dict["Email"] = user_name 
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Fehler: {e}")
        return False

def delete_specific_plan_entry(user_name, exercise_name):
    try:
        existing_data = conn.read(ttl="0s")
        # Alle Zeilen behalten, außer diejenige, die den Plan dieser Übung für diesen User enthält
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

# --- 4. LOGIN & SESSION STATE ---
full_data = load_data()
if 'selected_ex' not in st.session_state: st.session_state.selected_ex = ""

# --- 5. ANMELDUNG ---
if "user" not in st.session_state or not st.session_state.user:
    st.title("🦾 Iron Hub")
    with st.container(border=True):
        st.subheader("Willkommen zurück")
        user_input = st.text_input("Name eingeben", placeholder="Wer bist du?")
        if st.button("Starten"):
            if user_input:
                st.session_state.user = user_input.strip()
                st.rerun()
    st.stop()

current_user = st.session_state.user

# Onboarding
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False
if not user_exists:
    st.header(f"Hey {current_user}! Erstelle dein Profil:")
    with st.form("onboarding"):
        c1, c2 = st.columns(2)
        groesse = c1.number_input("Größe (cm)", value=180)
        s_weight = c1.number_input("Gewicht (kg)", value=80.0)
        z_weight = c2.number_input("Ziel (kg)", value=75.0)
        if st.form_submit_button("Account erstellen"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Start: {groesse}cm", "Gewicht": s_weight, "Sätze": 0, "Wiederholungen": 0, "Ziel": z_weight}, current_user)
            st.balloons()
            st.rerun()
    st.stop()

# --- 6. DATEN & LOGIK ---
data = full_data[full_data['Email'] == current_user]
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0
wasser_heute = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()
mein_plan = data[data['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

# Motivation
quotes = ["Schweiß ist Fett, das weint.", "Disziplin schlägt Talent.", "Wer nicht anfängt, hat schon verloren.", "Eat big, lift big."]
st.caption(f"✨ {random.choice(quotes)}")

# --- 7. DASHBOARD ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
m2.metric("Gewicht", f"{last_weight} kg")
m3.metric("Wasser", f"{wasser_heute} L", "💧")
m4.metric("Ziel", f"{ziel_gewicht} kg", "🎯")

st.write("---")

# --- 8. LAYOUT ---
col_left, col_right = st.columns([1, 1.8], gap="large")

with col_left:
    # HABITS
    with st.container(border=True):
        st.subheader("🍎 Daily Habits")
        if st.button("💊 Kreatin eingenommen", use_container_width=True):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                st.balloons()
                st.rerun()
        
        st.write("---")
        # Wasser mit Progress Bar
        st.write(f"💧 **Wasser:** {wasser_heute}L / 3.0L")
        progress = min(wasser_heute / 3.0, 1.0)
        st.progress(progress)
        if st.button("+ 0.5L Wasser", use_container_width=True):
            save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Wasser", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.rerun()
        
        st.write("---")
        # Gewicht
        new_w = st.number_input("Körpergewicht", value=last_weight, step=0.1)
        if st.button("⚖️ Gewicht speichern", use_container_width=True):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                if new_w < last_weight: st.snow()
                st.rerun()

    # INDIVIDUELLER PLAN
    with st.container(border=True):
        st.subheader("📋 Dein Plan")
        if mein_plan:
            for ex in mein_plan:
                c_ex, c_del = st.columns([4, 1])
                if c_ex.button(f"🏋️ {ex}", key=f"p_{ex}", use_container_width=True):
                    st.session_state.selected_ex = ex
                    st.rerun()
                if c_del.button("❌", key=f"del_{ex}"):
                    delete_specific_plan_entry(current_user, ex)
                    st.rerun()
        else: st.info("Füge Übungen aus dem Katalog hinzu.")

with col_right:
    # WORKOUT LOG
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Workout Log")
        with st.expander("📚 Übungskatalog"):
            tabs = st.tabs(["Push", "Pull", "Legs/Core"])
            katalog = {
                "Push": ["Bankdrücken", "Schulterdrücken", "Dips", "Seitheben", "Schrägbank"],
                "Pull": ["Klimmzüge", "Rudern (LH)", "Latzug", "Bizeps Curls", "Kreuzheben"],
                "Legs/Core": ["Kniebeugen", "Beinpresse", "Wadenheben", "Plank", "Beinheben"]
            }
            def render_cat(name_list):
                for name in name_list:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{name}**")
                    if c2.button("Log", key=f"log_{name}"):
                        st.session_state.selected_ex = name
                        st.rerun()
                    if c3.button("📌 Plan", key=f"add_{name}"):
                        save_entry({"Datum": "PLAN", "Typ": "Plan", "Übung/Info": name, "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
                        st.toast(f"{name} im Plan!")
                        time.sleep(0.5); st.rerun()
            with tabs[0]: render_cat(katalog["Push"])
            with tabs[1]: render_cat(katalog["Pull"])
            with tabs[2]: render_cat(katalog["Legs/Core"])

        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        c1, c2, c3 = st.columns(3)
        u_kg = c1.number_input("kg", step=2.5, value=0.0)
        u_s = c2.number_input("Sätze", step=1, value=3)
        u_r = c3.number_input("Reps", step=1, value=10)
        if st.button("🚀 SATZ SPEICHERN", use_container_width=True):
            if u_name:
                save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
                st.toast("⚡ Starkes Set!", icon="⚡")
                st.session_state.selected_ex = ""
                time.sleep(1); st.rerun()

    # GRAPH
    with st.container(border=True):
        if not weights.empty:
            df_p = weights.copy()
            df_p['Datum'] = pd.to_datetime(df_p['Datum'])
            fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#00D4FF'])
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)

# --- 9. SIDEBAR ---
with st.sidebar:
    st.write(f"👤 **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = ""
        st.rerun()
