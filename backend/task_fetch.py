import os
import requests
from datetime import datetime
import pytz
from app import app, db, WilayahDetails, DataHistoris

API_KEY = os.getenv("OPENWEATHER_API_KEY")
TZ_WIB = pytz.timezone('Asia/Jakarta')

def tarik_data_aktual_per_jam():
    sekarang = datetime.now(TZ_WIB).replace(minute=0, second=0, microsecond=0)
    print(f"[{sekarang.strftime('%H:%M')}] Menarik data aktual OpenWeatherMap...")
    
    with app.app_context():
        daftar_wilayah = WilayahDetails.query.all()
        for wilayah in daftar_wilayah:
            if DataHistoris.query.filter_by(id_wilayah=wilayah.id_wilayah, waktu_aktual=sekarang.replace(tzinfo=None)).first():
                continue 
            
            url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={wilayah.latitude}&lon={wilayah.longitude}&appid={API_KEY}"
            try:
                respon = requests.get(url).json()
                data_polusi = respon['list'][0]['components']
                
                catatan_baru = DataHistoris(
                    id_wilayah=wilayah.id_wilayah,
                    waktu_aktual=sekarang.replace(tzinfo=None),
                    pm25=data_polusi.get('pm2_5', 0), pm10=data_polusi.get('pm10', 0),
                    so2=data_polusi.get('so2', 0), co=data_polusi.get('co', 0),
                    no2=data_polusi.get('no2', 0), ozon=data_polusi.get('o3', 0)
                )
                db.session.add(catatan_baru)
            except Exception as e:
                print(f"Gagal menarik {wilayah.nama_wilayah}: {e}")
        
        db.session.commit()
    print("✅ Data aktual berhasil disimpan.")