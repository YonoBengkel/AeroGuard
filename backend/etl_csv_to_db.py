import pandas as pd
from app import app, db, WilayahDetails, DataHistoris
import os
from datetime import datetime

def jalankan_etl_historis():
    # 1. EXTRACT: Cari dan baca file CSV di folder utama
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset_polutan_jatim.csv')
    
    if not os.path.exists(csv_path):
        print(f"File tidak ditemukan di: {csv_path}")
        return

    print("Membaca data dari CSV (Extract)...")
    df = pd.read_csv(csv_path)
    print(f"Total baris data mentah: {len(df)}")

    with app.app_context():
        # 2. TRANSFORM: Buat kamus (dictionary) untuk mengubah Nama Kota menjadi ID Wilayah
        daftar_wilayah = WilayahDetails.query.all()
        kamus_wilayah = {w.nama_wilayah: w.id_wilayah for w in daftar_wilayah}
        
        # Cek apakah tabel data_historis masih kosong
        jumlah_data_sekarang = DataHistoris.query.count()
        if jumlah_data_sekarang > 0:
            print(f"Tabel data_historis sudah berisi {jumlah_data_sekarang} baris. Proses dibatalkan untuk mencegah duplikasi data ganda.")
            return

        print("Mulai mencocokkan data dan ID Wilayah (Transform)...")
        data_siap_load = []
        
        for index, row in df.iterrows():
            nama_kota_di_csv = row['Kota']
            
            # Cek apakah kota ada di database kita
            if nama_kota_di_csv in kamus_wilayah:
                id_wilayah_db = kamus_wilayah[nama_kota_di_csv]
                
                # Konversi waktu dari string ke format datetime
                waktu_aktual_dt = datetime.strptime(row['Waktu'], "%Y-%m-%d %H:%M:%S")
                
                # Bungkus ke dalam format Object SQLAlchemy
                data_baru = DataHistoris(
                    id_wilayah=id_wilayah_db,
                    waktu_aktual=waktu_aktual_dt,
                    pm25=row['PM2.5 (µg/m³)'],
                    pm10=row['PM10 (µg/m³)'],
                    so2=row['SO2 (µg/m³)'],
                    co=row['CO (µg/m³)'],
                    no2=row['NO2 (µg/m³)'],
                    ozon=row['Ozon (µg/m³)']
                )
                data_siap_load.append(data_baru)

        # 3. LOAD: Masukkan semua data ke Supabase menggunakan metode Bulk (Massal)
        print(f"Memompa {len(data_siap_load)} baris ke Supabase (Load). Tunggu sebentar...")
        db.session.bulk_save_objects(data_siap_load)
        db.session.commit()
        
        print("✅ Proses ETL Selesai! Seluruh data historis berhasil diamankan di Supabase.")

if __name__ == '__main__':
    jalankan_etl_historis()