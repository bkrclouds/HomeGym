import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px
import random

# --- 1. SEITEN-SETUP & CSS (HIGH CONTRAST) ---
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

    /* Spezielles Styling für den Löschen-Button */
    .delete-container .stButton>button {
        background: linear-gradient(135deg, #FF4B4B 0%, #AF0000 100%) !important;
        border: none !important;
    }
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
        # Behalte nur Daten, die NICHT zum aktuellen User gehören
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

# --- 6. NAVIGATION (SIDEBAR) ---
with st.sidebar:
    st.title("🦾 Iron Hub")
    page = st.radio("Menü", ["Dashboard", "Einstellungen"])
    st.write("---")
    st.write(f"👤 Eingeloggt als: **{st.session_state.user}**")
    if st.button("Abmelden"):
        st.session_state.user = None
        st.rerun()

# --- 7. TUTORIAL ---
if not st.session_state.tutorial_done:
    st.title(f"Willkommen, {st.session_state.user}!")
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
        
        texts = [
            ("Dein Coach", "Ich begleite dich bei jeder Einheit."),
            ("Schnelles Logging", "Tracke Sätze in Sekunden."),
            ("Dein Plan", "Deine Übungen, immer griffbereit."),
            ("Kreatin 💊", "Bleib am Ball und halte deinen Streak!"),
            ("Bereit?", "Lass uns loslegen!")
        ]
        st.header(texts[st.session_state.step-1][0])
        st.write(texts[st.session_state.step-1][1])
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
            if c_next.button("STARTEN 🚀"):
                st.session_state.tutorial_done = True
                st.rerun()
    st.stop()

# --- 8. SEITEN-LOGIK ---
current_user = st.session_state.user
user_data = full_data[full_data['Email'] == current_user] if not full_data.empty else pd.DataFrame()

if page == "Dashboard":
    if st.session_state.trigger_balloons: st.balloons(); st.session_state.trigger_balloons = False
    if st.session_state.trigger_snow: st.snow(); st.session_state.trigger_snow = False

    if user_data.empty:
        st.header("Profil einrichten")
        with st.form("setup"):
            g = st.number_input("Größe (cm)", value=180)
            w = st.number_input("Gewicht (kg)", value=80.0)
            z = st.number_input("Ziel (kg)", value=75.0)
            if st.form_submit_button("Speichern"):
                save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Start: {g}cm", "Gewicht": w, "Sätze": 0, "Wiederholungen": 0, "Ziel": z}, current_user)
                st.rerun()
        st.stop()

    # Dashboard-Inhalt (Metriken)
    streak = get_kreatin_streak(user_data)
    last_w = float(user_data[user_data['Typ'] == 'Gewicht']['Gewicht'].iloc[-1])
    wasser = user_data[(user_data['Typ'] == 'Wasser') & (user_data['Datum'] == str(date.today()))]['Gewicht'].sum()

    st.title(f"🦾 Dashboard: {current_user}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
    m2.metric("Gewicht", f"{last_w} kg")
    m3.metric("Wasser heute", f"{wasser} L", "💧")

    # Hier folgen deine Habit-Buttons und Workout-Logs (wie im vorigen Code)
    st.info("Logge hier dein heutiges Training!")

elif page == "Einstellungen":
    st.title("⚙️ Einstellungen")
    
    st.subheader("Dein Account")
    st.write(f"Nutzername: **{current_user}**")
    
    st.write("---")
    st.subheader("⚠️ Daten & Datenschutz")
    st.write("Du hast jederzeit das Recht, deine Daten bei uns vollständig zu löschen.")
    
    with st.expander("Account löschen"):
        st.error("Dieser Vorgang kann nicht rückgängig gemacht werden!")
        st.write("Alle Trainingslogs, dein Profil und deine Streaks werden sofort gelöscht.")
        
        confirm = st.text_input("Bestätige die Löschung, indem du 'LÖSCHEN' tippst:")
        
        st.markdown('<div class="delete-container">', unsafe_allow_html=True)
        if st.button("MEINEN ACCOUNT JETZT LÖSCHEN"):
            if confirm == "LÖSCHEN":
                if delete_entire_user(current_user):
                    st.success("Alle Daten wurden entfernt. Du wirst abgemeldet...")
                    time.sleep(2)
                    st.session_state.user = None
                    st.rerun()
            else:
                st.warning("Bitte gib 'LÖSCHEN' ein, um zu bestätigen.")
        st.markdown('</div>', unsafe_allow_html=True)

