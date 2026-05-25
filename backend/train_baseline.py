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

# Setup MLflow ke DagsHub dengan nama eksperimen baru
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
EXPERIMENT_NAME = "AeroGuard_Baseline_Spasial"
mlflow.set_experiment(EXPERIMENT_NAME)

def jalankan_komparasi_baseline_spasial():
    print("Membaca data historis...")
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset_polutan_jatim.csv')
    df = pd.read_csv(csv_path)
    
    # 1. Preprocessing Penamaan
    df.rename(columns={
        'Kota': 'nama_wilayah', 'Waktu': 'waktu_aktual',
        'PM2.5 (µg/m³)': 'PM25', 'PM10 (µg/m³)': 'PM10',
        'SO2 (µg/m³)': 'SO2', 'CO (µg/m³)': 'CO',
        'NO2 (µg/m³)': 'NO2', 'Ozon (µg/m³)': 'O3'
    }, inplace=True)
    
    # 2. Rekayasa Fitur Temporal (Kecerdasan Waktu)
    df['waktu_aktual'] = pd.to_datetime(df['waktu_aktual'])
    df['jam'] = df['waktu_aktual'].dt.hour
    df['bulan'] = df['waktu_aktual'].dt.month
    df['hari_dalam_minggu'] = df['waktu_aktual'].dt.dayofweek
    
    df = df.drop(columns=['waktu_aktual'])
    
    # 3. Rekayasa Fitur Spasial (One-Hot Encoding untuk 38 Kota)
    df = pd.get_dummies(df, columns=['nama_wilayah'], drop_first=False)
    
    df.dropna(inplace=True)
    
    daftar_polutan = ['PM25', 'PM10', 'SO2', 'CO', 'NO2', 'O3']
    
    kandidat_model = {
        "RandomForest": RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "ExtraTrees": ExtraTreesRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "LightGBM": LGBMRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    }

    for polutan in daftar_polutan:
        print(f"\n=== Evaluasi Baseline Spasial untuk Polutan: {polutan} ===")
        
        # 4. Pencegahan Data Leakage (Kebocoran Data)
        # Model tidak boleh melihat nilai polutan lain pada jam yang sama saat belajar
        kolom_bocor = [p for p in daftar_polutan if p != polutan]
        X = df.drop(columns=[polutan] + kolom_bocor)
        y = df[polutan]
        
        # Mereset index sangat penting untuk mencegah ValueError 'Index' jika ada manipulasi matriks
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        for nama_model, algoritma in kandidat_model.items():
            run_name = f"Baseline_Spasial_{polutan}_{nama_model}"
            
            with mlflow.start_run(run_name=run_name):
                print(f"Melatih {nama_model}...")
                algoritma.fit(X_train, y_train)
                
                prediksi = algoritma.predict(X_test)
                mae = mean_absolute_error(y_test, prediksi)
                
                mlflow.log_param("algoritma", nama_model)
                mlflow.log_param("polutan", polutan)
                mlflow.log_metric("MAE", mae)
                
                print(f"Hasil {nama_model} -> MAE: {mae:.4f}")

if __name__ == "__main__":
    jalankan_komparasi_baseline_spasial()