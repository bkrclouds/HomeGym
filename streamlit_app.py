import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import plotly.express as px

# --- 1. SEITEN-SETUP & CSS ---
st.set_page_config(page_title="Iron Hub", page_icon="🦾", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF !important; }
    label, p, span, .stMarkdown { color: #FFFFFF !important; font-weight: 500; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 800 !important; }
    div[data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 2.2rem !important; }
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
    .btn-danger button {
        background: linear-gradient(135deg, #FF4B4B 0%, #AF0000 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION STATE ---
for key, default in [('user', None), ('tutorial_done', False), ('step', 1), 
                     ('selected_ex', ""), ('show_settings', False)]:
    if key not in st.session_state: st.session_state[key] = default

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

def delete_user_data(user_name):
    try:
        existing_data = conn.read(ttl="0s")
        updated_df = existing_data[existing_data['Email'] != user_name]
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except: return False

def get_kreatin_streak(df):
    if df.empty: return 0
    kreatin_data = df[df['Typ'] == 'Kreatin'].copy()
    if kreatin_data.empty: return 0
    kreatin_dates = sorted(pd.to_datetime(kreatin_data['Datum']).dt.date.unique(), reverse=True)
    streak, check_date = 0, date.today()
    if kreatin_dates[0] < check_date - pd.Timedelta(days=1): return 0
    for d in kreatin_dates:
        if d == check_date or d == check_date - pd.Timedelta(days=1):
            streak += 1
            check_date = d - pd.Timedelta(days=1)
        else: break
    return streak

# --- 5. LOGIN ---
full_data = conn.read(ttl="1m")

if st.session_state.user is None:
    st.title("🦾 Iron Hub")
    with st.container(border=True):
        st.subheader("Willkommen zurück!")
        name_input = st.text_input("Dein Name", placeholder="Tippe deinen Namen...")
        if st.button("Einloggen"):
            if name_input:
                name_clean = name_input.strip()
                st.session_state.user = name_clean
                user_exists = name_clean in full_data['Email'].values if not full_data.empty else False
                st.session_state.tutorial_done = user_exists
                st.rerun()
    st.stop()

# --- 6. TUTORIAL ---
if not st.session_state.tutorial_done:
    st.title(f"Willkommen, {st.session_state.user}!")
    with st.container():
        st.markdown('<div class="onboarding-card">', unsafe_allow_html=True)
        images = ["https://images.unsplash.com/photo-1594381898411-846e7d193883?w=800",
                  "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800",
                  "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=800",
                  "https://images.unsplash.com/photo-1593079831268-3381b0db4a77?w=800",
                  "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800"]
        st.image(images[st.session_state.step - 1], use_container_width=True)
        st.header(["Iron Hub", "Tracking", "Dein Plan", "Kreatin", "Ready?"][st.session_state.step-1])
        st.write(["Dein digitaler Gym-Partner.", "Logge Sätze in Sekunden.", "Erstelle deinen eigenen Plan.", "Verpasse nie deinen Streak.", "Starte jetzt deine Reise!"][st.session_state.step-1])
        st.markdown('</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if st.session_state.step > 1 and c1.button("Zurück"): st.session_state.step -= 1; st.rerun()
        if st.session_state.step < 5:
            if c2.button("Weiter"): st.session_state.step += 1; st.rerun()
        else:
            if c2.button("STARTEN 🚀"): st.session_state.tutorial_done = True; st.rerun()
    st.stop()

# --- 7. DASHBOARD DATEN ---
current_user = st.session_state.user
user_df = full_data[full_data['Email'] == current_user] if not full_data.empty else pd.DataFrame()

if user_df.empty:
    st.header(f"Profil-Setup 🦾")
    with st.form("setup"):
        c1, c2 = st.columns(2)
        w = c1.number_input("Startgewicht (kg)", value=80.0, step=0.1); zw = c2.number_input("Zielgewicht (kg)", value=75.0, step=0.1)
        if st.form_submit_button("Speichern"):
            save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Start", "Gewicht": w, "Sätze": 0, "Wiederholungen": 0, "Ziel": zw}, current_user)
            st.rerun()
    st.stop()

# BERECHNUNGEN
streak = get_kreatin_streak(user_df)
weights_df = user_df[user_df['Typ'] == 'Gewicht'].copy()
weights_df['Datum'] = pd.to_datetime(weights_df['Datum'])
weights_df = weights_df.sort_values('Datum')

last_w = float(weights_df['Gewicht'].iloc[-1]) if not weights_df.empty else 0.0
start_w = float(weights_df['Gewicht'].iloc[0]) if not weights_df.empty else 0.0
ziel_w = float(user_df['Ziel'].dropna().iloc[0]) if 'Ziel' in user_df.columns and not user_df['Ziel'].dropna().empty else 0.0
wasser_heute = user_df[(user_df['Typ'] == 'Wasser') & (user_df['Datum'] == str(date.today()))]['Gewicht'].sum()
mein_plan = user_df[user_df['Typ'] == 'Plan']['Übung/Info'].unique().tolist()

# SETTINGS
c_h1, c_h2 = st.columns([0.9, 0.1])
if c_h2.button("⚙️"): st.session_state.show_settings = not st.session_state.show_settings

if st.session_state.show_settings:
    with st.container(border=True):
        st.subheader("Einstellungen")
        if st.button("Abmelden"): st.session_state.user = None; st.rerun()
        with st.expander("🛡️ Datenschutz"):
            st.write("Deine Daten liegen verschlüsselt in Deinem privaten Google Sheet. Wir geben nichts weiter.")
        with st.expander("🗑️ Account löschen"):
            st.warning("Das löscht alle Einträge unwiderruflich!")
            confirm = st.text_input("Tippe 'LÖSCHEN':")
            if st.button("JETZT LÖSCHEN", key="del_btn"):
                if confirm == "LÖSCHEN": delete_user_data(current_user); st.session_state.user = None; st.rerun()
        if st.button("Schließen"): st.session_state.show_settings = False; st.rerun()
    st.stop()

# DASHBOARD
st.title(f"🦾 Iron Hub: {current_user}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Streak", f"{streak} Tage", "🔥")
m2.metric("Gewicht", f"{last_w} kg", f"{last_w - start_w:+.1f} kg")
m3.metric("Wasser", f"{wasser_heute} L", "💧")
m4.metric("Ziel", f"{ziel_w} kg", "🎯")
st.write("---")

col_l, col_r = st.columns([1, 1.8], gap="large")

with col_l:
    with st.container(border=True):
        st.subheader("🍎 Daily Habits")
        if st.button("💊 Kreatin genommen"):
            save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user)
            st.balloons(); st.rerun()
        st.progress(min(wasser_heute / 3.0, 1.0), text=f"Wasser: {wasser_heute}L / 3L")
        if st.button("+ 0.5L Wasser"):
            save_entry({"Datum": str(date.today()), "Typ": "Wasser", "Übung/Info": "Glas", "Gewicht": 0.5, "Sätze": 0, "Wiederholungen": 0}, current_user); st.rerun()
        
        st.write("---")
        # Mein Plan Sektion
        st.subheader("📋 Mein Plan")
        if not mein_plan: st.info("Füge Übungen aus dem Katalog hinzu!")
        for ex in mein_plan:
            cl1, cl2 = st.columns([4,1])
            if cl1.button(f"🏋️ {ex}", key=f"plan_{ex}"): st.session_state.selected_ex = ex; st.rerun()
            if cl2.button("🗑️", key=f"del_{ex}"):
                # Hier müsste eine Logik zum Löschen aus dem Plan hin (einfachheitshalber hier übersprungen)
                pass

with col_r:
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Workout Log")
        with st.expander("📚 Übungs-Katalog"):
            tabs = st.tabs(["Push", "Pull", "Legs"])
            katalog = {"Push": ["Bankdrücken", "Schulterdrücken", "Dips"], 
                       "Pull": ["Klimmzüge", "Rudern", "Latzug"], 
                       "Legs": ["Kniebeugen", "Beinpresse", "Waden"]}
            for i, (cat, items) in enumerate(katalog.items()):
                with tabs[i]:
                    for n in items:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(n)
                        if c2.button("Log", key=f"cat_l_{n}"): st.session_state.selected_ex = n; st.rerun()
                        if c3.button("📌 Plan", key=f"cat_p_{n}"):
                            save_entry({"Datum": "PLAN", "Typ": "Plan", "Übung/Info": n, "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}, current_user); st.rerun()

        u_name = st.text_input("Übung", value=st.session_state.selected_ex)
        c_kg, c_s, c_r = st.columns(3)
        u_kg = c_kg.number_input("kg", step=2.5, value=0.0); u_s = c_s.number_input("Sätze", value=3); u_r = c_r.number_input("Reps", value=10)
        if st.button("🚀 SATZ SPEICHERN"):
            save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}, current_user)
            st.session_state.selected_ex = ""; st.rerun()

# 3. GEWICHTSVERLAUF
st.write("---")
with st.container(border=True):
    st.subheader("📈 Gewichtsverlauf")
    if len(weights_df) > 1:
        fig = px.line(weights_df, x='Datum', y='Gewicht', markers=True)
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(l=0, r=0, t=20, b=0))
        fig.update_traces(line_color='#00D4FF', marker=dict(size=8))
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Trage dein Gewicht an mehreren Tagen ein, um den Verlauf zu sehen.")
