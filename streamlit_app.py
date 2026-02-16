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

# In der save_entry Funktion:
new_row_dict["Email"] = current_user # Füge dies hinzu

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
    kreatin_dates = pd.to_datetime(df[df['Typ'] == 'Kreatin']['Datum']).dt.date.unique()
    kreatin_dates = sorted(kreatin_dates, reverse=True)
    if not kreatin_dates: return 0
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

# --- 4. 🍔 SIDEBAR (BURGER MENÜ) ---
with st.sidebar:
    st.title("🍔 Menü")
    st.markdown("### ⚙️ Einstellungen")
    ziel_gewicht = st.number_input("Zielgewicht (kg)", value=100.0, step=0.1, format="%.1f")
    st.write("---")
    st.warning("⚠️ Gefahrenzone")
    if st.button("🗑️ Letzten Eintrag löschen"):
        if delete_last_entry():
            st.success("Gelöscht!")
            time.sleep(1.5)
            # --- NEU: ONBOARDING & LOGIN LOGIK ---
# Wir prüfen, wer eingeloggt ist (In der Streamlit Cloud ist das st.experimental_user.email oder ein Selektor)
# Für den Anfang nutzen wir einen einfachen Selektor in der Sidebar:
with st.sidebar:
    current_user = st.selectbox("👤 Nutzer wechseln", ["Bitte wählen...", "Mein Name", "Frau", "Bruder"])

# Falls kein Nutzer gewählt ist oder der Nutzer neu ist:
if current_user == "Bitte wählen...":
    st.warning("Willkommen im Iron Hub! Bitte wähle dein Profil aus.")
    st.stop() # Hält die App hier an, bis ein Nutzer gewählt wird

# Prüfen, ob der Nutzer schon Daten hat
user_data = data[data['Email'] == current_user] if 'Email' in data.columns else pd.DataFrame()

if user_data.empty:
    st.balloons()
    st.header(f"Willkommen, {current_user}! 🦾")
    st.subheader("Lass uns dein Profil einrichten:")
    
    with st.form("onboarding_form"):
        start_weight = st.number_input("Dein aktuelles Startgewicht (kg)", min_value=30.0, max_value=250.0, value=80.0)
        user_goal = st.selectbox("Dein Ziel", ["Muskelaufbau", "Fettabbau", "Kraftsteigern"])
        
        if st.form_submit_button("Profil speichern & Starten"):
            # Speichere den ersten Eintrag als "Profil-Marker"
            onboarding_entry = {
                "Datum": str(date.today()), 
                "Typ": "Gewicht", 
                "Email": current_user,  # Wir nutzen hier den Namen als ID
                "Übung/Info": f"Profil-Setup: {user_goal}", 
                "Gewicht": start_weight, 
                "Sätze": 0, 
                "Wiederholungen": 0
            }
            if save_entry(onboarding_entry):
                st.success("Profil erstellt! Viel Erfolg beim Training.")
                time.sleep(1)
                st.rerun()
    st.stop() # Zeigt den Rest der App erst nach dem Setup

# Filter die Daten für den Rest der App, damit man nur seine eigenen sieht
data = data[data['Email'] == current_user]

# --- 5. DESIGN ---
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

# --- 6. DATEN & LOGIK ---
data = load_data()
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

# --- 7. DASHBOARD ---
st.title("🦾 Iron Hub")
m1, m2, m3 = st.columns(3)
with m1: st.metric("Kreatin-Streak", f"{streak_count} Tage", "🔥" if streak_count > 0 else "❄️")
with m2: st.metric("Gewicht", f"{last_weight} kg", delta=f"{last_weight - ziel_gewicht:.1f} kg zum Ziel", delta_color="inverse")
with m3: st.metric("PUMP", last_workout, "🔥")

