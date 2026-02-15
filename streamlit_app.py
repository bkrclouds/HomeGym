import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- SEITEN-SETUP ---
st.set_page_config(page_title="My Fitness Hub", page_icon="🏋️‍♂️", layout="centered")

# --- VERBINDUNG ZU GOOGLE SHEETS ---
# Wir erstellen eine Verbindung zur Tabelle
conn = st.connection("gsheets", type=GSheetsConnection)

# Funktion zum Laden der Daten
def load_data():
    return conn.read(ttl="10m") # ttl=0 sorgt dafür, dass wir immer die neuesten Daten sehen

# Funktion zum Speichern eines neuen Eintrags
def save_entry(new_row_dict):
    try:
        # Wir holen die Daten aus dem Cache (schnell!)
        existing_data = load_data()
        
        # Neue Daten anhängen
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row_dict])], ignore_index=True)
        
        # Einmaliger Schreibvorgang zu Google
        conn.update(data=updated_df)
        
        # WICHTIG: Cache löschen, damit die Historie beim nächsten Mal aktuell ist
        st.cache_data.clear()
        
        st.balloons()
        st.success("Erfolgreich im Sheet gespeichert!")
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            st.error("Google braucht kurz Pause (Limit erreicht). Bitte in 1 Minute nochmal probieren!")
        else:
            st.error(f"Fehler: {e}")

# --- UI DESIGN ---
st.title("🏋️‍♂️ My HomeGym")

# --- TAGES-CHECK (Kreatin & Gewicht) ---
st.header("🥤 Kreatin Tracker")
col_crea, col_weight = st.columns(2)

with col_crea:
    if st.button("✅ Kreatin eingenommen", use_container_width=True):
        save_entry({
            "Datum": str(date.today()), 
            "Typ": "Kreatin", 
            "Übung/Info": "5g", 
            "Gewicht": 0, "Sätze": 0, "Wiederholungen": 0
        })
        st.toast("Kreatin geloggt! 💧")

with col_weight:
    weight = st.number_input("Körpergewicht (kg):", min_value=0.0, step=0.1, format="%.1f")
    if st.button("⚖️ Gewicht speichern", use_container_width=True):
        save_entry({
            "Datum": str(date.today()), 
            "Typ": "Gewicht", 
            "Übung/Info": "Körpergewicht", 
            "Gewicht": weight, "Sätze": 0, "Wiederholungen": 0
        })
        st.success(f"{weight} kg gespeichert!")

st.divider()

# --- WORKOUT LOG ---
st.header("📝 Training")
exercise = st.text_input("Name der Übung", placeholder="z.B. Bankdrücken")

c1, c2, c3 = st.columns(3)
with c1:
    w = st.number_input("Gewicht (kg)", min_value=0.0, step=0.5)
with c2:
    s = st.number_input("Sätze", min_value=0, step=1)
with c3:
    r = st.number_input("Wiederholungen", min_value=0, step=1)

if st.button("🚀 Satz speichern", use_container_width=True):
    if exercise:
        save_entry({
            "Datum": str(date.today()), 
            "Typ": "Training", 
            "Übung/Info": exercise, 
            "Gewicht": w, "Sätze": s, "Wiederholungen": r
        })
        st.balloons()
        st.success(f"{exercise} hinzugefügt!")
    else:
        st.warning("Bitte Übungsnamen angeben.")

st.divider()

# --- HISTORIE & ANALYSE ---
st.header("📈 Deine Historie")
data = load_data()

if not data.empty:
    # Tabellarische Ansicht (Neueste zuerst)
    st.dataframe(data.sort_values(by="Datum", ascending=False), use_container_width=True)
    
    # Gewichtsverlauf Chart
    weight_df = data[data["Typ"] == "Gewicht"].copy()
    if not weight_df.empty:
        st.subheader("Gewichtsverlauf")
        weight_df["Datum"] = pd.to_datetime(weight_df["Datum"])
        st.line_chart(weight_df.set_index("Datum")["Gewicht"])
else:
    st.info("Noch keine Daten vorhanden. Fang an zu trainieren!")









