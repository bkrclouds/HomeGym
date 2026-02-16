import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px
import random

# --- 1. SEITEN-SETUP & CSS (HIGH CONTRAST FÜR MOBILE) ---
st.set_page_config(page_title="Iron Hub 2.0", page_icon="🦾", layout="wide")

st.markdown("""
    <style>
    /* Globaler High Contrast Mode */
    .stApp { background-color: #0E1117; color: #FFFFFF !important; }
    
    /* Erzwingt weißen Text für alle Labels und Texte */
    label, p, span, .stMarkdown { color: #FFFFFF !important; font-weight: 500; }
    
    /* Überschriften in Reinweiß */
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 800 !important; }

    /* Neon-Blaue Metriken */
    div[data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 2.5rem !important; }
    div[data-testid="stMetricDelta"] > div { color: #FF4B4B !important; } /* Gewichtsziel-Delta */

    /* Moderne Buttons */
    .stButton>button {
        border-radius: 12px; border: none; padding: 10px 20px;
        background: linear-gradient(135deg, #007AFF 0%, #00D4FF 100%);
        color: white !important; font-weight: bold; width: 100%;
    }
    
    /* Onboarding Card */
    .onboarding-card {
        background-color: #1E2129; border-radius: 20px; padding: 25px;
        border: 2px solid #00D4FF; text-align: center; margin-bottom: 20px;
    }
    
    /* Expander & Container Styling */
    div[data-testid="stExpander"] { background-color: #1E2129; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG & FUNKTIONEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_entry(new_row_dict, user_name):
    try:
        existing_data = conn.read(ttl="0s")
        new_row_dict["Email"] = user_name 
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Speicherfehler: {e}")
        return False

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

# --- 3. SESSION STATE INITIALISIERUNG ---
if 'tutorial_done' not in st.session_state: st.session_state.tutorial_done = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'selected_ex' not in st.session_state: st.session_state.selected_ex = ""
if 'trigger_balloons' not in st.session_state: st.session_state.trigger_balloons = False
if 'trigger_snow' not in st.session_state: st.session_state.trigger_snow = False

# --- 4. TUTORIAL (ONBOARDING) ---
if not st.session_state.tutorial_done:
    st.title("🦾 Willkommen bei Iron Hub")
    
    with st.container():
        st.markdown('<div class="onboarding-card">', unsafe_allow_html=True)
        
        # Tutorial Bilder von Unsplash (stabil & passend)
        images = [
            "https://images.unsplash.com/photo-1594381898411-846e7d193883?q=80&w=800", # Coach
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=800", # Logging
            "https://images.unsplash.com/photo-1434682881908-b43d0467b798?q=80&w=800", # Plan
            "https://images.unsplash.com/photo-1593079831268-3381b0db4a77?q=80&w=800", # Kreatin
            "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=800"  # Start
        ]
        
        st.image(images[st.session_state.step - 1], use_container_width=True)
        
        if st.session_state.step == 1:
            st.header("Dein neuer Coach")
            st.write("Hey! Ich begleite dich ab jetzt bei jeder Einheit. Iron Hub ist mehr als nur ein Logbuch – es ist dein digitaler Trainingspartner.")
        elif st.session_state.step == 2:
            st.header("Blitzschnelles Logging")
            st.write("Kein unnötiger Schnickschnack. Wähle deine Übung und speichere deine Sätze in Sekunden. So bleibt der Fokus auf dem Training.")
        elif st.session_state.step == 3:
            st.header("Dein individueller Plan")
            st.write("Stell dir deinen persönlichen Plan aus unserem Katalog zusammen. Deine Lieblingsübungen sind immer nur einen Klick entfernt.")
        elif st.session_state.step == 4:
            st.header("Einzigartiger Kreatin-Tracker 💊")
            st.write("Wusstest du? Fast keine App trackt deine Supplements so motivierend wie wir. Verpasse nie wieder deinen Streak!")
        elif st.session_state.step == 5:
            st.header("Bereit für die Gains?")
            st.write("Schnapp dir dein Equipment. Wir fangen jetzt an!")

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
            if c_next.button("LET'S GO! 🚀"):
                st.session_state.tutorial_done = True
                st.rerun()
    st.stop()

# --- 5. DASHBOARD & LOGIK ---

# Animationen auslösen (bevor der Rest lädt)
if st.session_state.trigger_balloons:
    st.balloons()
    st.session_state.trigger_balloons = False
if st.session_state.trigger_snow:
    st.snow()
    st.session_state.trigger_snow = False

full_data = conn.read(ttl="5m")

if "user" not in st.session_state or not st.session_state.user:
    st.title("🦾 Iron Hub Login")
    user_input = st.text_input("Name eingeben", placeholder="Wer trainiert heute?")
    if st.button("Einloggen"):
        if user_input:
            st.session_state.user = user_input.strip()
            st.rerun()
    st.stop()

current_user = st.session_state.user
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False

if not user_exists:
    st.header(f"Willkommen im Team, {current_user}!")
    with st.form("onboarding"):
        c1, c2 = st.columns(2)
        groesse = c1.number_input("Größe (cm)", value=180)
        s_weight = c1.number_input("Gewicht (kg)", value=80.0)
        z_weight = c2.number_input("Ziel (kg)", value=75.0)
        if st.form_submit_button("Profil erstellen"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Start: {groesse}cm", "Gewicht": s_weight, "Sätze": 0, "Wiederholungen": 0, "Ziel": z_weight}, current_user)
            st.session_state.trigger_balloons = True
            st.rerun()
    st.stop()

# --- DATEN BERECHNEN ---
data = full_data[full_data['Email'] == current_user]
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0
wasser_heute = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()
mein_plan = data[data['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

# --- DASHBOARD UI ---
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
                if new_w < last_weight:
                    st.session_state.trigger_snow = True
                st.rerun()

    with st.container(border=True):
        st.subheader("📋 Mein Plan")
        for ex in mein_plan:
            cl1, cl2 = st.columns([4,1])
            if cl1.button(f"🏋️ {ex}", key=f"pl_{ex}"):
                st.session_state.selected_ex = ex
                st.rerun()
            if cl2.button("❌", key=f"rm_{ex}"):
                delete_specific_plan_entry(current_user, ex)
                st.rerun()

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
                        st.toast(f"{n} im Plan!")
                        time.sleep(0.5); st.rerun()
            with tabs[0]: render_cat(katalog["Push"])
            with tabs[1]: render_cat(katalog["Pull"])
            with tabs[2]: render_cat(katalog["Legs/Core"])

        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        c_kg, c_s, c_r = st.columns(3)
        u_kg = c_kg.number_input("kg", step=2.5, value=0.0)
        u_s = c_s.number_input("Sätze", step=1, value=3)
        u_r = c_r.number_input("Reps", step=1, value=10)
        if st.button("🚀 SATZ SPEICHERN"):
            if u_name:
                save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
                st.toast("⚡ Starkes Set!", icon="⚡")
                st.session_state.selected_ex = ""
                time.sleep(1); st.rerun()

    if not weights.empty:
        df_p = weights.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#00D4FF'])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

with st.sidebar:
    st.write(f"👤 **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = ""
        st.rerun()
