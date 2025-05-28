# app/routes.py
from flask import Blueprint, render_template, request as flask_request
from flask_socketio import emit, join_room, leave_room
# __init__.py'den socketio ve diğerlerini import ediyoruz. Config'i doğrudan config.py'den alacağız.
from app import socketio, background_thread, thread_stop_event, latest_weather_data_all_cities
from .config import Config # config.py app/ içinde olduğu için .config
import threading
import atexit
import time 

main_bp = Blueprint('main', __name__)
active_subscriptions = {}

@main_bp.route('/')
def index():
    cities_list = Config.CITIES 
    default_selected_city = cities_list[0] if cities_list and len(cities_list) > 0 else None
    
    if not cities_list: # Sadece boşsa değil, None ise de kontrol edebiliriz.
        print("UYARI (routes.py index): Config.CITIES listesi boş veya tanımlanmamış!")
        cities_list = [] # Şablona boş liste gönder ki hata vermesin

    max_hist_points_for_template = Config.MAX_HISTORY_POINTS_SETTING

    return render_template('index.html', 
                           cities=cities_list, 
                           selected_city=default_selected_city,
                           config_max_history_points=max_hist_points_for_template
                          )

@socketio.on('connect', namespace='/weather')
def handle_weather_connect():
    global background_thread
    client_sid = flask_request.sid
    # print(f"Client bağlandı: {client_sid}, Namespace: /weather")
    
    if not Config.OPENWEATHERMAP_API_KEY:
        print(f"API Anahtarı eksik (SID: {client_sid}). Arka plan görevi BAŞLATILMAYACAK.")
        emit('error_occurred', {'message': 'Sunucu yapılandırma hatası: API anahtarı eksik.'})
        return

    if background_thread is None or not background_thread.is_alive():
        print("Arka plan thread'i başlatılıyor...")
        thread_stop_event.clear()
        from app import weather_data_background_task
        background_thread = threading.Thread(target=weather_data_background_task)
        background_thread.daemon = True
        background_thread.start()
    # else:
        # print("Arka plan thread'i zaten çalışıyor.")
    
@socketio.on('subscribe_to_city', namespace='/weather')
def handle_subscribe_to_city(data):
    client_sid = flask_request.sid
    new_city_room = data.get('city')
    
    if not new_city_room or new_city_room not in Config.CITIES:
        print(f"UYARI (subscribe): Geçersiz şehir abonelik isteği: {new_city_room} (SID: {client_sid}).")
        emit('error_occurred', {'message': f'Geçersiz şehir adı: {new_city_room}'})
        return

    previous_room = active_subscriptions.get(client_sid)
    if previous_room and previous_room != new_city_room:
        leave_room(previous_room)
    
    join_room(new_city_room)
    active_subscriptions[client_sid] = new_city_room
    # print(f"Client {client_sid}, {new_city_room} odasına katıldı.")

    if new_city_room in latest_weather_data_all_cities:
        emit('weather_update', latest_weather_data_all_cities[new_city_room])
    else:
        city_name_display = new_city_room.split(',')[0]
        emit('weather_update', {"city": city_name_display, "message": "Veri bekleniyor..."})

@socketio.on('disconnect', namespace='/weather')
def handle_weather_disconnect():
    client_sid = flask_request.sid
    current_room = active_subscriptions.pop(client_sid, None)
    # if current_room:
    #     print(f'Client {client_sid} ({current_room} odasından) ayrıldı.')
    # else:
    #     print(f'Client {client_sid} ayrıldı (abone olduğu oda yoktu).')

def shutdown_server_on_exit(): # Fonksiyon adını değiştirdim, `shutdown_server` başka yerde kullanılabilir
    print("Sunucu kapatılıyor (atexit), arka plan thread'i durduruluyor...")
    thread_stop_event.set()
    if background_thread and background_thread.is_alive():
        # print("Arka plan thread'inin sonlanması bekleniyor...")
        background_thread.join(timeout=5) # 5 saniye bekle
        if background_thread.is_alive():
            print("UYARI (atexit): Arka plan thread'i zaman aşımına uğradı.")
        # else:
            # print("Arka plan thread'i başarıyla durduruldu (atexit).")
    # else:
        # print("Arka plan thread'i çalışmıyordu veya zaten durmuştu (atexit).")

atexit.register(shutdown_server_on_exit)