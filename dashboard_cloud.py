import streamlit as st
import gspread
import pandas as pd
import json
import os
from google.oauth2 import service_account
import altair as alt

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Drought Monitor",
    page_icon="🌤️",
    layout="wide"
)

# --- CONSTANTS ---
SHEET_NAME = 'drought_monitor_db'

# --- AUTHENTICATION ---
# This function caches the connection so it doesn't reconnect every time you refresh
@st.cache_resource
def connect_to_sheet():
    """Connects to Google Sheets using Streamlit Secrets or Env Vars"""
    try:
        # Try finding the secret in Streamlit's built-in secrets management first
        if "GCP_SERVICE_ACCOUNT" in st.secrets:
            key_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
        # Fallback to os.environ (good for local testing or alternative setups)
        elif "GCP_SERVICE_ACCOUNT" in os.environ:
            key_dict = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
        else:
            st.error("❌ Error: GCP_SERVICE_ACCOUNT secret not found.")
            st.stop()
            
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(key_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.stop()

# --- DATA LOADING ---
def load_data():
    sheet = connect_to_sheet()
    # Get all records
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# --- DASHBOARD UI ---
st.title("🌤️ Real-Time Drought Monitor")
st.markdown("Monitor temperature, wind, and rain levels directly from the Ambient Weather Station.")

# Add a refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Load the data
try:
    df = load_data()

    if not df.empty:
        # Convert timestamp to datetime objects for better plotting
        # Adjust 'Date' column name if it's different in your sheet (e.g. 'Timestamp')
        # We assume the first column is the timestamp based on your update_data.py
        first_col = df.columns[0] 
        df[first_col] = pd.to_datetime(df[first_col])

        # --- METRICS ROW ---
        # Get the latest row of data
        latest = df.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperature", f"{latest.iloc[1]} °C")
        col2.metric("Wind Speed", f"{latest.iloc[2]} km/h")
        col3.metric("Rainfall", f"{latest.iloc[3]} mm")
        col4.metric("Humidity", f"{latest.iloc[4]} %")

        st.divider()

        # --- CHARTS ---
        st.subheader("📈 Trends Over Time")
        
        # Temperature Chart
        chart_temp = alt.Chart(df).mark_line(color='orange').encode(
            x=alt.X(f'{first_col}:T', title='Time'),
            y=alt.Y(df.columns[1], title='Temperature (°C)'),
            tooltip=[first_col, df.columns[1]]
        ).interactive()
        
        st.altair_chart(chart_temp, use_container_width=True)

        # Rain & Wind Chart (Combined or Separate)
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.caption("Rainfall History")
            chart_rain = alt.Chart(df).mark_bar(color='blue').encode(
                x=alt.X(f'{first_col}:T', title='Time'),
                y=alt.Y(df.columns[3], title='Rain (mm)'),
                tooltip=[first_col, df.columns[3]]
            )
            st.altair_chart(chart_rain, use_container_width=True)

        with col_chart2:
            st.caption("Wind Speed History")
            chart_wind = alt.Chart(df).mark_line(color='green').encode(
                x=alt.X(f'{first_col}:T', title='Time'),
                y=alt.Y(df.columns[2], title='Wind (km/h)'),
                tooltip=[first_col, df.columns[2]]
            )
            st.altair_chart(chart_wind, use_container_width=True)

        # --- RAW DATA ---
        with st.expander("View Raw Data"):
            st.dataframe(df.sort_values(by=first_col, ascending=False))

    else:
        st.warning("⚠️ The database is connected, but the sheet is empty.")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")