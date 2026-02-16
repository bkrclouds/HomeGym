import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time
import plotly.express as px

# --- 1. SEITEN-SETUP ---
st.set_page_config(page_title="Iron Hub", page_icon="🦾", layout="wide")

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
        st.error(f"Fehler beim Speichern: {e}")
        return False

def delete_last_entry():
    try:
        existing_data = conn.read(ttl="0s")
        if not existing_data.empty:
            updated_df = existing_data.drop(existing_data.index[-1])
            conn.update(data=updated_df)
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Fehler beim Löschen: {e}")
        return False

def get_kreatin_streak(df):
    if df.empty: return 0
    kreatin_data = df[df['Typ'] == 'Kreatin']
    if kreatin_data.empty: return 0
    kreatin_dates = pd.to_datetime(kreatin_data['Datum']).dt.date.unique()
    kreatin_dates = sorted(kreatin_dates, reverse=True)
    streak, today = 0, date.today()
    check_date = today
    if kreatin_dates[0] < today:
        check_date = today - pd.Timedelta(days=1)
        if kreatin_dates[0] < check_date: return 0
    for d in kreatin_dates:
        if d == check_date:
            streak += 1
            check_date -= pd.Timedelta(days=1)
        elif d < check_date: break
    return streak

# --- 4. LOGIN & ANMELDUNG ---
full_data = load_data()

if 'selected_ex' not in st.session_state:
    st.session_state.selected_ex = ""
if 'ex_info' not in st.session_state:
    st.session_state.ex_info = ""

st.title("🦾 Iron Hub")

if "user" not in st.session_state or not st.session_state.user:
    with st.container(border=True):
        st.subheader("Anmeldung")
        user_input = st.text_input("Dein Name", placeholder="Wer trainiert heute?")
        if st.button("Einloggen"):
            if user_input:
                st.session_state.user = user_input.strip()
                st.rerun()
    st.stop()

current_user = st.session_state.user

# Onboarding Check
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False

if not user_exists:
    st.header(f"Willkommen, {current_user}! 🦾")
    with st.form("onboarding"):
        st.write("Erstelle dein Profil:")
        c1, c2 = st.columns(2)
        groesse = c1.number_input("Größe (cm)", value=180)
        s_weight = c1.number_input("Startgewicht (kg)", value=80.0)
        z_weight = c2.number_input("Zielgewicht (kg)", value=75.0)
        if st.form_submit_button("Profil erstellen"):
            first_entry = {"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Start: {groesse}cm", "Gewicht": s_weight, "Sätze": 0, "Wiederholungen": 0, "Ziel": z_weight}
            if save_entry(first_entry, current_user):
                st.balloons()
                time.sleep(1)
                st.rerun()
    st.stop()

# --- 5. DASHBOARD DATEN ---
data = full_data[full_data['Email'] == current_user]
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
prev_weight = float(weights['Gewicht'].iloc[-2]) if len(weights) > 1 else last_weight
last_workout = data[data['Typ'] == 'Training']['Übung/Info'].iloc[-1] if not data[data['Typ'] == 'Training'].empty else "Kein Training"
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0

# --- 6. DASHBOARD ANZEIGE ---
m1, m2, m3 = st.columns(3)
m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
m2.metric("Gewicht", f"{last_weight} kg")
m3.metric("Letzte Übung", last_workout, "💪")

st.write("---")

