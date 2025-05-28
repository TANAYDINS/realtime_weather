# app/data_processor.py
import datetime
import numpy as np
from app.config import Config # Config sınıfını import et

# Sayısal yöntem modüllerimizi import edelim
from app.numerical_methods import integration, interpolation, differentiation # ODE'yi şimdilik kullanmıyoruz

# Şehir bazlı geçmiş verileri saklamak için sözlükler
# Bu sözlükler uygulama çalıştığı sürece bellekte tutulacak.
# Uzun süreli çalıştırmalarda bellek yönetimi için daha gelişmiş stratejiler (örn. Redis) düşünülebilir.
temperature_history = {} 
rain_rate_history = {}   

# Geçmiş veri noktası sayısı (Config dosyasından alınıyor)
MAX_HISTORY_POINTS = Config.MAX_HISTORY_POINTS_SETTING 
# İnterpolasyon ve tahmin için üretilecek nokta sayıları
INTERPOLATION_POINTS_TO_GENERATE = 25 # İnterpolasyon grafiğinde kaç nokta gösterileceği
PREDICTION_HORIZON_SECONDS = 15 * 60 # Tahmin ufku: 15 dakika (saniye cinsinden)
PREDICTION_POINTS_TO_GENERATE = 4    # Tahmin ufkunda kaç nokta üretilecek (son bilinen + 3 gelecek nokta)

