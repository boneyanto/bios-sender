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
    'penerimaan': '1ayQ5Y2-NwlCBYFZjsEFJvi67zbubmUdqMtOeDfC-E7U',
    'pengeluaran': '1H0aR41ZGtFE1WSCyObTqbUDzsB6NKAg--PUw0577fK8',
    'saldo_operasional': '1_lm0MA9F68SEIXA8s4XfsGVWiF-Cja3EymEd4ou4PlE',
    'saldo_pengelolaan_kas': '1IItvpcxH14GLCO1tIGVz0plA8dHe5vqd0_Z4jMxNV80',
    'saldo_dana_kelolaan': '1BHSukPx8K-PljTnhxxkfoGAp4RQmZbrhiv66hyGzp_g',
    'jumlah_dosen': '11wNwBoBClTfjtooUs8Ngx0qWdu1IRVfwB4beiyEXb7Q',
    'jumlah_tendik': '1ljT3L7eZjgI8LFnC6C_KpK2_QRSYRxhFCfPEsofnqkI'
}

ENDPOINTS = {
    'penerimaan': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/akuntansi/penerimaan',
    'pengeluaran': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/akuntansi/pengeluaran',
    'saldo_operasional': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/saldo/saldo_operasional',
    'saldo_pengelolaan_kas': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/saldo/saldo_pengelolaan_kas',
    'saldo_dana_kelolaan': 'https://training-bios2.kemenkeu.go.id/api/ws/keuangan/saldo/saldo_dana_kelolaan',
    'jumlah_dosen': 'https://training-bios2.kemenkeu.go.id/api/ws/pendidikan/sdm/jumlah_tenaga_pendidik_ptn',
    'jumlah_tendik': 'https://training-bios2.kemenkeu.go.id/api/ws/pendidikan/sdm/jumlah_tenaga_kependidikan'
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
    """Send data to API endpoint and return status + error message"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Validasi tanggal transaksi
        if 'tgl_transaksi' in data:
            # Konversi format tanggal
            input_date = datetime.strptime(data['tgl_transaksi'], '%d/%m/%Y')
            today_date = datetime.today()
            
            # Cek apakah tanggal melebihi hari ini
            if input_date > today_date:
                error_msg = f"ERROR: Tanggal transaksi {data['tgl_transaksi']} melebihi hari ini"
                print(error_msg)
                return False, error_msg  # Return status gagal
            
            data['tgl_transaksi'] = input_date.strftime('%Y-%m-%d')
            
        # Konversi field numerik
        numeric_fields = ['jumlah', 'saldo_akhir', 'nilai_deposito', 'nilai_bunga', 'professor_pns', 'professor_non_pns', 'lektor_kepala_pns', 'lektor_kepala_non_pns', 'lektor_pns', 'lektor_non_pns', 'asisten_ahli_pns', 'asisten_ahli_non_pns', 'tenaga_pengajar_pns', 'tenaga_pengajar_non_pns', 'terkualifikasi_s3', 'pegawai_pppk', 'pns', 'non_pns']
        
        for field in numeric_fields:
            if field in data:
                # Handle nilai kosong
                if data[field] in ['', None]:
                    data[field] = 0.0
                try:
                    data[field] = float(data[field])
                except Exception as e:
                    error_msg = f"ERROR: Gagal konversi {field} ke angka: {str(e)}"
                    print(error_msg)
                    return False, error_msg  # Return status gagal
        
        # Debug: Tampilkan data yang akan dikirim
        print(f"\n📤 Mengirim data ke {endpoint}:")
        print(json.dumps(data, indent=2))
        
        # Kirim data
        response = requests.post(endpoint, json=data, headers=headers)
        response.raise_for_status()
        
        # Cek respons API
        api_response = response.json()
        if api_response.get('status') != 'MSG20001':  # Sesuaikan dengan kode sukses API
            error_msg = f"ERROR API: {api_response.get('message')}"
            print(error_msg)
            return False, error_msg
        
        return True, "Sukses"  # Return status sukses
        
    except Exception as e:
        error_msg = f"ERROR: Gagal mengirim data - {str(e)}"
        print(error_msg)
        return False, error_msg  # Return status gagal

def main():
    """Main function dengan error handling"""
    print("Memulai sinkronisasi data...")
    
    # Dapatkan token API
    token = get_api_token()
    if not token:
        print("Gagal mendapatkan token API. Keluar.")
        return
    
    # Proses setiap tipe data
    for data_type, sheet_id in SHEET_IDS.items():
        try:
            print(f"\n🔍 Memproses {data_type}...")
            
            # Ambil data dari Google Sheet
            records = get_sheet_data(sheet_id)
            if not records:
                print("❌ Tidak ada data yang ditemukan")
                continue
                
            print(f"📊 Ditemukan {len(records)} record")
            
            endpoint = ENDPOINTS[data_type]
            success_count = 0
            
            # Kirim data per record
            for idx, record in enumerate(records, 1):
                print(f"\n📨 Record {idx}/{len(records)}")
                success, message = send_data(endpoint, token, record)
                
                if not success:
                    print(f"❌ Gagal mengirim record {idx}. Proses dihentikan!")
                    print(f"💡 Pesan error: {message}")
                    print(f"💾 Record terakhir yang gagal: {json.dumps(record, indent=2)}")
                    break  # Hentikan proses untuk tipe data ini
                
                success_count += 1
                print(f"✅ Berhasil mengirim record {idx}")
            
            print(f"\n📊 Ringkasan {data_type}:")
            print(f"Total sukses: {success_count}/{len(records)}")
            
        except Exception as e:
            print(f"❌ Error fatal: {str(e)}")
            break  # Hentikan seluruh proses

    print("\nSinkronisasi selesai!")

if __name__ == "__main__":
    main()
