import gspread
import os
import json
from google.oauth2 import service_account
import requests
from datetime import datetime
import sys

# --- CONFIGURATION ---
SHEET_NAME = 'drought_monitor_db'

# YOUR AMBIENT WEATHER KEYS
API_KEY = '09ce6326726b4bdf95ed561e59978fa7dab77c2b56f14c1f86df3a10b28ccb15'
APP_KEY = '202fcdf535334859ac5f7abdb294fa19c91c744d7c464a38ab009b582d9762a0'
BASE_URL = "https://api.ambientweather.net/v1/devices"

def connect_to_sheet():
    """Connects to Google Sheets using the GitHub Secret"""
    try:
        # Load credentials from the Environment Variable
        key_dict = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(key_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except KeyError:
        print("❌ Error: GCP_SERVICE_ACCOUNT secret not found in environment variables.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

def get_live_weather():
    """Fetches data from Ambient Weather Station"""
    try:
        url = f"{BASE_URL}?apiKey={API_KEY}&applicationKey={APP_KEY}&limit=1"
        response = requests.get(url)
        data = response.json()
        
        if not data: return None
        
        station = data[0]['lastData']
        
        # Conversions
        temp_c = round((station.get('tempf', 0) - 32) * 5/9, 2)
        wind_kmh = round(station.get('windspeedmph', 0) * 1.609, 2)
        rain_mm = round(station.get('hourlyrainin', 0) * 25.4, 2)
        humidity = station.get('humidity', 0)
        
        return [temp_c, wind_kmh, rain_mm, humidity]
        
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

def update_once():
    print("☁️  Running Cloud Update...")
    
    try:
        # 1. Get Weather Data
        weather = get_live_weather()
        
        if weather:
            # 2. Add Timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row_to_add = [current_time] + weather 
            
            # 3. Send to Google Sheets
            sheet = connect_to_sheet()
            sheet.append_row(row_to_add)
            
            print(f"[{current_time}] 🚀 Success! Uploaded: {weather[0]}°C to Cloud.")
        else:
            print("⚠️ No weather data received.")
            
    except Exception as e:
        print(f"⚠️ Error during update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_once()