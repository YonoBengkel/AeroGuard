import os
import pandas as pd
from datetime import datetime, timedelta
import joblib
import pytz
import mlflow
from app import app, db, DataHistoris, Predictions, WilayahDetails, ModelRegistry
from ispu_logic import kalkulasi_ispu_final, siapkan_fitur_prediksi
from sqlalchemy.dialects.postgresql import insert 

TZ_WIB = pytz.timezone('Asia/Jakarta')

def eksekusi_prediksi_24jam_dan_log():
    sekarang = datetime.now(TZ_WIB).replace(minute=0, second=0, microsecond=0)
    print(f"[{sekarang.strftime('%H:%M')}] Memulai Direct Forecasting 24 Jam...")
    
    try:
        paket_model = joblib.load('models/xgb_ispu_jatim_multi_otak.pkl')
        dict_model_spesialis = paket_model['dict_model_spesialis']
        fitur_model = paket_model['fitur']
    except Exception as e:
        print(f"⚠️ Model gagal dimuat: {e}")
        return

    semua_prediksi_untuk_csv = []
    data_untuk_upsert = []

    with app.app_context():
        model_aktif = ModelRegistry.query.filter_by(is_active=True).first()
        if not model_aktif:
            return

        daftar_wilayah = WilayahDetails.query.all()
        batas_waktu_h3 = sekarang - timedelta(hours=72)
        
        for wilayah in daftar_wilayah:
            riwayat = DataHistoris.query.filter(
                DataHistoris.id_wilayah == wilayah.id_wilayah,
                DataHistoris.waktu_aktual >= batas_waktu_h3.replace(tzinfo=None)
            ).order_by(DataHistoris.waktu_aktual.asc()).all()

            if len(riwayat) < 72:
                continue

            df_history_raw = pd.DataFrame([{
                'waktu_aktual': r.waktu_aktual, 'nama_wilayah': wilayah.nama_wilayah,
                'PM25': r.pm25, 'PM10': r.pm10, 'SO2': r.so2, 'CO': r.co, 'NO2': r.no2, 'O3': r.ozon
            } for r in riwayat])
            
            df_input = siapkan_fitur_prediksi(df_history_raw, ['PM25', 'PM10', 'SO2', 'CO', 'NO2', 'O3'], fitur_model)
            
            for jam_ke in range(1, 25):
                target_jam = sekarang + timedelta(hours=jam_ke)
                dict_prediksi = {}
                
                for nama_target, model_ai in dict_model_spesialis.items():
                    polutan = nama_target.split('_')[1].split(' ')[0].replace('.', '').upper()
                    pred_val = model_ai.predict(df_input)[0][jam_ke - 1] 
                    dict_prediksi[polutan] = float(max(0, pred_val))
                
                hasil_ispu = kalkulasi_ispu_final(dict_prediksi)
                
                baris_data = {
                    'id_model': model_aktif.id_model, 'id_wilayah': wilayah.id_wilayah,
                    'waktu_dibuat': sekarang.replace(tzinfo=None), 'target_waktu': target_jam.replace(tzinfo=None),
                    'pred_pm25': dict_prediksi.get('PM25', 0), 'pred_pm10': dict_prediksi.get('PM10', 0),
                    'pred_so2': dict_prediksi.get('SO2', 0), 'pred_co': dict_prediksi.get('CO', 0),
                    'pred_no2': dict_prediksi.get('NO2', 0), 'pred_ozon': dict_prediksi.get('O3', 0),
                    'pred_skor_ispu': hasil_ispu['skor_ispu_final'], 'pred_kategori_ispu': hasil_ispu['kategori_ispu']
                }
                data_untuk_upsert.append(baris_data)
                
                baris_data['nama_kota'] = wilayah.nama_wilayah 
                semua_prediksi_untuk_csv.append(baris_data)

        if data_untuk_upsert:
            stmt = insert(Predictions).values(data_untuk_upsert)
            stmt = stmt.on_conflict_do_update(
                constraint='uix_wilayah_waktu', 
                set_={k: getattr(stmt.excluded, k) for k in data_untuk_upsert[0].keys() if k not in ['id_model', 'id_wilayah', 'target_waktu']}
            )
            db.session.execute(stmt)
            db.session.commit()

    if semua_prediksi_untuk_csv:
        nama_file_csv = f"prediksi_{sekarang.strftime('%Y%m%d_%H%M')}.csv"
        pd.DataFrame(semua_prediksi_untuk_csv).to_csv(nama_file_csv, index=False)
        
        with mlflow.start_run(run_name=f"Siklus_{sekarang.strftime('%Y%m%d_%H%M')}"):
            mlflow.set_tag("waktu_eksekusi", sekarang.strftime('%Y-%m-%d %H:%M:%S'))
            mlflow.log_artifact(nama_file_csv)
        os.remove(nama_file_csv)