import os
import gspread
import json
import requests
from datetime import datetime
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configurations
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_IDS = {
    'penerimaan': '1loDtJGrMCHKrh5kkqF3Wkj6hZJqZGDd5',
    'pengeluaran': '1lsepC97hH0cN6J6_CvU6zleenexq_MVd',
    'saldo_operasional': '1lwgiS1eXtg8XrirQ_4fO91-OjdVVHA4x',
    'saldo_pengelolaan_kas': '1IItvpcxH14GLCO1tIGVz0plA8dHe5vqd0_Z4jMxNV80',
    'saldo_dana_kelolaan': '1m52DWPAR1icWNJ4xbwP2NCG5dy6HoXbY'
}

ENDPOINTS = {
    'penerimaan': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/akuntansi/penerimaan',
    'pengeluaran': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/akuntansi/pengeluaran',
    'saldo_operasional': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/saldo/saldo_operasional',
    'saldo_pengelolaan_kas': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/saldo/saldo_pengelolaan_kas',
    'saldo_dana_kelolaan': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/saldo/saldo_dana_kelolaan'
}

def get_api_token():
    """Get API authentication token"""
    try:
        auth_url = "https://training-bios2.kemenkeu.go.id/api/token"
        payload = {
            "satker": os.getenv('SATKER'),
            "key": os.getenv('API_KEY')
        }
        response = requests.post(auth_url, data=payload)
        response.raise_for_status()
        return response.json().get('token')
    except Exception as e:
        print(f"Error getting API token: {str(e)}")
        return None

def get_sheet_data(sheet_id, sheet_name='Sheet1'):
    """Get data from Google Sheets"""
    try:
        # Parse credentials
        raw_creds = os.getenv('GOOGLE_CREDENTIALS')
        if not raw_creds:
            raise ValueError("GOOGLE_CREDENTIALS environment variable is empty")
            
        google_creds = json.loads(raw_creds)
        creds = Credentials.from_service_account_info(google_creds, scopes=SCOPES)
        
        # Access spreadsheet
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        
        # Access worksheet
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Worksheet '{sheet_name}' not found in sheet {sheet_id}")
            return []
            
        # Get records
        records = worksheet.get_all_records()
        if not records:
            print(f"No data found in sheet {sheet_id}/{sheet_name}")
            return []
            
        return records
        
    except Exception as e:
        print(f"Error getting sheet data: {str(e)}")
        return []

def send_data(endpoint, token, data):
    """Send data to API endpoint"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Convert date format
        if 'tgl_transaksi' in data:
            data['tgl_transaksi'] = datetime.strptime(
                data['tgl_transaksi'], '%d/%m/%Y'
            ).strftime('%Y-%m-%d')
            
        # Convert numeric fields
        numeric_fields = ['jumlah', 'saldo_akhir', 'nilai_deposito', 'nilai_bunga']
        for field in numeric_fields:
            if field in data:
                data[field] = float(data[field])
        
        response = requests.post(endpoint, json=data, headers=headers)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.text}")
        return e.response.status_code
    except Exception as e:
        print(f"Error sending data: {str(e)}")
        return 500

def main():
    """Main function"""
    print("Starting data sync...")
    
    # Get API token
    token = get_api_token()
    if not token:
        print("Failed to get API token. Exiting.")
        return
        
    print("Successfully obtained API token")
    
    # Process each data type
    for data_type, sheet_id in SHEET_IDS.items():
        try:
            print(f"\nProcessing {data_type}...")
            
            # Get data from sheet
            records = get_sheet_data(sheet_id)
            print(f"Found {len(records)} records")
            
            if not records:
                continue
                
            endpoint = ENDPOINTS[data_type]
            
            # Send each record
            for idx, record in enumerate(records, 1):
                print(f"Sending record {idx}/{len(records)}")
                status = send_data(endpoint, token, record)
                print(f"Status: {status}")
                
        except Exception as e:
            print(f"Error processing {data_type}: {str(e)}")
            continue
            
    print("\nData sync completed!")

if __name__ == "__main__":
    main()
