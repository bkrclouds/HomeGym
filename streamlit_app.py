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
        st.error(f"Fehler: {e}")
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

# --- 4. LOGIN & ANMELDUNG (DIREKT BEIM ÖFFNEN) ---
full_data = load_data()

# Session State für Übungsauswahl initialisieren
if 'selected_ex' not in st.session_state:
    st.session_state.selected_ex = ""

st.title("🦾 Iron Hub")

# Login-Bereich im Hauptfenster, wenn noch kein User eingetippt wurde
if "user" not in st.session_state or not st.session_state.user:
    with st.container(border=True):
        st.subheader("Anmeldung")
        user_input = st.text_input("Gib deinen Namen ein:", placeholder="Dein Name...")
        if st.button("Einloggen"):
            if user_input:
                st.session_state.user = user_input.strip()
                st.rerun()
            else:
                st.warning("Bitte gib einen Namen ein.")
    st.stop()

current_user = st.session_state.user

# --- 5. ONBOARDING (WENN NEUER USER) ---
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False

if not user_exists:
    st.header(f"Willkommen, {current_user}!")
    with st.form("onboarding"):
        st.write("Bitte richte dein Profil einmalig ein:")
        c1, c2 = st.columns(2)
        groesse = c1.number_input("Größe (cm)", value=180)
        s_weight = c1.number_input("Startgewicht (kg)", value=80.0)
        z_weight = c2.number_input("Zielgewicht (kg)", value=75.0)
        if st.form_submit_button("Profil erstellen"):
            first_entry = {"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": f"Profil: {groesse}cm", "Gewicht": s_weight, "Sätze": 0, "Wiederholungen": 0, "Ziel": z_weight}
            if save_entry(first_entry, current_user):
                st.success("Profil angelegt!")
                time.sleep(1)
                st.rerun()
    st.stop()

# --- 6. DASHBOARD DATEN ---
data = full_data[full_data['Email'] == current_user]
streak = get_kreatin_streak(data)
weights = data[data['Typ'] == 'Gewicht']
last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
last_workout = data[data['Typ'] == 'Training']['Übung/Info'].iloc[-1] if not data[data['Typ'] == 'Training'].empty else "Kein Training"
ziel_gewicht = float(data['Ziel'].dropna().iloc[0]) if 'Ziel' in data.columns and not data['Ziel'].dropna().empty else 0.0

# --- 7. DASHBOARD ANZEIGE (OBEN) ---
m1, m2, m3 = st.columns(3)
m1.metric("Kreatin-Streak", f"{streak} Tage", "🔥")
m2.metric("Aktuelles Gewicht", f"{last_weight} kg")
m3.metric("Letztes Training", last_workout, "💪")

st.write("---")

# --- 8. TRAININGSKACHEL (EINGABE & KATALOG) ---
with st.container(border=True):
    st.subheader("🏋️‍♂️ Training & Übungen")
    
    # Katalog zum Anklicken
    with st.expander("📚 Übungskatalog öffnen"):
        tabs = st.tabs(["Push", "Pull", "Legs"])
        push_ex = ["Bankdrücken", "Schulterdrücken", "Dips", "Seitheben"]
        pull_ex = ["Klimmzüge", "Rudern", "Bizeps Curls", "Facepulls"]
        legs_ex = ["Kniebeugen", "Beinpresse", "Wadenheben", "Plank"]
        
        with tabs[0]:
            for ex in push_ex:
                if st.button(ex, key=f"btn_{ex}"):
                    st.session_state.selected_ex = ex
                    st.rerun()
        with tabs[1]:
            for ex in pull_ex:
                if st.button(ex, key=f"btn_{ex}"):
                    st.session_state.selected_ex = ex
                    st.rerun()
        with tabs[2]:
            for ex in legs_ex:
                if st.button(ex, key=f"btn_{ex}"):
                    st.session_state.selected_ex = ex
                    st.rerun()

    # Eingabemaske
    u_name = st.text_input("Aktuelle Übung", value=st.session_state.selected_ex)
    c1, c2, c3 = st.columns(3)
    u_kg = c1.number_input("Gewicht (kg)", step=2.5)
    u_s = c2.number_input("Sätze", step=1, value=3)
    u_r = c3.number_input("Wiederholungen", step=1, value=10)
    
    if st.button("🚀 Satz speichern"):
        if u_name:
            if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user):
                st.toast(f"{u_name} gespeichert!")
                st.session_state.selected_ex = ""
                time.sleep(1)
                st.rerun()

# --- 9. WEITERE FUNKTIONEN (GEWICHT & GRAFIK) ---
col_a, col_b = st.columns([1, 2])
with col_a:
    with st.container(border=True):
        st.subheader("🍎 Habits")
        if st.button("💊 Kreatin genommen"):
            save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.rerun()
        st.write("---")
        new_w = st.number_input("Gewicht tracken", value=last_weight, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Check", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.rerun()

with col_b:
    with st.container(border=True):
        st.subheader("📈 Gewichtsverlauf")
        if not weights.empty:
            df_p = weights.copy()
            df_p['Datum'] = pd.to_datetime(df_p['Datum'])
            fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark")
            if ziel_gewicht > 0:
                fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="red", annotation_text="Ziel")
            st.plotly_chart(fig, use_container_width=True)

# --- 10. SIDEBAR (LOGOUT & LÖSCHEN) ---
with st.sidebar:
    st.write(f"Eingeloggt als: **{current_user}**")
    if st.button("Abmelden"):
        st.session_state.user = ""
        st.rerun()
    st.write("---")
    if st.button("🗑️ Letzten Eintrag löschen"):
        if delete_last_entry():
            st.success("Gelöscht!")
            time.sleep(1)
            st.rerun()
