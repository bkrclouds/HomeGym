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

# --- 4. LOGIN & SESSION STATE ---
full_data = load_data()

if 'selected_ex' not in st.session_state:
    st.session_state.selected_ex = ""
if 'ex_info' not in st.session_state:
    st.session_state.ex_info = ""

# --- 5. ANMELDUNG (WIRD ALS ERSTES ANGEZEIGT) ---
if "user" not in st.session_state or not st.session_state.user:
    st.title("🦾 Iron Hub")
    with st.container(border=True):
        st.subheader("Anmeldung")
        user_input = st.text_input("Gib deinen Namen ein:", placeholder="Wer trainiert heute?")
        if st.button("Einloggen"):
            if user_input:
                st.session_state.user = user_input.strip()
                st.rerun()
    st.stop()

current_user = st.session_state.user

# Onboarding Check
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False

if not user_exists:
    st.header(f"Willkommen im Team, {current_user}! 🦾")
    with st.form("onboarding"):
        st.write("Bitte richte kurz dein Profil ein:")
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

# --- 6. DASHBOARD DATEN ---
data = full_data[full_data['Email'] == current_user]
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
last_workout = data[data['Typ'] == 'Training']['Übung/Info'].iloc[-1] if not data[data['Typ'] == 'Training'].empty else "Noch kein Training"
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0

# --- 7. DASHBOARD ANZEIGE (METRIKEN) ---
st.title(f"🦾 Iron Hub Dashboard")
m1, m2, m3 = st.columns(3)
m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
m2.metric("Gewicht", f"{last_weight} kg")
m3.metric("Letzte Übung", last_workout, "💪")

st.write("---")

# --- 8. HAUPTBEREICH: HABITS ZUERST ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    # DAILY HABITS KACHEL (JETZT OBEN)
    with st.container(border=True):
        st.subheader("🍎 Daily Habits")
        st.write("Tracke deine täglichen Erfolge:")
        
        if st.button("💊 Kreatin genommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                st.balloons()
                time.sleep(1)
                st.rerun()
        
        st.write("---")
        new_w = st.number_input("Heutiges Gewicht (kg)", value=last_weight, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                if new_w < last_weight:
                    st.snow()
                st.rerun()

    # GRAFIK UNTER DEN HABITS
    with st.container(border=True):
        st.subheader("📈 Gewichtsverlauf")
        if not weights.empty:
            df_p = weights.copy()
            df_p['Datum'] = pd.to_datetime(df_p['Datum'])
            fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark")
            if ziel_gewicht > 0:
                fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="red", annotation_text="Ziel")
            st.plotly_chart(fig, use_container_width=True)

with col_right:
    # WORKOUT LOG KACHEL
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Workout Log")
        
        # Katalog zum Auswählen
        with st.expander("📚 Übungskatalog & Anleitung"):
            t1, t2, t3 = st.tabs(["Push", "Pull", "Legs/Core"])
            
            katalog = {
                "Push": {
                    "Bankdrücken": "Stange zur Brust, Ellbogen 45°, Füße fest.",
                    "Schulterdrücken": "Hanteln senkrecht hoch, Core fest.",
                    "Dips": "Leicht vorlehnen (Brust) oder aufrecht (Trizeps).",
                    "Seitheben": "Arme bis Schulterhöhe, kleine Finger leicht hoch.",
                    "Schrägbank": "Fokus obere Brust, 30-45° Steigung.",
                    "Butterfly": "Arme wie bei Umarmung führen.",
                    "Military Press": "Langhantel stehend, Po & Bauch fest.",
                    "Trizeps Kabel": "Ellbogen fest am Körper.",
                    "Liegestütze": "Körper wie ein Brett.",
                    "Engbank": "Hände schulterbreit für Trizeps."
                },
                "Pull": {
                    "Klimmzüge": "Brust zur Stange, Schultern runter.",
                    "Rudern (LH)": "Oberkörper parallel, zum Nabel ziehen.",
                    "Latzug": "Zur oberen Brust, Ellbogen runter.",
                    "Bizeps Curls": "Kein Schwung, Ellbogen fest.",
                    "Hammer Curls": "Daumen hoch für Unterarm-Dicke.",
                    "Facepulls": "Seil zur Stirn, Ellbogen hoch.",
                    "Kreuzheben": "Rücken gerade, Stange nah am Schienbein.",
                    "Einarm-Rudern": "Rücken gerade, zur Hüfte ziehen.",
                    "Reverse Flys": "Hintere Schulter, leichtes Gewicht.",
                    "Lat-Überzüge": "Arme fast gestreckt, Zug aus dem Lat."
                },
                "Legs/Core": {
                    "Kniebeugen": "Gewicht auf Fersen, Rücken gerade.",
                    "Beinpresse": "Knie oben nicht ganz durchstrecken.",
                    "Ausfallschritte": "Großer Schritt, Knie fast zum Boden.",
                    "Wadenheben": "Volle Dehnung & oben halten.",
                    "Beinstrecker": "Oben kurz maximal anspannen.",
                    "Beinbeuger": "Fersen zum Po ziehen.",
                    "Plank": "Bauch & Po fest, kein Hohlkreuz.",
                    "Beinheben": "Unteren Rücken an Boden pressen.",
                    "Rumän. Kreuzheben": "Hüfte zurück, Dehnung spüren.",
                    "Russian Twist": "Oberkörper rotieren, Beine hoch."
                }
            }

            def render_list(exercises):
                for name, info in exercises.items():
                    c_n, c_b = st.columns([3, 1])
                    c_n.markdown(f"**{name}**: *{info}*")
                    if c_b.button("Wählen", key=f"ex_{name}"):
                        st.session_state.selected_ex = name
                        st.session_state.ex_info = info
                        st.rerun()

            with t1: render_list(katalog["Push"])
            with t2: render_list(katalog["Pull"])
            with t3: render_list(katalog["Legs/Core"])

        # Eingabemaske
        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        if st.session_state.ex_info:
            st.caption(f"💡 Info: {st.session_state.ex_info}")
            
        c1, c2, c3 = st.columns(3)
        u_kg = c1.number_input("Gewicht (kg)", step=2.5, value=0.0)
        u_s = c2.number_input("Sätze", step=1, value=3)
        u_r = c3.number_input("Reps", step=1, value=10)
        
        if st.button("🚀 SATZ SPEICHERN"):
            if u_name:
                if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user):
                    st.toast("BOOM! ⚡️ Eintrag gespeichert!", icon="⚡")
                    st.session_state.selected_ex = ""
                    st.session_state.ex_info = ""
                    time.sleep(1)
                    st.rerun()

# --- 9. SIDEBAR (LOGOUT & CLEANUP) ---
with st.sidebar:
    st.write(f"Nutzer: **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = ""
        st.rerun()
    st.write("---")
    st.warning("Gefahrenzone")
    if st.button("🗑️ Letzten Eintrag löschen"):
        if delete_last_entry():
            st.success("Eintrag gelöscht!")
            time.sleep(1)
            st.rerun()
