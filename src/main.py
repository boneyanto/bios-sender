import os
import gspread
import requests
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# Config
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_IDS = {
    'penerimaan': '1loDtJGrMCHKrh5kkqF3Wkj6hZJqZGDd5',
    'pengeluaran': '1lsepC97hH0cN6J6_CvU6zleenexq_MVd',
    'saldo_operasional': '1lwgiS1eXtg8XrirQ_4fO91-OjdVVHA4x',
    'saldo_pengelolaan_kas': '1m1prCpKIAEbhGA7Pa98sBzGXt4Zo0sBT',
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
    auth_url = "https://training-bios2.kemenkeu.go.id/api/token"
    payload = {
        "satker": os.getenv('SATKER'),
        "key": os.getenv('API_KEY')
    }
    response = requests.post(auth_url, data=payload)
    return response.json().get('token')

def get_sheet_data(sheet_id, sheet_name):
    try:
        # Debug 1: Cek apakah credentials ada
        raw_creds = os.getenv('GOOGLE_CREDENTIALS')
        if not raw_creds:
            raise Exception("GOOGLE_CREDENTIALS environment variable is empty")
            
        # Debug 2: Cek parsing JSON
        print("Raw Credentials (first 50 chars):", raw_creds[:50] + "...")  # Jangan tampilkan semua
        google_creds = json.loads(raw_creds)
        
        # Debug 3: Cek hasil parsing
        print("Credentials Keys:", google_creds.keys())  # Harus muncul dictionary keys
        
        # ... (kode lanjutan)
    except Exception as e:
        print(f"Error in get_sheet_data: {str(e)}")
        raise

def send_data(endpoint, token, data):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(endpoint, json=data, headers=headers)
    return response.status_code

def main():
    token = get_api_token()
    
    for data_type, sheet_id in SHEET_IDS.items():
        try:
            records = get_sheet_data(sheet_id, 'Sheet1')  # Ganti dengan nama sheet yang sesuai
            endpoint = ENDPOINTS[data_type]
            
            for record in records:
                # Convert date format if needed
                if 'tgl_transaksi' in record:
                    record['tgl_transaksi'] = datetime.strptime(
                        record['tgl_transaksi'], '%d/%m/%Y'
                    ).strftime('%Y-%m-%d')
                
                status = send_data(endpoint, token, record)
                print(f"Sent {data_type} data - Status: {status}")
                
        except Exception as e:
            print(f"Error processing {data_type}: {str(e)}")

if __name__ == "__main__":
    main()
