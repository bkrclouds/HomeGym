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
    # --- WORKOUT LOG EINGABE ---
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        u_name = st.text_input("Name der Übung", placeholder="z.B. Bankdrücken")
        
        c1, c2, c3 = st.columns(3)
        u_kg = c1.number_input("kg", step=2.5, min_value=0.0)
        u_s = c2.number_input("Sätze", step=1, min_value=0)
        u_r = c3.number_input("Reps", step=1, min_value=0)
        
        if st.button("🚀 Satz speichern"):
            if u_name:
                if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}):
                    st.toast(f"{u_name} geloggt! ⚡", icon="⚡")
                    st.success("Erfolg gespeichert!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.warning("Bitte gib einen Namen für die Übung ein.")

    st.write("##") # Abstandhalter

    # --- ÜBUNGS-GUIDE (UNTERMENÜ) ---
    with st.expander("📚 Profi-Übungskatalog (30+ Übungen)", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Brust & Schultern", "Rücken & Bizeps", "Beine & Core"])

        with tab1:
            # --- BRUST & SCHULTERN ---
            kat_brust = st.selectbox("Übung wählen (Brust/Schulter):", [
                "Bankdrücken (Langhantel)", "Schrägbankdrücken", "Flyes (Kurzhantel)", "Liegestütze", "Dips",
                "Schulterdrücken (Military Press)", "Seitheben", "Frontheben", "Butterfly", "Push-ups (Diamond)"
            ])
            guides_b = {
                "Bankdrücken (Langhantel)": "Klassiker für die Brust. Stange zur Mitte der Brust führen, Ellbogen leicht nach innen.",
                "Schrägbankdrücken": "Fokus auf die obere Brust. Bank auf ca. 30-45 Grad einstellen.",
                "Flyes (Kurzhantel)": "Dehnung der Brustmuskulatur. Arme fast gestreckt wie bei einer Umarmung führen.",
                "Liegestütze": "Körperspannung halten! Hände unter den Schultern, Brust berührt fast den Boden.",
                "Dips": "Fokus auf untere Brust und Trizeps. Oberkörper leicht nach vorne lehnen.",
                "Schulterdrücken (Military Press)": "Core anspannen, kein Hohlkreuz! Gewicht senkrecht über den Kopf drücken.",
                "Seitheben": "Hanteln seitlich führen, bis die Arme parallel zum Boden sind. Kleine Finger leicht höher.",
                "Frontheben": "Gewicht vor dem Körper auf Augenhöhe heben. Nicht mit dem Körper schwingen.",
                "Butterfly": "Konstante Spannung auf der Brust. Hände auf Brusthöhe zusammenführen.",
                "Push-ups (Diamond)": "Hände bilden ein Dreieck unter der Brust. Fokus auf Trizeps und innere Brust."
            }
            st.info(guides_b[kat_brust])

        with tab2:
            # --- RÜCKEN & BIZEPS ---
            kat_ruecken = st.selectbox("Übung wählen (Rücken/Bizeps):", [
                "Klimmzüge", "Latzug (Breit)", "Rudern (Langhantel)", "Einarmiges Rudern", "Kreuzheben",
                "Hyperextensions", "Facepulls", "Bizeps Curls (SZ)", "Hammer Curls", "Konzentrations-Curls"
            ])
            guides_r = {
                "Klimmzüge": "Hände weit greifen, Brust zur Stange ziehen. Schulterblätter aktiv nach unten.",
                "Latzug (Breit)": "Stange zur oberen Brust ziehen, leichtes Zurücklehnen erlaubt.",
                "Rudern (Langhantel)": "Oberkörper fast parallel zum Boden. Stange zum Bauchnabel ziehen.",
                "Einarmiges Rudern": "Auf Bank abstützen. Hantel kontrolliert zur Hüfte ziehen.",
                "Kreuzheben": "Rücken gerade! Kraft kommt aus den Beinen und dem unteren Rücken.",
                "Hyperextensions": "Stärkt den unteren Rücken. Bewegung nur aus der Hüfte, kein Überstrecken.",
                "Facepulls": "Seil zum Gesicht ziehen, Ellbogen hoch. Perfekt für die hintere Schulter.",
                "Bizeps Curls (SZ)": "SZ-Stange für handgelenkschonendes Training. Ellbogen bleiben fest an den Rippen.",
                "Hammer Curls": "Daumen zeigen nach oben. Trainiert den Brachialis (Dicke des Oberarms).",
                "Konzentrations-Curls": "Im Sitzen, Ellbogen am Innenschenkel fixiert. Kein Abfälschen möglich."
            }
            st.info(guides_r[kat_ruecken])

        with tab3:
            # --- BEINE & CORE ---
            kat_beine = st.selectbox("Übung wählen (Beine/Core):", [
                "Kniebeugen", "Beinpresse", "Ausfallschritte", "Beinstrecker", "Beinbeuger (Liegend)",
                "Wadenheben", "Plank (Unterarmstütz)", "Crunches", "Beinheben", "Russian Twist"
            ])
            guides_be = {
                "Kniebeugen": "Hüfte nach hinten, Rücken gerade. Knie bleiben stabil über den Füßen.",
                "Beinpresse": "Füße schulterbreit. Knie nicht komplett durchdrücken am Ende.",
                "Ausfallschritte": "Großer Schritt nach vorn, hinteres Knie geht Richtung Boden. Oberkörper aufrecht.",
                "Beinstrecker": "Fokus auf den Quadrizeps. Oben kurz halten für maximale Kontraktion.",
                "Beinbeuger (Liegend)": "Fersen Richtung Gesäß ziehen. Hüfte bleibt auf der Polsterung.",
                "Wadenheben": "Über den gesamten Bewegungsumfang gehen (tief dehnen, hoch drücken).",
                "Plank (Unterarmstütz)": "Körper bildet eine gerade Linie. Po nicht zu hoch, Bauch maximal anspannen.",
                "Crunches": "Nur den oberen Rücken vom Boden abheben. Blick zur Decke.",
                "Beinheben": "Rücken bleibt flach am Boden. Beine gestreckt langsam senken und heben.",
                "Russian Twist": "Im Sitzen Beine abheben und Oberkörper rotieren. Optional mit Gewicht."
            }
            st.info(guides_be[kat_beine])

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



