import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import mlflow
from dotenv import load_dotenv

load_dotenv()

# Setup MLflow ke DagsHub
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
EXPERIMENT_NAME = "AeroGuard_Baseline_Comparison"
mlflow.set_experiment(EXPERIMENT_NAME)

def jalankan_komparasi_baseline():
    print("Membaca data historis...")
    # Pastikan letak file CSV sudah benar (1 tingkat di atas folder backend)
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset_polutan_jatim.csv')
    df = pd.read_csv(csv_path)
    
    # Preprocessing Sederhana
    df.rename(columns={
        'PM2.5 (µg/m³)': 'PM25', 'PM10 (µg/m³)': 'PM10',
        'SO2 (µg/m³)': 'SO2', 'CO (µg/m³)': 'CO',
        'NO2 (µg/m³)': 'NO2', 'Ozon (µg/m³)': 'O3'
    }, inplace=True)
    
    # Membuang kolom non-numerik untuk uji coba cepat
    df = df.drop(columns=['Kota', 'Waktu'])
    df.dropna(inplace=True)
    
    daftar_polutan = ['PM25', 'PM10', 'SO2', 'CO', 'NO2', 'O3']
    
    # 4 Kandidat Algoritma yang Dipertandingkan
    kandidat_model = {
        "RandomForest": RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "ExtraTrees": ExtraTreesRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "LightGBM": LGBMRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    }

    for polutan in daftar_polutan:
        print(f"\n=== Evaluasi Baseline untuk Polutan: {polutan} ===")
        
        # Pisahkan Target (Y) dan Fitur inputan (X)
        X = df.drop(columns=[polutan])
        y = df[polutan]
        
        # Split Data (80% Train, 20% Test)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        for nama_model, algoritma in kandidat_model.items():
            run_name = f"Baseline_{polutan}_{nama_model}"
            
            with mlflow.start_run(run_name=run_name):
                print(f"Melatih {nama_model}...")
                algoritma.fit(X_train, y_train)
                
                # Prediksi dan Evaluasi
                prediksi = algoritma.predict(X_test)
                mae = mean_absolute_error(y_test, prediksi)
                
                # Catat Parameter dan Metrik ke DagsHub
                mlflow.log_param("algoritma", nama_model)
                mlflow.log_param("polutan", polutan)
                mlflow.log_metric("MAE", mae)
                
                print(f"Hasil {nama_model} -> MAE: {mae:.4f}")

if __name__ == "__main__":
    jalankan_komparasi_baseline()