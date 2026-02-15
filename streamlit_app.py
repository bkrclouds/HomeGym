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

def save_entry(new_row_dict):
    try:
        existing_data = conn.read(ttl="0s")
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False

def get_kreatin_streak(df):
    if df.empty: return 0
    kreatin_dates = pd.to_datetime(df[df['Typ'] == 'Kreatin']['Datum']).dt.date.unique()
    kreatin_dates = sorted(kreatin_dates, reverse=True)
    if not kreatin_dates: return 0
    streak = 0
    today = date.today()
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

# --- 4. 🍔 BURGER MENÜ (SIDEBAR) ---
# Alles hierunter ist eingerückt und erscheint NUR links im Menü
with st.sidebar:
    st.title("🍔 Menü")
    st.markdown("### ⚙️ Einstellungen")
    ziel_gewicht = st.number_input("Dein Zielgewicht (kg)", value=100.0, step=0.1, format="%.1f")
    st.write("---")
    st.info(f"Dein aktuelles Ziel: **{ziel_gewicht} kg**")
    st.write("Hier kannst du dein Ziel jederzeit anpassen.")

# --- AB HIER: HAUPTSEITE (Nicht mehr eingerückt!) ---

# --- 5. DESIGN (Dark Mode Styling) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    div[data-testid="stMetricValue"] { color: #007AFF; font-weight: bold; }
    .stButton>button {
        border-radius: 15px; border: none;
        background: linear-gradient(135deg, #007AFF 0%, #0051AF 100%);
        color: white; font-weight: bold; height: 3.5em; width: 100%;
    }
    input { background-color: #252525 !important; color: white !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 6. DATEN LADEN & LOGIK ---
data = load_data()
streak_count = get_kreatin_streak(data)

if not data.empty:
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
    
    trainings = data[data['Typ'] == 'Training']
    last_workout = trainings['Übung/Info'].iloc[-1] if not trainings.empty else "Kein Training"
else:
    last_weight, last_workout = 0.0, "Kein Training"

# --- 7. DASHBOARD (OBEN) ---
st.title("🦾 Iron Hub")
m1, m2, m3 = st.columns(3)

with m1:
    st.metric("Kreatin-Streak", f"{streak_count} Tage", "🔥" if streak_count > 0 else "❄️")
with m2:
    diff_to_goal = last_weight - ziel_gewicht
    st.metric("Gewicht", f"{last_weight} kg", delta=f"{diff_to_goal:.1f} kg zum Ziel", delta_color="inverse")
with m3:
    st.metric("PUMP", last_workout, "🔥")

st.write("##")

# --- 8. HAUPTBEREICH (INPUTS) ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("### 🍎 Daily Habits")
        if st.button("💊 Kreatin eingenommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}):
                st.balloons()
                st.toast("Kreatin geloggt!", icon="✅")
                time.sleep(2)
                st.rerun()

        st.write("---")
        new_w = st.number_input("Gewicht (kg)", value=last_weight if last_weight > 0 else 80.0, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Körpergewicht", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}):
                if last_weight > 0 and new_w < last_weight:
                    st.snow()
                    st.toast("Abgenommen! ❤️", icon="❤️")
                else:
                    st.toast("Gewicht gespeichert!", icon="⚖️")
                time.sleep(2)
                st.rerun()

with col_right:
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        u_name = st.text_input("Name der Übung", placeholder="z.B. Bankdrücken")
        c1, c2, c3 = st.columns(3)
        u_kg = c1.number_input("kg", step=2.5)
        u_s = c2.number_input("Sätze", step=1)
        u_r = c3.number_input("Reps", step=1)
        if st.button("🚀 Satz speichern"):
            if u_name:
                if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}):
                    st.toast("BOOM! ⚡", icon="⚡")
                    st.success(f"{u_name} gespeichert!")
                    time.sleep(1.5)
                    st.rerun()

# --- 9. 📈 DIAGRAMM (ZOOM & ZIEL-LINIE) ---
st.write("##")
with st.container(border=True):
    st.markdown("### 📉 Gewichtsverlauf & Ziel")
    if not data.empty and not data[data['Typ'] == 'Gewicht'].empty:
        df_plot = data[data['Typ'] == 'Gewicht'].copy()
        df_plot['Datum'] = pd.to_datetime(df_plot['Datum'])
        df_plot = df_plot.sort_values('Datum')
        
        fig = px.line(df_plot, x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#007AFF'])
        
        # Ziel-Linie hinzufügen
        fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="#FF4B4B", annotation_text=f"Ziel {ziel_gewicht}kg")
        
        # Zoom berechnen (Ziel und Daten müssen sichtbar sein)
        all_w = df_plot['Gewicht'].tolist() + [ziel_gewicht]
        fig.update_yaxes(range=[min(all_w)-2, max(all_w)+2], fixedrange=False)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        st.plotly_chart(fig, use_container
