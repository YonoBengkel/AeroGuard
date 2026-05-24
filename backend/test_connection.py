import os
from dotenv import load_dotenv
from supabase import create_client, Client
import mlflow

# Membaca variabel rahasia dari file .env
load_dotenv()

print("--- Mengecek Infrastruktur AeroGuard ---")

# 1. Uji Koneksi Supabase
try:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    # Mencoba mengambil data dari tabel yang kosong tidak akan error
    # selama koneksinya berhasil.
    cek_tabel = supabase.table("wilayah_details").select("*").limit(1).execute()
    print("✅ Supabase Berhasil Terhubung!")
except Exception as e:
    print(f"❌ Supabase Gagal: {e}")

# 2. Uji Koneksi MLflow (DagsHub)
try:
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
    mlflow.set_tracking_uri(mlflow_uri)
    
    # Mengambil daftar eksperimen di DagsHub
    experiments = mlflow.search_experiments()
    print("✅ MLflow (DagsHub) Berhasil Terhubung!")
except Exception as e:
    print(f"❌ MLflow Gagal: {e}")