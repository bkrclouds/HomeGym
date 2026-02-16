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
    """Speichert einen Eintrag und fügt automatisch den User hinzu."""
    try:
        existing_data = conn.read(ttl="0s")
        # Hier fixen wir den NameError: Wir hängen den User direkt an das Dict an
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

# --- 4. DATEN LADEN & NUTZER-CHECK ---
full_data = load_data()

with st.sidebar:
    st.title("🍔 Menü")
    current_user = st.selectbox("👤 Profil wählen", ["Bitte wählen...", "Pascal", "Frau", "Bruder"])
    st.write("---")

# STOPP, wenn kein Nutzer gewählt ist
if current_user == "Bitte wählen...":
    st.title("🦾 Iron Hub")
    st.info("Willkommen! Bitte wähle links dein Profil aus, um deine Daten zu sehen.")
    st.stop()

# Prüfen, ob der Nutzer schon existiert (Onboarding)
user_exists = not full_data.empty and current_user in full_data['Email'].values if 'Email' in full_data.columns else False

if not user_exists:
    st.balloons()
    st.header(f"Willkommen im Team, {current_user}! 🦾")
    st.subheader("Richten wir kurz dein Profil ein:")
    with st.form("onboarding_form"):
        s_weight = st.number_input("Dein aktuelles Startgewicht (kg)", value=80.0, step=0.1)
        z_weight = st.number_input("Dein Zielgewicht (kg)", value=75.0, step=0.1)
        if st.form_submit_button("Profil speichern & Starten"):
            first_entry = {
                "Datum": str(date.today()), 
                "Typ": "Gewicht", 
                "Übung/Info": "Profil-Start", 
                "Gewicht": s_weight, 
                "Sätze": 0, "Wiederholungen": 0
            }
            if save_entry(first_entry, current_user):
                st.success("Profil erstellt!")
                time.sleep(1)
                st.rerun()
    st.stop()

# Ab hier: Filter die Daten nur für den aktuellen User
data = full_data[full_data['Email'] == current_user]

# --- 5. SIDEBAR EINSTELLUNGEN ---
with st.sidebar:
    st.markdown("### ⚙️ Einstellungen")
    ziel_gewicht = st.number_input("Zielgewicht (kg)", value=100.0, step=0.1, format="%.1f")
    st.write("---")
    st.warning("⚠️ Gefahrenzone")
    if st.button("🗑️ Letzten Eintrag löschen"):
        if delete_last_entry():
            st.success("Gelöscht!")
            time.sleep(1)
            st.rerun()

# --- 6. DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    div[data-testid="stMetricValue"] { color: #007AFF; font-weight: bold; }
    .stButton>button {
        border-radius: 15px; border: none;
        background: linear-gradient(135deg, #007AFF 0%, #0051AF 100%);
        color: white; font-weight: bold; height: 3em; width: 100%;
    }
    input { background-color: #252525 !important; color: white !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 7. DASHBOARD LOGIK ---
streak_count = get_kreatin_streak(data)
if 'selected_exercise' not in st.session_state:
    st.session_state.selected_exercise = ""

if not data.empty:
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
    trainings = data[data['Typ'] == 'Training']
    last_workout = trainings['Übung/Info'].iloc[-1] if not trainings.empty else "Kein Training"
else:
    last_weight, last_workout = 0.0, "Kein Training"

# --- 8. DASHBOARD ANZEIGE ---
st.title(f"🦾 Iron Hub: {current_user}")
m1, m2, m3 = st.columns(3)
with m1: st.metric("Kreatin-Streak", f"{streak_count} Tage", "🔥" if streak_count > 0 else "❄️")
with m2: st.metric("Gewicht", f"{last_weight} kg", delta=f"{last_weight - ziel_gewicht:.1f} kg zum Ziel", delta_color="inverse")
with m3: st.metric("PUMP", last_workout, "🔥")

# --- 9. HAUPTBEREICH (EINGABE) ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("### 🍎 Daily Habits")
        if st.button("💊 Kreatin eingenommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user):
                st.balloons()
                time.sleep(1)
                st.rerun()
        st.write("---")
        new_w = st.number_input("Gewicht (kg)", value=last_weight if last_weight > 0 else 80.0, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Körpergewicht", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}, current_user):
                if last_weight > 0 and new_w < last_weight: st.snow()
                time.sleep(1)
                st.rerun()

with col_right:
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        u_name = st.text_input("Übung", value=st.session_state.selected_exercise, placeholder="Name eingeben")
        c1, c2, c3 = st.columns(3)
        u_kg, u_s, u_r = c1.number_input("kg", step=2.5), c2.number_input("Sätze", step=1), c3.number_input("Reps", step=1)
        if st.button("🚀 Satz speichern"):
            if u_name and save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user):
                st.toast("BOOM! ⚡")
                st.session_state.selected_exercise = ""
                time.sleep(1)
                st.rerun()

# --- 10. KATALOG & GRAPHS ---
with st.expander("📚 Übungskatalog"):
    # (Hier kommt dein Tab-Code aus dem Original hin - gekürzt für die Übersicht)
    selected = st.selectbox("Schnellauswahl", ["Bankdrücken (LH)", "Klimmzüge", "Kniebeugen"])
    if st.button("Übernehmen"):
        st.session_state.selected_exercise = selected
        st.rerun()

st.write("##")
with st.container(border=True):
    st.markdown("### 📈 Dein Gewichtsverlauf")
    if not data[data['Typ'] == 'Gewicht'].empty:
        df_p = data[data['Typ'] == 'Gewicht'].copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        fig = px.line(df_p.sort_values('Datum'), x='Datum', y='Gewicht', markers=True, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with st.expander("📂 Deine Historie"):
    st.dataframe(data.sort_values("Datum", ascending=False), use_container_width=True)
