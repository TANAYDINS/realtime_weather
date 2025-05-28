# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from .config import Config # config.py app/ içinde olduğu için .config
import threading
import time
import os

socketio = SocketIO()

background_thread = None
thread_stop_event = threading.Event()
latest_weather_data_all_cities = {}

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object(config_class) # config_class zaten Config objesi olacak

    if not app.config.get('OPENWEATHERMAP_API_KEY'):
        print("KRİTİK UYARI (create_app): OpenWeatherMap API anahtarı YÜKLENEMEDİ!")
    else:
        print(f"OpenWeatherMap API Anahtarı yüklendi (create_app): {app.config['OPENWEATHERMAP_API_KEY'][:5]}...")

    socketio.init_app(app, cors_allowed_origins="*")

    from .routes import main_bp # .routes, çünkü routes.py app/ içinde
    app.register_blueprint(main_bp)

    return app

def weather_data_background_task():
    # Bu importlar fonksiyon içinde olmalı ki create_app çağrılmadan önce döngüsel bağımlılık olmasın
    from app.data_fetcher import get_weather_data_from_api
    from app.data_processor import process_api_data
    
    current_time_start_task = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time_start_task}] Arka plan veri çekme görevi BAŞLATILIYOR.")
    
    if not Config.CITIES:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] HATA (BG Görev): Config.CITIES listesi boş.")
        return
    if not Config.OPENWEATHERMAP_API_KEY:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] KRİTİK HATA (BG Görev): OPENWEATHERMAP_API_KEY eksik.")
        return

    while not thread_stop_event.is_set():
        # print(f"[{time.strftime('%H:%M:%S')}] Yeni veri çekme döngüsü...")
        successful_api_fetches = 0
        cities_processed_successfully = 0
        
        for city_name_in_config in Config.CITIES:
            if thread_stop_event.is_set(): break
            
            raw_data = get_weather_data_from_api(city_name_in_config) # Bu fonksiyon zaten kendi loglarını basıyor
            
            if raw_data and raw_data.get("cod") == 200:
                successful_api_fetches += 1
                processed_data = process_api_data(raw_data, city_name_in_config)
                if processed_data:
                    latest_weather_data_all_cities[city_name_in_config] = processed_data
                    socketio.emit('weather_update', processed_data, room=city_name_in_config, namespace='/weather')
                    cities_processed_successfully +=1
                # else:
                    # process_api_data None döndü, zaten loglamış olmalı (veya gerekirse burada logla)
                    # print(f"[{time.strftime('%H:%M:%S')}] UYARI (BG Görev): {city_name_in_config} için veri işlenemedi.")
            # else: raw_data hatalı veya None ise get_weather_data_from_api zaten logladı.
            
            time.sleep(1.1) # API çağrıları arası bekleme
        
        # print(f"[{time.strftime('%H:%M:%S')}] Döngü tamamlandı. Başarılı API: {successful_api_fetches}/{len(Config.CITIES)}, İşlenen: {cities_processed_successfully}/{len(Config.CITIES)}")
        
        for _ in range(Config.DATA_FETCH_INTERVAL):
            if thread_stop_event.is_set(): break
            time.sleep(1)
            
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Arka plan veri çekme görevi DURDURULDU.")