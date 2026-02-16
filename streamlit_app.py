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
        new_row_dict["Email"] = user_name # Wir nutzen "Email" als Spalte für den User-Namen
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False

# --- 4. LOGIN & ONBOARDING ---
full_data = load_data()

with st.sidebar:
    st.title("👤 Login")
    # Freie Texteingabe statt fester Liste
    current_user = st.text_input("Dein Name", value="", placeholder="Name eingeben...").strip()
    st.write("---")

if not current_user:
    st.title("🦾 Iron Hub")
    st.info("Willkommen! Bitte gib links deinen Namen ein, um zu starten.")
    st.stop()

# Prüfen, ob der Nutzer schon existiert
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False

if not user_exists:
    st.header(f"Willkommen beim ersten Start, {current_user}! 🦾")
    st.subheader("Richten wir dein Profil ein:")
    
    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        with col1:
            groesse = st.number_input("Größe (cm)", min_value=100, max_value=250, value=180)
            s_weight = st.number_input("Aktuelles Gewicht (kg)", min_value=30.0, value=80.0, step=0.1)
        with col2:
            z_weight = st.number_input("Zielgewicht (kg)", min_value=30.0, value=75.0, step=0.1)
            geschlecht = st.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"])
            
        if st.form_submit_button("Profil erstellen & Training starten"):
            # Erster Eintrag speichert die Stammdaten
            first_entry = {
                "Datum": str(date.today()), 
                "Typ": "Gewicht", 
                "Übung/Info": f"Profil: {groesse}cm, {geschlecht}", 
                "Gewicht": s_weight, 
                "Sätze": 0, 
                "Wiederholungen": 0,
                "Ziel": z_weight # Wir speichern das Ziel direkt mit ab
            }
            if save_entry(first_entry, current_user):
                st.success("Profil erfolgreich erstellt!")
                time.sleep(1)
                st.rerun()
    st.stop()

# Daten für den aktuellen User filtern
data = full_data[full_data['Email'] == current_user]

# --- 5. DASHBOARD WERTE BERECHNEN ---
if not data.empty:
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
    # Zielgewicht aus den User-Daten holen (falls vorhanden)
    try:
        ziel_gewicht = float(data['Ziel'].dropna().iloc[0])
    except:
        ziel_gewicht = 0.0
    
    trainings = data[data['Typ'] == 'Training']
    last_workout = trainings['Übung/Info'].iloc[-1] if not trainings.empty else "Kein Training"
else:
    last_weight, last_workout, ziel_gewicht = 0.0, "Kein Training", 0.0

# --- 6. DASHBOARD ANZEIGE ---
st.title(f"🦾 Dashboard: {current_user}")
m1, m2, m3 = st.columns(3)
with m1:
    kreatin_streak = 0 # (Funktion get_kreatin_streak hier einfügen falls gewünscht)
    st.metric("Kreatin-Streak", f"{kreatin_streak} Tage")
with m2:
    st.metric("Aktuelles Gewicht", f"{last_weight} kg")
with m3:
    st.metric("Letztes Training", last_workout)

# --- 7. EINGABEBEREICH ---
st.write("##")
col_input, col_graph = st.columns([1, 1.5], gap="large")

with col_input:
    with st.container(border=True):
        st.markdown("### 📝 Neuer Eintrag")
        option = st.selectbox("Was möchtest du tracken?", ["Training", "Gewicht", "Kreatin"])
        
        if option == "Training":
            u_name = st.text_input("Übung")
            c1, c2, c3 = st.columns(3)
            u_kg = c1.number_input("kg", step=2.5)
            u_s = c2.number_input("Sätze", step=1)
            u_r = c3.number_input("Reps", step=1)
            if st.button("🚀 Speichern"):
                save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
                st.rerun()
                
        elif option == "Gewicht":
            new_w = st.number_input("Gewicht (kg)", value=last_weight, step=0.1)
            if st.button("⚖️ Speichern"):
                save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Körpergewicht", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user)
                st.rerun()

        elif option == "Kreatin":
            if st.button("💊 Kreatin genommen"):
                save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
                st.rerun()

# --- 8. GRAFIK ---
with col_graph:
    with st.container(border=True):
        st.markdown("### 📈 Gewichtsverlauf")
        if not weights.empty:
            df_plot = weights.copy()
            df_plot['Datum'] = pd.to_datetime(df_plot['Datum'])
            fig = px.line(df_plot.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark")
            # Ziellinie einblenden
            if ziel_gewicht > 0:
                fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="red", annotation_text="Dein Ziel")
            st.plotly_chart(fig, use_container_width=True)

# --- 9. GEFAHRENZONE ---
with st.sidebar:
    st.write("---")
    if st.button("🗑️ Letzten Eintrag löschen"):
        from __main__ import delete_last_entry # Falls Funktion oben definiert
        delete_last_entry()
        st.rerun()