# --- 8. HAUPTBEREICH ---
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
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        u_name = st.text_input("Übung", value=st.session_state.selected_exercise, placeholder="Name eingeben oder unten wählen")
        c1, c2, c3 = st.columns(3)
        u_kg, u_s, u_r = c1.number_input("kg", step=2.5), c2.number_input("Sätze", step=1), c3.number_input("Reps", step=1)
        if st.button("🚀 Satz speichern"):
            if u_name and save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}):
                st.toast("BOOM! ⚡")
                st.session_state.selected_exercise = ""
                time.sleep(1.5)
                st.rerun()

    # --- ÜBUNGS-GUIDE ---
    st.write("##")
    with st.expander("📚 Übungskatalog (Klick zum Übernehmen)", expanded=False):
        t1, t2, t3 = st.tabs(["Brust & Schultern", "Rücken & Bizeps", "Beine & Core"])
        
        def render_guide(category_dict, key_suffix):
            selected = st.selectbox("Übung wählen:", ["Bitte wählen..."] + list(category_dict.keys()), key=f"sb_{key_suffix}")
            if selected != "Bitte wählen...":
                st.info(category_dict[selected])
                if st.button(f"✅ {selected} übernehmen", key=f"btn_{key_suffix}"):
                    st.session_state.selected_exercise = selected
                    st.rerun()

        with t1:
            render_guide({
                "Bankdrücken (LH)": "Stange zur Brust führen, Ellbogen leicht einrücken, Füße fest am Boden.",
                "Schrägbankdrücken": "30-45 Grad Steigung für die obere Brustmuskulatur.",
                "Flyes (KH)": "Dehnung der Brust, Arme fast gestreckt wie bei einer Umarmung führen.",
                "Dips": "Oberkörper leicht nach vorn für Brustfokus, aufrecht für Trizeps.",
                "Liegestütze": "Körperspannung halten, Hände unter den Schultern platzieren.",
                "Schulterdrücken (KH)": "Hanteln senkrecht nach oben führen, Core fest anspannen.",
                "Seitheben": "Arme seitlich heben bis Schulterhöhe, kleine Finger leicht nach oben.",
                "Frontheben": "Gewicht kontrolliert vor dem Körper auf Augenhöhe heben.",
                "Butterfly": "Konstante Spannung, Hände auf Brusthöhe zusammenführen.",
                "Military Press": "Langhantel stehend über Kopf drücken, kein Hohlkreuz machen."
            }, "brust")

        with t2:
            render_guide({
                "Klimmzüge": "Brust zur Stange ziehen, Schulterblätter aktiv nach unten.",
                "Latzug (Breit)": "Stange zur oberen Brust ziehen, Ellbogen nach unten führen.",
                "Rudern (LH)": "Oberkörper parallel zum Boden, Stange zum Bauchnabel ziehen.",
                "Einarmiges Rudern": "Rücken gerade, Hantel kontrolliert zur Hüfte ziehen.",
                "Kreuzheben": "Kraft aus den Beinen, Rücken wie ein Brett gespannt halten.",
                "Facepulls": "Seil zum Gesicht ziehen, Ellbogen bleiben hoch.",
                "Bizeps Curls (SZ)": "Stabile Haltung, Ellbogen fest an den Rippen fixieren.",
                "Hammer Curls": "Daumen nach oben, trainiert Oberarm-Dicke und Unterarm.",
                "Konzentrations-Curls": "Im Sitzen, Ellbogen am Innenschenkel für Isolation.",
                "Hyperextensions": "Bewegung aus der Hüfte, unteren Rücken kontrolliert stärken."
            }, "ruecken")

        with t3:
            render_guide({
                "Kniebeugen": "Gewicht auf Fersen, Rücken gerade, tief gehen wie beim Hinsetzen.",
                "Beinpresse": "Füße schulterbreit, Knie am Ende nicht komplett durchstrecken.",
                "Ausfallschritte": "Großer Schritt, hinteres Knie geht fast zum Boden.",
                "Beinstrecker": "Fokus auf Quadrizeps, oben kurz die Spannung halten.",
                "Beinbeuger": "Fersen zum Po ziehen, Hüfte bleibt fest auf der Bank.",
                "Wadenheben": "Über den vollen Bewegungsumfang gehen, oben kurz halten.",
                "Plank": "Körper wie ein Brett anspannen, Po nicht zu hoch nehmen.",
                "Crunches": "Oberen Rücken leicht anheben, Blick schräg nach oben.",
                "Beinheben": "Unteren Rücken fest am Boden halten, Beine gestreckt heben.",
                "Russian Twist": "Beine abheben, Oberkörper rotieren, Bauch fest anspannen."
            }, "beine")

# --- 9. DIAGRAMM ---
st.write("##")
with st.container(border=True):
    st.markdown("### 📈 Gewichtsverlauf")
    if not data.empty and not data[data['Typ'] == 'Gewicht'].empty:
        df_p = data[data['Typ'] == 'Gewicht'].copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        df_p = df_p.sort_values('Datum')
        fig = px.line(df_p, x='Datum', y='Gewicht', markers=True, template="plotly_dark", color_discrete_sequence=['#007AFF'])
        fig.add_hline(y=ziel_gewicht, line_dash="dash", line_color="#FF4B4B", annotation_text="Ziel")
        all_w = df_p['Gewicht'].tolist() + [ziel_gewicht]
        fig.update_yaxes(range=[min(all_w)-2, max(all_w)+2])
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        st.plotly_chart(fig, use_container_width=True)

# --- 10. HISTORIE ---
with st.expander("📂 Alle Einträge"):
    if not data.empty:
        st.dataframe(data.sort_values("Datum", ascending=False), use_container_width=True)