def process_api_data(api_data, city_name_from_config):
    """
    OpenWeatherMap API'sinden gelen ham veriyi işler, sayısal analizleri uygular
    ve istemciye gönderilecek formatta bir sözlük döndürür.

    Args:
        api_data (dict): OpenWeatherMap API'sinden gelen JSON yanıtı.
        city_name_from_config (str): Şehrin yapılandırmadaki tam adı (örn: "Mersin,TR").
    
    Returns:
        dict or None: İşlenmiş veri sözlüğü veya hata durumunda None.
    """
    if not api_data or api_data.get("cod") != 200:
        print(f"HATA (data_processor): {city_name_from_config} için geçersiz API verisi: {api_data.get('message', 'Bilinmeyen hata') if api_data else 'Veri yok'}")
        return None

    try:
        # API'den gelen Unix zaman damgasını al, yoksa mevcut UTC zamanını kullan
        api_timestamp_unix = api_data.get("dt", datetime.datetime.now(datetime.timezone.utc).timestamp())
        api_timestamp_dt = datetime.datetime.fromtimestamp(api_timestamp_unix, tz=datetime.timezone.utc)
        timestamp_iso = api_timestamp_dt.isoformat() # İstemci tarafında parse etmesi kolay format

        # Şehir için geçmiş veri listelerini al veya oluştur
        city_temp_history = temperature_history.setdefault(city_name_from_config, [])
        city_rain_history = rain_rate_history.setdefault(city_name_from_config, [])

        # Temel hava durumu verilerini al
        main_data = api_data.get("main", {})
        weather_info = api_data.get("weather", [{}])[0] # Hava durumu listesinin ilk elemanı
        wind_data = api_data.get("wind", {})
        sys_data = api_data.get("sys", {})
        rain_data = api_data.get("rain", {})
        snow_data = api_data.get("snow", {})

        current_temp = main_data.get("temp")
        current_humidity = main_data.get("humidity")
        # Yağış verisi "1h" anahtarı altında gelir (son 1 saatteki mm cinsinden)
        current_rain_rate_hourly = rain_data.get("1h", 0.0) 

        # İstemciye gönderilecek temel veri yapısı
        processed_data = {
            "city_fq": city_name_from_config, # İstemcinin hangi şehir için veri aldığını bilmesi için
            "timestamp": timestamp_iso,
            "city": api_data.get("name", city_name_from_config.split(',')[0]), # API'den gelen şehir adı
            "temperature": current_temp,
            "humidity": current_humidity,
            "feels_like": main_data.get("feels_like"),
            "pressure": main_data.get("pressure"),
            "wind_speed": wind_data.get("speed"),
            "description": weather_info.get("description"),
            "icon_code": weather_info.get("icon"),
            "rain_last_1h": current_rain_rate_hourly,
            "snow_last_1h": snow_data.get("1h", 0.0), # Kar verisi (varsa)
            "sunrise": datetime.datetime.fromtimestamp(sys_data.get("sunrise"), tz=datetime.timezone.utc).strftime('%H:%M UTC') if sys_data.get("sunrise") else None,
            "sunset": datetime.datetime.fromtimestamp(sys_data.get("sunset"), tz=datetime.timezone.utc).strftime('%H:%M UTC') if sys_data.get("sunset") else None,
            
            # Sayısal yöntem sonuçları için başlangıç değerleri
            "nm_total_rain_trapezoidal": None,
            "nm_total_rain_simpson": None,
            "nm_original_temp_series_for_plot": [], # İnterpolasyon için orijinal veri
            "nm_interpolated_temps_linear": [],
            "nm_interpolated_temps_cubic": [],
            "nm_temp_derivative_central": None,
            "nm_predicted_temps_linear": [],
            "nm_predicted_temps_cubic": []
        }
        
        # Sıcaklık geçmişini güncelle
        if current_temp is not None:
            # Aynı zaman damgasına sahip mükerrer veri eklememek için kontrol
            if not city_temp_history or city_temp_history[-1][0] != api_timestamp_unix:
                city_temp_history.append((api_timestamp_unix, current_temp))
            # Geçmiş veri listesini MAX_HISTORY_POINTS ile sınırla
            while len(city_temp_history) > MAX_HISTORY_POINTS:
                city_temp_history.pop(0)
        
        # Yağış oranı geçmişini güncelle (saatlik mm cinsinden)
        # Aynı zaman damgasına sahip mükerrer veri eklememek için kontrol
        if not city_rain_history or city_rain_history[-1][0] != api_timestamp_unix:
            city_rain_history.append((api_timestamp_unix, current_rain_rate_hourly))
        while len(city_rain_history) > MAX_HISTORY_POINTS:
            city_rain_history.pop(0)

        # SAYISAL YÖNTEMLER
        # ------------------

        # 1. Yağış Entegrasyonu (Toplam Yağış Hesabı)
        if len(city_rain_history) >= 2:
            # Geçmiş verileri zamana göre sırala (önemli!)
            sorted_rain_history = sorted(city_rain_history, key=lambda p: p[0])
            rain_times_unix = np.array([p[0] for p in sorted_rain_history])
            rain_rates_hourly = np.array([p[1] for p in sorted_rain_history])
            
            # Yağış oranını mm/saat'ten mm/saniye'ye çevir (entegrasyon için zaman birimi saniye olacak)
            rain_rates_mm_per_sec = rain_rates_hourly / 3600.0
            
            # Entegrasyon için en az 2 farklı zaman noktası gerekli
            if len(rain_times_unix) >= 2 and len(np.unique(rain_times_unix)) >= 2:
                total_rain_trapz = integration.trapezoidal_rule(rain_rates_mm_per_sec, rain_times_unix)
                if total_rain_trapz is not None:
                    processed_data["nm_total_rain_trapezoidal"] = round(total_rain_trapz, 4)
            
            # Simpson kuralı için en az 3 farklı zaman noktası gerekli
            if len(rain_times_unix) >= 3 and len(np.unique(rain_times_unix)) >= 3:
                total_rain_simpson = integration.simpsons_rule(rain_rates_mm_per_sec, rain_times_unix)
                if total_rain_simpson is not None:
                    processed_data["nm_total_rain_simpson"] = round(total_rain_simpson, 4)

        # 2. Sıcaklık İnterpolasyonu, Türevi ve Tahmini
        if len(city_temp_history) >= 2:
            sorted_temp_history = sorted(city_temp_history, key=lambda p: p[0])
            temp_times_unix_all = np.array([p[0] for p in sorted_temp_history])
            temps_values_all = np.array([p[1] for p in sorted_temp_history])

            # İnterpolasyon ve türev için benzersiz zaman noktaları kullanmak önemli
            unique_times_unix, unique_indices = np.unique(temp_times_unix_all, return_index=True)
            unique_temps_values = temps_values_all[unique_indices]

            # Orijinal (filtrelenmiş) sıcaklık serisini grafikte göstermek için sakla
            processed_data["nm_original_temp_series_for_plot"] = [
                (datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat(), temp) 
                for ts, temp in zip(unique_times_unix, unique_temps_values)
            ]

            if len(unique_times_unix) >= 2: # En az 2 farklı nokta gerekli
                # İnterpolasyon için yeni x değerleri (zaman aralığı)
                # unique_times_unix[0]'dan unique_times_unix[-1]'e kadar INTERPOLATION_POINTS_TO_GENERATE sayıda nokta
                if unique_times_unix[0] < unique_times_unix[-1]: # Başlangıç ve bitiş zamanları farklı olmalı
                    x_new_for_interpolation = np.linspace(unique_times_unix[0], unique_times_unix[-1], num=INTERPOLATION_POINTS_TO_GENERATE)
                    
                    y_linear_interp = interpolation.linear_interpolation(unique_times_unix, unique_temps_values, x_new_for_interpolation)
                    processed_data["nm_interpolated_temps_linear"] = [
                        (datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat(), temp if not np.isnan(temp) else None) 
                        for ts, temp in zip(x_new_for_interpolation, y_linear_interp)
                    ]
                    
                    # Kübik spline için en az 2 nokta gerekir, ama 4+ daha iyi sonuç verir
                    if len(unique_times_unix) >= 2: # Scipy daha azıyla da çalışır
                        y_cubic_interp = interpolation.cubic_spline_interpolation(unique_times_unix, unique_temps_values, x_new_for_interpolation)
                        processed_data["nm_interpolated_temps_cubic"] = [
                            (datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat(), temp if not np.isnan(temp) else None) 
                            for ts, temp in zip(x_new_for_interpolation, y_cubic_interp)
                        ]

                # Tahmin (Ekstrapolasyon)
                last_known_time_unix = unique_times_unix[-1]
                # Tahmin edilecek zaman noktaları (son bilinen nokta + gelecekteki N nokta)
                prediction_time_points_unix = np.linspace(
                    last_known_time_unix, 
                    last_known_time_unix + PREDICTION_HORIZON_SECONDS, 
                    num=PREDICTION_POINTS_TO_GENERATE 
                )
                
                predicted_temps_linear_extrap = interpolation.linear_interpolation(unique_times_unix, unique_temps_values, prediction_time_points_unix)
                processed_data["nm_predicted_temps_linear"] = [
                    (datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat(), temp if not np.isnan(temp) else None)
                    for ts, temp in zip(prediction_time_points_unix, predicted_temps_linear_extrap)
                ]
                
                if len(unique_times_unix) >= 2: # Kübik için
                    predicted_temps_cubic_extrap = interpolation.cubic_spline_interpolation(unique_times_unix, unique_temps_values, prediction_time_points_unix)
                    processed_data["nm_predicted_temps_cubic"] = [
                        (datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat(), temp if not np.isnan(temp) else None)
                        for ts, temp in zip(prediction_time_points_unix, predicted_temps_cubic_extrap)
                    ]
            
            # Sıcaklık Değişim Hızı (Türev)
            # Merkezi fark için en az 3 farklı nokta gerekli
            if len(unique_times_unix) >= 3:
                temp_derivatives_central = differentiation.central_difference(unique_temps_values, unique_times_unix)
                # np.gradient NaN döndürmez, ama biz yine de kontrol edelim
                if temp_derivatives_central.size > 0:
                    # Son geçerli türev değerini al (bu, sondan bir önceki nokta için hesaplanan türevdir)
                    # Eğer tüm geçmiş için ortalama veya en son anlık değişim isteniyorsa, bu kısım değişebilir.
                    # Şimdilik son hesaplanan türevi alıyoruz.
                    last_valid_derivative = temp_derivatives_central[-1] # np.gradient son türevi de hesaplar (ileri/geri farkla)
                    if not np.isnan(last_valid_derivative):
                        # Türev saniye başına °C cinsinden, dakikaya çevirmek için *60
                        processed_data["nm_temp_derivative_central"] = round(last_valid_derivative * 60, 3) 
        
        return processed_data

    except Exception as e:
        print(f"KRİTİK HATA (data_processor - {city_name_from_config}): Veri işlenirken istisna oluştu: {e}")
        import traceback
        traceback.print_exc() # Hatanın tam izini yazdır
        return None