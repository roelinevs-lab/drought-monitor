import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import json

# --- CONFIGURATION ---
SHEET_NAME = 'drought_monitor_db'
# We remove the hardcoded JSON filename reference here

# --- PAGE SETUP ---
st.set_page_config(page_title="Drought Monitor (Cloud)", page_icon="🌤️")
st.title("🌤️ Drought Monitor: Live from Cloud")

# --- FUNCTION TO LOAD DATA ---
@st.cache_data(ttl=60)
def load_data():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # LOGIC: Check where the key is
        # Option A: We are on Streamlit Cloud (Use Secrets)
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        
        # Option B: We are on Local Laptop (Use File)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('google_key.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- MAIN APP ---
df = load_data()

if not df.empty:
    latest = df.iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Temp", f"{latest['temp_avg_c']} °C")
    col2.metric("Latest Humidity", f"{latest['humidity']} %")
    col3.metric("Rainfall", f"{latest['precip_rate_mm']} mm")

    st.subheader("Cloud Data History")
    st.line_chart(df.set_index('Date')[['temp_avg_c', 'humidity']])
    
    time.sleep(60)
    st.rerun()
else:
    st.write("Waiting for data...")