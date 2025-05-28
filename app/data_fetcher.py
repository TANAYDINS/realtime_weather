# app/data_fetcher.py
import requests
import os
import sys

# Bu blok, dosya doğrudan çalıştırıldığında config'i doğru import etmek için.
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_for_config = os.path.dirname(current_dir) # app klasörünün bir üstü
    if project_root_for_config not in sys.path:
        sys.path.insert(0, project_root_for_config)
    # print(f"data_fetcher.py __main__ - sys.path'e eklendi: {project_root_for_config}")

from app.config import Config # .config yerine app.config, çünkü app bir paket

BASE_OPENWEATHERMAP_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_weather_data_from_api(city_name_with_country):
    """
    OpenWeatherMap API'sinden anlık hava durumu verilerini çeker.
    city_name_with_country: "Ankara,TR" formatında olmalı.
    """
    if not city_name_with_country:
        print("HATA (data_fetcher): Şehir adı sağlanmadı.")
        return None

    api_key = Config.OPENWEATHERMAP_API_KEY
    if not api_key:
        print(f"HATA (data_fetcher): OpenWeatherMap API anahtarı ayarlanmamış ({city_name_with_country}).")
        return None

    params = {
        'q': city_name_with_country,
        'appid': api_key,
        'units': 'metric',
        'lang': 'tr' # Hava durumu açıklamalarını Türkçe almak için (isteğe bağlı)
    }

    try:
        response = requests.get(BASE_OPENWEATHERMAP_URL, params=params, timeout=10) # Timeout ekle
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # 401: API anahtarı hatası, 404: Şehir bulunamadı, 429: Limit aşıldı
        error_message = f"API HTTP Hatası ({city_name_with_country}): {http_err}."
        if http_err.response is not None:
            error_message += f" Yanıt: {http_err.response.text}"
        print(error_message)
        # Hata durumunda da bir JSON dönebiliriz, böylece çağıran yer cod'u kontrol edebilir
        try:
            return http_err.response.json() # API genellikle hata mesajını JSON olarak döner
        except ValueError: # Eğer yanıt JSON değilse
             return {"cod": str(http_err.response.status_code), "message": str(http_err)}
    except requests.exceptions.Timeout:
        print(f"API Zaman Aşımı ({city_name_with_country}): İstek 10 saniyeden uzun sürdü.")
        return {"cod": "timeout", "message": "API isteği zaman aşımına uğradı."}
    except requests.exceptions.RequestException as req_err:
        print(f"API Bağlantı/İstek Hatası ({city_name_with_country}): {req_err}")
        return {"cod": "connection_error", "message": str(req_err)}
    except Exception as e:
        print(f"API Verisi İşlenirken Bilinmeyen Hata ({city_name_with_country}): {e}")
        return {"cod": "unknown_error", "message": str(e)}

if __name__ == '__main__':
    print("--- data_fetcher.py Şehir Test Scripti ---")
    if not Config.OPENWEATHERMAP_API_KEY:
        print("HATA: OPENWEATHERMAP_API_KEY .env dosyasından yüklenemedi veya config.py'de ayarlanmadı.")
        print("Lütfen .env dosyanızı ve app/config.py dosyasını kontrol edin.")
    else:
        print(f"Kullanılan API Anahtarı (ilk 5 karakter): {Config.OPENWEATHERMAP_API_KEY[:5]}...")

        # Test edilecek şehirler listesi (Config.CITIES'i kullan)
        # İsterseniz buraya spesifik sorunlu şehirleri ekleyebilirsiniz test için.
        cities_to_test = Config.CITIES
        # cities_to_test = ["Gumushane,TR", "Ankara,TR", "NonExistentCity,XX"] # Spesifik test için

        if not cities_to_test:
            print("Config.CITIES listesi boş, test edilecek şehir yok.")
        else:
            print(f"\n{len(cities_to_test)} şehir test edilecek Config.CITIES listesinden...\n")
            successful_count = 0
            failed_count = 0
            for city in cities_to_test:
                print(f"-> {city} için veri çekiliyor...")
                data = get_weather_data_from_api(city)
                if data and data.get("cod") == 200:
                    print(f"   BAŞARILI! {data.get('name')}: {data.get('main', {}).get('temp')}°C, {data.get('weather', [{}])[0].get('description')}")
                    successful_count += 1
                elif data and data.get("cod") != 200 : # API'den hata kodu geldiyse
                    print(f"   BAŞARISIZ! API Hatası ({city}): Kod {data.get('cod')}, Mesaj: {data.get('message')}")
                    failed_count += 1
                else: # get_weather_data_from_api None veya beklenmedik bir şey döndürdüyse
                    print(f"   BAŞARISIZ! ({city}) için `get_weather_data_from_api` fonksiyonundan beklenmedik yanıt veya None.")
                    failed_count += 1
                print("-" * 20)
            
            print(f"\n--- Test Sonucu ---")
            print(f"Toplam Test Edilen: {len(cities_to_test)}")
            print(f"Başarılı: {successful_count}")
            print(f"Başarısız: {failed_count}")
            if failed_count > 0:
                print("\nLütfen BAŞARISIZ olan şehirlerin isimlerini OpenWeatherMap'te kontrol edin")
                print("ve app/config.py dosyasındaki TURKISH_PROVINCES_API_FRIENDLY listesini güncelleyin.")
                print("Doğru format genellikle 'ŞehirAdı,TR' şeklindedir (örn: 'Istanbul,TR').")
                print("Türkçe karakterler sorun çıkarıyorsa, ASCII karşılıklarını deneyin (örn: 'Canakkale,TR').")