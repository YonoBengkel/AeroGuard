import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import UniqueConstraint

# Memuat variabel dari .env
load_dotenv()

app = Flask(__name__)

# Menarik PostgreSQL Connection String
db_url = os.getenv('DATABASE_URL')
if not db_url:
    raise ValueError("DATABASE_URL tidak ditemukan di file .env!")

# SQLAlchemy terkadang butuh awalan 'postgresql://' bukan 'postgres://'
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi jembatan database
db = SQLAlchemy(app)

# ==========================================
# SKEMA DATABASE (Tabel)
# ==========================================

class WilayahDetails(db.Model):
    __tablename__ = 'wilayah_details'
    id_wilayah = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_wilayah = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    __table_args__ = (UniqueConstraint('latitude', 'longitude', name='uq_latitude_longitude'),)
    data_historis = db.relationship('DataHistoris', backref='wilayah', lazy=True)
    prediksi = db.relationship('Predictions', backref='wilayah', lazy=True)

class ModelRegistry(db.Model):
    __tablename__ = 'model_registry'
    id_model = db.Column(db.Integer, primary_key=True, autoincrement=True)
    algoritma = db.Column(db.String(50), nullable=False)
    versi_model = db.Column(db.String(20), nullable=False)
    hyperparameter = db.Column(db.JSON)
    training_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    
    prediksi = db.relationship('Predictions', backref='model', lazy=True)

class DataHistoris(db.Model):
    __tablename__ = 'data_historis'
    id_data = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_wilayah = db.Column(db.Integer, db.ForeignKey('wilayah_details.id_wilayah'), nullable=False)
    waktu_aktual = db.Column(db.DateTime, nullable=False)
    pm25 = db.Column(db.Float)
    pm10 = db.Column(db.Float)
    so2 = db.Column(db.Float)
    co = db.Column(db.Float)
    no2 = db.Column(db.Float)
    ozon = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Predictions(db.Model):
    __tablename__ = 'predictions'
    id_prediksi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_model = db.Column(db.Integer, db.ForeignKey('model_registry.id_model'), nullable=False)
    id_wilayah = db.Column(db.Integer, db.ForeignKey('wilayah_details.id_wilayah'), nullable=False)
    waktu_dibuat = db.Column(db.DateTime, default=datetime.utcnow)
    target_waktu = db.Column(db.DateTime, nullable=False)
    pred_pm25 = db.Column(db.Float)
    pred_pm10 = db.Column(db.Float)
    pred_so2 = db.Column(db.Float)
    pred_co = db.Column(db.Float)
    pred_no2 = db.Column(db.Float)
    pred_ozon = db.Column(db.Float)
    pred_skor_ispu = db.Column(db.Integer)
    pred_kategori_ispu = db.Column(db.String(50))
    status = db.Column(db.String(50), default='PENDING')
    
    # KUNCI UPSERT: Memastikan tidak ada 2 prediksi untuk wilayah & target waktu yang sama
    __table_args__ = (
        UniqueConstraint('id_wilayah', 'target_waktu', name='uix_wilayah_waktu'),
    )

if __name__ == '__main__':
    # Script kecil untuk mengetes apakah SQLAlchemy berhasil membaca Supabase
    with app.app_context():
        try:
            # Mencoba query tabel WilayahDetails
            jumlah_wilayah = WilayahDetails.query.count()
            print("✅ SQLAlchemy berhasil terhubung ke Supabase!")
            print(f"✅ Saat ini ada {jumlah_wilayah} baris di tabel wilayah_details.")
        except Exception as e:
            print(f"❌ Koneksi SQLAlchemy gagal: {e}")