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

def delete_last_entry():
    try:
        existing_data = conn.read(ttl="0s")
        if not existing_data.empty:
            # Entfernt die letzte Zeile
            updated_df = existing_data.drop(existing_data.index[-1])
            conn.update(data=updated_df)
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Fehler beim Löschen: {e}")
        return False

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

# --- 4. 🍔 BURGER MENÜ (SIDEBAR) ---
# WICHTIG: Nur was hier eingerückt ist, erscheint im Menü!
with st.sidebar:
    st.title("🍔 Menü")
    st.markdown("### ⚙️ Einstellungen")
    ziel_gewicht = st.number_input("Dein Zielgewicht (kg)", value=100.0, step=0.1, format="%.1f")
    st.write("---")
    st.info(f"Ziel: **{ziel_gewicht} kg**")

# --- AB HIER: HAUPTSEITE (Nicht mehr eingerückt!) ---

# --- 5. DESIGN (Custom CSS) ---
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

# --- 6. DATEN & LOGIK ---
data = load_data()
streak_count = get_kreatin_streak(data)

if not data.empty:
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
    trainings = data[data['Typ'] == 'Training']
    last_workout = trainings['Übung/Info'].iloc[-1] if not trainings.empty else "Kein Training"
else:
    last_weight, last_workout = 0.0, "Kein Training"

# --- 7. DASHBOARD (METRIKEN) ---
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

# --- 8. INPUT BEREICH ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("### 🍎 Daily Habits")
        if st.button("💊 Kreatin eingenommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}):
                st.balloons()
                time.sleep(2)
                st.rerun()

        st.write("---")
        new_w = st.number_input("Gewicht (kg)", value=last_weight if last_weight > 0 else 80.0, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Körpergewicht", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}):
                if last_weight > 0 and new_w < last_weight: st.snow()
                time.sleep(2)
                st.rerun()

with col_right:
    # --- SESSION STATE INITIALISIERUNG ---
    # Das sorgt dafür, dass die App sich merkt, was du im Guide geklickt hast
    if 'selected_exercise' not in st.session_state:
        st.session_state.selected_exercise = ""

    # --- WORKOUT LOG EINGABE ---
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        
        # Das Eingabefeld zieht sich den Wert jetzt aus dem Session State
        u_name = st.text_input(
            "Name der Übung", 
            value=st.session_state.selected_exercise,
            placeholder="z.B. Bankdrücken",
            key="exercise_input"
        )
        
        c1, c2, c3 = st.columns(3)
        u_kg = c1.number_input("kg", step=2.5, min_value=0.0)
        u_s = c2.number_input("Sätze", step=1, min_value=0)
        u_r = c3.number_input("Reps", step=1, min_value=0)
        
        if st.button("🚀 Satz speichern"):
            if u_name:
                if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}):
                    st.toast(f"{u_name} geloggt! ⚡", icon="⚡")
                    # Nach dem Speichern das Feld leeren
                    st.session_state.selected_exercise = ""
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.warning("Bitte gib einen Namen ein oder wähle eine Übung unten aus.")

    st.write("##")

    # --- ÜBUNGS-GUIDE MIT ÜBERNAHME-FUNKTION ---
    with st.expander("📚 Profi-Übungskatalog (Klick zum Übernehmen)", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Brust & Schultern", "Rücken & Bizeps", "Beine & Core"])

        # Funktion zur Aktualisierung des Eingabefeldes
        def set_exercise(name):
            st.session_state.selected_exercise = name

        with tab1:
            kat_brust = st.selectbox("Übung wählen:", [
                "Wähle eine Übung...", "Bankdrücken (Langhantel)", "Schrägbankdrücken", "Flyes (Kurzhantel)", 
                "Liegestütze", "Dips", "Schulterdrücken", "Seitheben", "Frontheben", "Butterfly"
            ], key="sb_brust")
            
            if kat_brust != "Wähle eine Übung...":
                st.info(f"Anleitung: Hier kommt deine Beschreibung für {kat_brust} hin.")
                if st.button(f"✅ {kat_brust} übernehmen"):
                    set_exercise(kat_brust)
                    st.rerun() # Seite neu laden, um den Wert oben einzusetzen

        with tab2:
            kat_ruecken = st.selectbox("Übung wählen:", [
                "Wähle eine Übung...", "Klimmzüge", "Latzug (Breit)", "Rudern", "Kreuzheben", 
                "Bizeps Curls", "Hammer Curls"
            ], key="sb_ruecken")
            
            if kat_ruecken != "Wähle eine Übung...":
                st.info(f"Anleitung: Fokus auf den Rücken bei {kat_ruecken}.")
                if st.button(f"✅ {kat_ruecken} übernehmen"):
                    set_exercise(kat_ruecken)
                    st.rerun()

        with tab3:
            kat_beine = st.selectbox("Übung wählen:", [
                "Wähle eine Übung...", "Kniebeugen", "Beinpresse", "Ausfallschritte", 
                "Wadenheben", "Plank", "Crunches"
            ], key="sb_beine")
            
            if kat_beine != "Wähle eine Übung...":
                st.info(f"Anleitung: Stabile Basis bei {kat_beine}.")
                if st.button(f"✅ {kat_beine} übernehmen"):
                    set_exercise(kat_beine)
                    st.rerun()
                    
# --- 8. DIAGRAMM (MIT FIX FÜR SYNTAX ERROR) ---
st.write("##")
with st.container(border=True):
    st.markdown("### 📈 Gewichtsverlauf & Ziel")
    if not data.empty and not data[data['Typ'] == 'Gewicht'].empty:
        df_p = data[data['Typ'] == 'Gewicht'].copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        df_p = df_p.sort_values('Datum')
        
        fig = px.line(df_p, x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#007AFF'])
        fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="#FF4B4B", annotation_text=f"Ziel {ziel_gewicht}kg")
        
        all_w = df_p['Gewicht'].tolist() + [ziel_gewicht]
        fig.update_yaxes(range=[min(all_w)-2, max(all_w)+2])
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        # Hier war die Klammer im letzten Versuch offen:
        st.plotly_chart(fig, use_container_width=True)

# --- 10. HISTORIE ---
st.write("##")
with st.expander("📂 Historie & Filter"):
    if not data.empty:
        uebungen = ["Alle"] + sorted(data[data['Typ'] == 'Training']['Übung/Info'].unique().tolist())
        sel = st.selectbox("Übung filtern", uebungen)
        disp = data[data['Übung/Info'] == sel] if sel != "Alle" else data
        st.dataframe(disp.sort_values("Datum", ascending=False), use_container_width=True)




