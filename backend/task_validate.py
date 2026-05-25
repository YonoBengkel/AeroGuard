import pandas as pd
from datetime import datetime, timedelta
import pytz
import mlflow
from app import app, DataHistoris

TZ_WIB = pytz.timezone('Asia/Jakarta')

def validasi_akurasi_mlflow():
    sekarang = datetime.now(TZ_WIB).replace(minute=0, second=0, microsecond=0)
    waktu_prediksi_dibuat = sekarang - timedelta(hours=1)
    
    query_waktu = waktu_prediksi_dibuat.strftime('%Y-%m-%d %H:%M:%S')
    runs = mlflow.search_runs(filter_string=f"tags.waktu_eksekusi = '{query_waktu}'")
    
    if runs.empty:
        return

    run_id_terakhir = runs.iloc[0].run_id
    nama_file_csv = f"prediksi_{waktu_prediksi_dibuat.strftime('%Y%m%d_%H%M')}.csv"
    
    try:
        path_lokal = mlflow.artifacts.download_artifacts(run_id=run_id_terakhir, artifact_path=nama_file_csv)
        df_prediksi_lalu = pd.read_csv(path_lokal)
        df_target_sekarang = df_prediksi_lalu[df_prediksi_lalu['target_waktu'] == sekarang.strftime('%Y-%m-%d %H:%M:%S')]
        
        if df_target_sekarang.empty: return

        with app.app_context():
            aktual = DataHistoris.query.filter_by(waktu_aktual=sekarang.replace(tzinfo=None)).all()
            if not aktual: return
            
            df_aktual = pd.DataFrame([{'id_wilayah': a.id_wilayah, 'act_pm25': a.pm25, 'act_pm10': a.pm10} for a in aktual])
            df_eval = pd.merge(df_target_sekarang, df_aktual, on='id_wilayah')
            
            mae_pm25 = abs(df_eval['pred_pm25'] - df_eval['act_pm25']).mean()
            mae_pm10 = abs(df_eval['pred_pm10'] - df_eval['act_pm10']).mean()
            
            with mlflow.start_run(run_id=run_id_terakhir):
                mlflow.log_metric("MAE_PM25_1H_Ahead", mae_pm25)
                mlflow.log_metric("MAE_PM10_1H_Ahead", mae_pm10)
    except Exception as e:
        print(f"❌ Gagal melakukan validasi: {e}")