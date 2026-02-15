import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- SEITEN-SETUP ---
st.set_page_config(page_title="Iron Hub", page_icon="🦾", layout="wide")

# --- VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl="1s") # Wir erzwingen frische Daten beim Laden

def save_entry(new_row_dict):
    try:
        existing_data = conn.read(ttl="1s")
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False

def get_kreatin_streak(df):
    if df.empty:
        return 0
    
    # Nur Kreatin-Einträge filtern und Duplikate pro Tag entfernen
    kreatin_dates = pd.to_datetime(df[df['Typ'] == 'Kreatin']['Datum']).dt.date.unique()
    kreatin_dates = sorted(kreatin_dates, reverse=True)
    
    if not kreatin_dates:
        return 0
    
    streak = 0
    today = date.today()
    check_date = today
    
    # Falls heute noch nichts geloggt wurde, prüfen wir ab gestern
    if kreatin_dates[0] < today:
        check_date = today - pd.Timedelta(days=1)
        # Wenn auch gestern nichts war -> Streak gerissen (außer man hat heute noch Zeit)
        if kreatin_dates[0] < check_date:
            return 0

    # Rückwärts zählen
    for d in kreatin_dates:
        if d == check_date:
            streak += 1
            check_date -= pd.Timedelta(days=1)
        elif d < check_date:
            break # Lücke gefunden
            
    return streak

# --- DESIGN (MacroFactory Dark) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    div[data-testid="stMetricValue"] { color: #007AFF; }
    .stButton>button {
        border-radius: 15px; background: linear-gradient(135deg, #007AFF 0%, #0051AF 100%);
        color: white; font-weight: bold; height: 3.5em; width: 100%; border: none;
    }
    input { background-color: #252525 !important; color: white !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATEN LADEN ---
data = load_data()

# Logik für Dashboard-Werte
if not data.empty:
    weights = data[data['Typ'] == 'Gewicht']
    last_weight = float(weights['Gewicht'].iloc[-1]) if not weights.empty else 0.0
    prev_weight = float(weights['Gewicht'].iloc[-2]) if len(weights) > 1 else last_weight
    
    trainings = data[data['Typ'] == 'Training']
    last_workout = trainings['Übung/Info'].iloc[-1] if not trainings.empty else "Kein Training"
else:
    last_weight, prev_weight, last_workout = 0.0, 0.0, "Kein Training"

# --- UI: DASHBOARD ---
st.title("🦾 Iron Hub")
m1, m2, m3 = st.columns(3)
# Vor der Dashboard-Anzeige die Streak berechnen
streak_count = get_kreatin_streak(data)

with m1:
    # Wir zeigen die Flamme und die Anzahl der Tage
    st.metric("Kreatin-Streak", f"{streak_count} Tage", f"{'🔥' if streak_count > 0 else '❄️'}")
with m2: 
    diff = last_weight - prev_weight
    st.metric("Gewicht", f"{last_weight} kg", delta=f"{diff:.1f} kg", delta_color="inverse")
with m3: st.metric("PUMP", last_workout, "🔥")

st.write("##")

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("### 🍎 Kreatin einnahme")
        
        # KREATIN LOGIK
        if st.button("💊 Kreatin eingenommen"):
            if save_entry({"Datum": str(date.today()), "Typ": "Kreatin", "Übung/Info": "5g", "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0}):
                st.balloons() # Animation starten
                st.toast("Sauber! Kreatin ist drin.", icon="✅")
                time.sleep(2) # WARTEN, damit die Ballons fliegen können
                st.rerun()

        st.write("---")
        
        # GEWICHT LOGIK
        new_w = st.number_input("Gewicht (kg)", value=last_weight if last_weight > 0 else 80.0, step=0.1)
        if st.button("⚖️ Gewicht speichern"):
            if save_entry({"Datum": str(date.today()), "Typ": "Gewicht", "Übung/Info": "Körpergewicht", "Gewicht": new_w, "Sätze": 0, "Wiederholungen": 0}):
                if new_w < last_weight:
                    st.snow() # Effekt bei Abnahme
                    st.toast("Wahnsinn! Abgenommen ❤️", icon="❤️")
                else:
                    st.toast("Gewicht wurde gespeichert!", icon="⚖️")
                time.sleep(2)
                st.rerun()

with col_right:
    with st.container(border=True):
        st.markdown("### 🏋️‍♂️ Workout Log")
        u_name = st.text_input("Übung", placeholder="z.B. Bankdrücken")
        c1, c2, c3 = st.columns(3)
        u_kg = c1.number_input("kg", step=2.5)
        u_s = c2.number_input("Sätze", step=1)
        u_r = c3.number_input("Reps", step=1)

        if st.button("🚀 Satz speichern"):
            if u_name:
                if save_entry({"Datum": str(date.today()), "Typ": "Training", "Übung/Info": u_name, "Gewicht": u_kg, "Sätze": u_s, "Wiederholungen": u_r}):
                    st.toast("BOOM! ⚡", icon="⚡") # Blitz im Toast
                    st.success("Training gespeichert! ⚡")
                    time.sleep(1.5)
                    st.rerun()

import plotly.express as px # Stelle sicher, dass dies oben bei den Imports steht!

# --- 8. GRAFISCHE AUSWERTUNG ---
st.write("##")
with st.container(border=True):
    st.markdown("### 📈 Gewichtsverlauf & Ziel")
    
    # --- DEIN ZIEL HIER EINTRAGEN ---
    ziel_gewicht = 100.0 # Ändere diese Zahl auf dein persönliches Ziel
    # --------------------------------
    
    try:
        if not data.empty:
            df_weight = data[data['Typ'] == 'Gewicht'].copy()
            
            if not df_weight.empty:
                df_weight['Datum'] = pd.to_datetime(df_weight['Datum'])
                df_weight = df_weight.sort_values('Datum')
                
                # Plotly Diagramm erstellen
                fig = px.line(
                    df_weight, 
                    x='Datum', 
                    y='Gewicht',
                    markers=True,
                    template="plotly_dark",
                    color_discrete_sequence=['#007AFF']
                )
                
                # --- HIER KOMMT DIE ZIEL-LINIE ---
                fig.add_hline(
                    y=ziel_gewicht, 
                    line_dash="dash", 
                    line_color="#FF4B4B", # Ein motivierendes Rot/Orange
                    annotation_text=f"Ziel: {ziel_gewicht}kg", 
                    annotation_position="bottom right"
                )
                
                # Achsen-Optimierung (Zoom)
                # Wir berechnen den Bereich, damit die Ziel-Linie immer sichtbar ist
                all_weights = df_weight['Gewicht'].tolist() + [ziel_gewicht]
                y_min = min(all_weights) - 2
                y_max = max(all_weights) + 2
                
                fig.update_yaxes(range=[y_min, y_max], fixedrange=False)
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=350,
                    xaxis_title=None,
                    yaxis_title="kg"
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Noch keine Gewichtsdaten vorhanden.")
        else:
            st.info("Sammle Daten für deine Kurve!")
    except Exception as e:
        st.error(f"Diagramm-Fehler: {e}")