# --- 7. TRAININGSKACHEL MIT 30 ÜBUNGEN ---
with st.container(border=True):
    st.subheader("🏋️‍♂️ Workout Log & Guide")
    
    with st.expander("📚 Übungskatalog (Klick für Info & Auswahl)"):
        t1, t2, t3 = st.tabs(["Push (Brust/Schulter/Trizeps)", "Pull (Rücken/Bizeps)", "Legs & Core"])
        
        # Übungs-Listen mit Anleitung
        katalog = {
            "Push": {
                "Bankdrücken": "Stange zur Brust führen, Ellbogen 45 Grad, Füße fest am Boden.",
                "Schulterdrücken": "Hanteln senkrecht hoch, Core fest, kein Hohlkreuz.",
                "Dips": "Oberkörper leicht vor für Brustfokus, aufrecht für Trizeps.",
                "Seitheben": "Arme fast gestreckt bis Schulterhöhe, kleine Finger leicht hoch.",
                "Schrägbankdrücken": "Fokus auf obere Brust, 30-45 Grad Bankeinstellung.",
                "Butterfly": "Konstante Spannung, Arme wie bei einer Umarmung führen.",
                "Military Press": "Langhantel im Stehen drücken, Po und Bauch maximal anspannen.",
                "Trizepsdrücken Kabel": "Ellbogen fest am Körper, nur Unterarme bewegen.",
                "Liegestütze": "Körper wie ein Brett, Hände unter den Schultern.",
                "Engbankdrücken": "Hände schulterbreit für maximalen Trizeps-Fokus."
            },
            "Pull": {
                "Klimmzüge": "Brust zur Stange, Schulterblätter aktiv zusammenziehen.",
                "Rudern (LH)": "Oberkörper parallel zum Boden, Stange zum Bauchnabel.",
                "Latzug": "Stange zur oberen Brust ziehen, Ellbogen nach unten.",
                "Bizeps Curls (SZ)": "Kein Schwung, Ellbogen an den Rippen fixieren.",
                "Hammer Curls": "Daumen nach oben, trainiert Brachialis und Unterarme.",
                "Facepulls": "Seil zur Stirn ziehen, Ellbogen bleiben hoch.",
                "Kreuzheben": "Rücken gerade, Kraft aus den Beinen, Stange nah am Schienbein.",
                "Einarmiges Rudern": "Rücken gerade, Hantel kontrolliert zur Hüfte ziehen.",
                "Reverse Flys": "Fokus auf hintere Schulter, leichte Gewichte nutzen.",
                "Lat-Überzüge": "Arme fast gestreckt, Zug aus dem Latissimus spüren."
            },
            "Legs & Core": {
                "Kniebeugen": "Gewicht auf Fersen, Rücken gerade, Hüfte unter Kniehöhe.",
                "Beinpresse": "Füße schulterbreit, Knie oben nicht ganz durchstrecken.",
                "Ausfallschritte": "Großer Schritt, hinteres Knie kurz vor dem Boden.",
                "Wadenheben": "Voller Bewegungsumfang, oben kurz halten.",
                "Beinstrecker": "Quadrizeps oben maximal anspannen.",
                "Beinbeuger": "Fersen zum Po ziehen, Hüfte fest auf der Bank.",
                "Plank": "Körperspannung halten, kein Durchhängen im Rücken.",
                "Beinheben": "Unteren Rücken fest am Boden lassen.",
                "Rumänisches Kreuzheben": "Hüfte weit zurück, Dehnung im Beinbeuger spüren.",
                "Russian Twist": "Oberkörper rotieren, Füße für mehr Intensität abheben."
            }
        }

        def render_tab(exercises):
            for name, info in exercises.items():
                col_ex, col_btn = st.columns([3, 1])
                col_ex.markdown(f"**{name}**: *{info}*")
                if col_btn.button("Wählen", key=f"sel_{name}"):
                    st.session_state.selected_ex = name
                    st.session_state.ex_info = info
                    st.rerun()

        with t1: render_tab(katalog["Push"])
        with t2: render_tab(katalog["Pull"])
        with t3: render_tab(katalog["Legs & Core"])

    # Eingabemaske
    u_name = st.text_input("Ausgewählte Übung", value=st.session_state.selected_ex)
    if st.session_state.ex_info:
        st.caption(f"💡 Info: {st.session_state.ex_info}")
        
    c1, c2, c3 = st.columns(3)
    u_kg = c1.number_input("Gewicht (kg)", step=2.5, value=0.0)
    u_s = c2.number_input("Sätze", step=1, value=3)
    u_r = c3.number_input("Reps", step=1, value=10)
    
    if st.button("🚀 SATZ SPEICHERN"):
        if u_name:
            if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user):
                st.toast("BOOM! ⚡️ Übung gespeichert!", icon="⚡")
                st.session_state.selected_ex = ""
                st.session_state.ex_info = ""
                time.sleep(1)
                st.rerun()

# --- 8. HABITS & GEWICHT ---
st.write("##")
col_a, col_b = st.columns([1, 2])

with col_a:
    with st.container(border=True):
        st.subheader("🍎 Daily Habits")
        if st.button("💊 Kreatin genommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                st.balloons()
                time.sleep(1)
                st.rerun()
        
        st.write("---")
        new_w = st.number_input("Gewicht (kg)", value=last_weight, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                if new_w < last_weight:
                    st.snow()
                st.rerun()

with col_b:
    with st.container(border=True):
        st.subheader("📈 Gewichtsverlauf")
        if not weights.empty:
            df_p = weights.copy()
            df_p['Datum'] = pd.to_datetime(df_p['Datum'])
            fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#007AFF'])
            if ziel_gewicht > 0:
                fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="red", annotation_text="Ziel")
            st.plotly_chart(fig, use_container_width=True)

# --- 9. SIDEBAR (LOGOUT & DELETE) ---
with st.sidebar:
    st.write(f"Nutzer: **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = ""
        st.rerun()
    st.write("---")
    if st.button("🗑️ Letzten Eintrag löschen"):
        if delete_last_entry():
            st.success("Gelöscht!")
            time.sleep(1)
            st.rerun()
