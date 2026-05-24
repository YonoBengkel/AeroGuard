import pandas as pd
from app import app, db, WilayahDetails
import os

def seed_data_wilayah():
    # Pastikan file CSV ada di folder root (satu tingkat di atas folder backend)
    # Sesuaikan nama file jika berbeda
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wilayah_details_rows.csv')
    
    if not os.path.exists(csv_path):
        print(f"File CSV tidak ditemukan di: {csv_path}")
        return

    print("Membaca file CSV...")
    df_wilayah = pd.read_csv(csv_path)

    with app.app_context():
        # Cek apakah data sudah ada agar tidak duplikat
        jumlah_sekarang = WilayahDetails.query.count()
        if jumlah_sekarang > 0:
            print(f"Tabel sudah berisi {jumlah_sekarang} data. Hapus manual di Supabase jika ingin ulang.")
            return

        print("Memasukkan data ke Supabase...")
        for index, row in df_wilayah.iterrows():
            wilayah_baru = WilayahDetails(
                id_wilayah=row['id_wilayah'],
                nama_wilayah=row['nama_wilayah'],
                latitude=row['latitude'],
                longitude=row['longitude']
            )
            db.session.add(wilayah_baru)
        
        # Simpan perubahan (Load)
        db.session.commit()
        print(f"Berhasil memasukkan {len(df_wilayah)} wilayah ke Supabase!")

if __name__ == '__main__':
    seed_data_wilayah()