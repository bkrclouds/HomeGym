import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px

# --- 1. SEITEN-SETUP & CSS ---
st.set_page_config(page_title="Iron Hub", page_icon="🦾", layout="wide")

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
    div[data-testid="stExpander"] { background-color: #1E2129; border-radius: 12px; border: 1px solid #333; }
    .btn-danger button {
        background: linear-gradient(135deg, #FF4B4B 0%, #AF0000 100%) !important;
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
if 'show_settings' not in st.session_state: st.session_state.show_settings = False

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

def delete_user_data(user_name):
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

# --- 6. TUTORIAL ---
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
        st.header(["Dein neuer Coach", "Logging", "Plan", "Kreatin", "Bereit?"][st.session_state.step-1])
        st.write(["Begleitung bei jeder Einheit.", "Tracke in Sekunden.", "Dein Plan.", "Streak tracken.", "Let's Go!"][st.session_state.step-1])
        st.markdown('</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if st.session_state.step > 1:
            if c1.button("Zurück"): st.session_state.step -= 1; st.rerun()
        if st.session_state.step < 5:
            if c2.button("Weiter"): st.session_state.step += 1; st.rerun()
        else:
            if c2.button("STARTEN 🚀"): st.session_state.tutorial_done = True; st.rerun()
    st.stop()

# --- 7. DASHBOARD ---
current_user = st.session_state.user
data = full_data[full_data['Email'] == current_user] if not full_data.empty else pd.DataFrame()

if st.session_state.trigger_balloons: st.balloons(); st.session_state.trigger_balloons = False
if st.session_state.trigger_snow: st.snow(); st.session_state.trigger_snow = False

if data.empty:
    st.header(f"Dein Profil einrichten 🦾")
    with st.form("setup"):
        c1, c2 = st.columns(2)
        g = c1.number_input("Größe (cm)", value=180); w = c1.number_input("Startgewicht (kg)", value=80.0); zw = c2.number_input("Zielgewicht (kg)", value=75.0)
        if st.form_submit_button("Profil speichern"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Start", "Gewicht": w, "Sätze": 0, "Wiederholungen": 0, "Ziel": zw}, current_user)
            st.rerun()
    st.stop()

# DATEN BERECHNEN
streak = get_kreatin_streak(data)
weights_df = data[data['Typ'] == 'Gewicht'].copy()
weights_df['Datum'] = pd.to_datetime(weights_df['Datum'])
weights_df = weights_df.sort_values('Datum')

last_weight = float(weights_df['Gewicht'].iloc[-1]) if not weights_df.empty else 0.0
start_weight = float(weights_df['Gewicht'].iloc[0]) if not weights_df.empty else 0.0
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0
wasser_heute = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()
mein_plan = data[data['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

# SETTINGS BUTTON
c_h1, c_h2 = st.columns([0.9, 0.1])
if c_h2.button("⚙️"): st.session_state.show_settings = not st.session_state.show_settings

if st.session_state.show_settings:
    with st.container(border=True):
        st.subheader("Einstellungen")
        if st.button("Abmelden"): st.session_state.user = None; st.rerun()
        
        # Datenschutz Sektion
        with st.expander("🛡️ Datenschutz"):
            st.write("""
            **Allgemeiner Datenschutz:**
            Deine Daten werden ausschließlich zur Darstellung deines Trainingsfortschritts in dieser App verwendet. 
            Wir speichern dein Gewicht, deine Trainingseinheiten und deinen Kreatin-Status in einer gesicherten Datenbank.
            Deine Daten werden nicht an Dritte weitergegeben.
            """)
        
        # Account löschen Sektion
        with st.expander("🗑️ Account löschen"):
            st.warning("Achtung: Dies löscht alle deine Fortschritte unwiderruflich.")
            confirm = st.text_input("Tippe 'LÖSCHEN' zur Bestätigung:")
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if st.button("MEINEN ACCOUNT JETZT LÖSCHEN"):
                if confirm == "LÖSCHEN": 
                    delete_user_data(current_user)
                    st.session_state.user = None
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Schließen"): st.session_state.show_settings = False; st.rerun()
    st.stop()

# DASHBOARD HEADER
st.title(f"🦾 Iron Hub: {current_user}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
m2.metric("Gewicht", f"{last_weight} kg", f"{last_weight - start_weight:.1f} kg")
m3.metric("Wasser", f"{wasser_heute} L", "💧")
m4.metric("Ziel", f"{ziel_gewicht} kg", "🎯")
st.write("---")

# 1. DAILY HABITS & 2. WORKOUT LOG
col_l, col_r = st.columns([1, 1.8], gap="large")

with col_l:
    with st.container(border=True):
        st.subheader("🍎 Daily Habits")
        if st.button("💊 Kreatin genommen"):
            save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.session_state.trigger_balloons = True; st.rerun()
        st.write(f"💧 Wasser: {wasser_heute}L / 3L")
        st.progress(min(wasser_heute / 3.0, 1.0))
        if st.button("+ 0.5L Wasser"):
            save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Wasser", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user); st.rerun()
        new_w = st.number_input("Gewicht", value=last_weight, step=0.1)
        if st.button("⚖️ Speichern"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user)
            if new_w < last_weight: st.session_state.trigger_snow = True
            st.rerun()

with col_r:
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Workout Log")
        with st.expander("📚 Übungs-Katalog"):
            tabs = st.tabs(["Push", "Pull", "Legs"])
            katalog = {"Push": ["Bankdrücken", "Schulterdrücken"], "Pull": ["Klimmzüge", "Rudern"], "Legs": ["Kniebeugen", "Beinpresse"]}
            for i, (cat, items) in enumerate(katalog.items()):
                with tabs[i]:
                    for n in items:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{n}**")
                        if c2.button("Log", key=f"l_{n}"): st.session_state.selected_ex = n; st.rerun()
                        if c3.button("📌 Plan", key=f"a_{n}"):
                            save_entry({"Datum": "PLAN", "Typ": "Plan", "Übung/Info": n, "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user); st.rerun()

        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        c_kg, c_s, c_r = st.columns(3)
        u_kg = c_kg.number_input("kg", step=2.5, value=0.0); u_s = c_s.number_input("Sätze", value=3); u_r = c_r.number_input("Reps", value=10)
        if st.button("🚀 SATZ SPEICHERN"):
            save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
            st.session_state.selected_ex = ""; st.rerun()

# 3. GEWICHTSVERLAUF (GANZ UNTEN)
st.write("---")
with st.container(border=True):
    st.subheader("📈 Gewichtsverlauf & Statistik")
    if not weights_df.empty:
        fig = px.line(weights_df, x='Datum', y='Gewicht', title="Dein Weg zum Ziel", markers=True)
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white")
        fig.update_traces(line_color='#00D4FF')
        st.plotly_chart(fig, use_container_width=True)
