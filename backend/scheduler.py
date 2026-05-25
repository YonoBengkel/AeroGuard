import os
import mlflow
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

# Import tugas-tugas dari modul pekerja
from task_fetch import tarik_data_aktual_per_jam
from task_validate import validasi_akurasi_mlflow
from task_predict import eksekusi_prediksi_24jam_dan_log

load_dotenv()

# Setup MLflow Global agar semua worker tahu harus mengirim log ke mana
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
mlflow.set_experiment("AeroGuard_Production_Pipeline")

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    
    # Jadwal 1: Ekstraksi Data (Menit 0)
    scheduler.add_job(tarik_data_aktual_per_jam, 'cron', minute=0)
    
    # Jadwal 2: Validasi MLflow (Menit 5)
    scheduler.add_job(validasi_akurasi_mlflow, 'cron', minute=5)
    
    # Jadwal 3: Prediksi dan UPSERT (Menit 10)
    scheduler.add_job(eksekusi_prediksi_24jam_dan_log, 'cron', minute=10)
    
    print("--- Memulai Uji Coba Manual (Satu Putaran) ---")
    # Panggil langsung tanpa menunggu jadwal
    tarik_data_aktual_per_jam()
    eksekusi_prediksi_24jam_dan_log()
    validasi_akurasi_mlflow()
    
    print("--- Scheduler Modular MLOps Aktif ---")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nMematikan scheduler...")