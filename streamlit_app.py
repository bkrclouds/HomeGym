import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- 1. SEITEN-SETUP & CSS ---
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
    
    div[data-testid="stExpander"] { background-color: #1E2129; border-radius: 12px; border: 1px solid #333; }

    .btn-danger>div>button {
        background: linear-gradient(135deg, #FF4B4B 0%, #B22222 100%) !important;
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
        st.subheader("Willkommen!")
        name_input = st.text_input("Wie ist dein Name?", placeholder="Dein Name...")
        if st.button("Einloggen / Registrieren"):
            if name_input:
                name_clean = name_input.strip()
                st.session_state.user = name_clean
                user_exists = not full_data.empty and name_clean in full_data['Email'].values if 'Email' in full_data.columns else False
                st.session_state.tutorial_done = True if user_exists else False
                st.rerun()
    st.stop()

# --- 6. NAVIGATION ---
with st.sidebar:
    st.title("🦾 Iron Hub")
    choice = st.radio("Menü", ["Dashboard", "Einstellungen"], index=0 if st.session_state.current_page == "Dashboard" else 1)
    st.session_state.current_page = choice
    if st.button("Abmelden"):
        st.session_state.user = None
        st.rerun()

# --- 7. TUTORIAL (FÜR NEUE USER) ---
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
        
        steps_content = [
            ("Dein neuer Coach", "Ich begleite dich ab jetzt bei jeder Einheit."),
            ("Blitzschnelles Logging", "Tracke deine Sätze in Sekunden."),
            ("Dein individueller Plan", "Stell dir deinen Plan zusammen."),
            ("Der Kreatin-Tracker 💊", "Verpasse nie wieder deinen Streak."),
            ("Bereit?", "Lass uns dein Profil erstellen!")
        ]
        st.header(steps_content[st.session_state.step-1][0])
        st.write(steps_content[st.session_state.step-1][1])
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if st.session_state.step > 1:
            if c1.button("Zurück"):
                st.session_state.step -= 1
                st.rerun()
        if st.session_state.step < 5:
            if c2.button("Weiter"):
                st.session_state.step += 1
                st.rerun()
        else:
            if c2.button("TUTORIAL BEENDEN 🚀"):
                st.session_state.tutorial_done = True
                st.rerun()
    st.stop()

# --- 8. DASHBOARD ---
if st.session_state.current_page == "Dashboard":
    # Mobile Top-Nav (nur sichtbar wenn eingeloggt)
    c_nav1, c_nav2 = st.columns(2)
    c_nav1.button("🏠 Dashboard", disabled=True) # Aktive Seite
    if c_nav2.button("⚙️ Einstellungen"):
        st.session_state.current_page = "Einstellungen"
        st.rerun()
    st.write("---")

    if st.session_state.trigger_balloons: st.balloons(); st.session_state.trigger_balloons = False
    if st.session_state.trigger_snow: st.snow(); st.session_state.trigger_snow = False

    current_user = st.session_state.user
    data = full_data[full_data['Email'] == current_user] if not full_data.empty else pd.DataFrame()

    if data.empty:
        st.header("Profil einrichten")
        with st.form("setup"):
            g = st.number_input("Größe (cm)", value=180); w = st.number_input("Gewicht (kg)", value=80.0)
            if st.form_submit_button("Speichern"):
                save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Start", "Gewicht": w, "Sätze": 0, "Wiederholungen": 0, "Ziel": 75.0}, current_user)
                st.rerun()
        st.stop()

    # Logik & UI
    streak = get_kreatin_streak(data)
    last_weight = float(data[data['Typ'] == 'Gewicht']['Gewicht'].iloc[-1])
    wasser = data[(data['Typ'] == 'Wasser') & (data['Datum'] == str(date.today()))]['Gewicht'].sum()

    st.title(f"🦾 Iron Hub: {current_user}")
    m1, m2 = st.columns(2)
    m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
    m2.metric("Gewicht", f"{last_weight} kg")
    
    col_l, col_r = st.columns([1, 1.8], gap="medium")
    with col_l:
        with st.container(border=True):
            st.subheader("Daily Habits")
            if st.button("💊 Kreatin"):
                save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
                st.session_state.trigger_balloons = True; st.rerun()
            st.write(f"💧 Wasser: {wasser}L / 3L")
            if st.button("+ 0.5L Wasser"):
                save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Wasser", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user); st.rerun()

    with col_r:
        with st.container(border=True):
            st.subheader("Training loggen")
            u_name = st.text_input("Übung", value=st.session_state.selected_ex)
            c1, c2, c3 = st.columns(3)
            u_kg = c1.number_input("kg", value=0.0); u_s = c2.number_input("Sätze", value=3); u_r = c3.number_input("Reps", value=10)
            if st.button("🚀 SATZ SPEICHERN"):
                save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
                st.success("Gespeichert!"); time.sleep(0.5); st.rerun()

# --- 9. EINSTELLUNGEN ---
elif st.session_state.current_page == "Einstellungen":
    c_nav1, c_nav2 = st.columns(2)
    if c_nav1.button("🏠 Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
    c_nav2.button("⚙️ Einstellungen", disabled=True)
    st.write("---")

    st.title("⚙️ Einstellungen")
    with st.expander("Konto löschen"):
        st.error("Alle Daten werden gelöscht!")
        if st.button("BESTÄTIGEN & LÖSCHEN"):
            delete_entire_user(st.session_state.user)
            st.session_state.user = None
            st.rerun()
