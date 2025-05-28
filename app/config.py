# app/config.py
import os
from dotenv import load_dotenv

# .env dosyasını projenin kök dizininden yükle
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"BAŞARILI: .env dosyası yüklendi: {dotenv_path}")
else:
    print(f"UYARI: .env dosyası BULUNAMADI: {dotenv_path}")
    print(f"Lütfen .env dosyasının '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}' dizininde olduğundan emin olun.")

# ÖNEMLİ: Bu liste OpenWeatherMap API'sinin kabul ettiği isimlerle güncellenmelidir.
# `app/data_fetcher.py` içindeki test scriptini kullanarak her bir şehri doğrulayın!
# Aşağıdaki liste sadece bir başlangıçtır ve çalışmayan isimler içerebilir.
TURKISH_PROVINCES_API_FRIENDLY = [
    "Adana,TR", "Adıyaman,TR", "Afyonkarahisar,TR", "Ağrı,TR", "Amasya,TR",
    "Ankara,TR", "Antalya,TR", "Artvin,TR", "Aydın,TR", "Balıkesir,TR",
    "Bilecik,TR", "Bingöl,TR", "Bitlis,TR", "Bolu,TR", "Burdur,TR",
    "Bursa,TR", "Çanakkale,TR", "Çankırı,TR", "Çorum,TR", "Denizli,TR",
    "Diyarbakır,TR", "Edirne,TR", "Elazığ,TR", "Erzincan,TR", "Erzurum,TR",
    "Eskişehir,TR", "Gaziantep,TR", "Giresun,TR", "Gümüşhane,TR", # Gumushane 404 veriyordu, doğru ismi bulun!
    "Hakkari,TR", "Hatay,TR", "Isparta,TR", "Mersin,TR", "İstanbul,TR", "İzmir,TR",
    "Kars,TR", "Kastamonu,TR", "Kayseri,TR", "Kırklareli,TR", "Kırşehir,TR",
    "Kocaeli,TR", "Konya,TR", "Kütahya,TR", "Malatya,TR", "Manisa,TR",
    "Kahramanmaraş,TR", "Mardin,TR", "Muğla,TR", "Muş,TR", "Nevşehir,TR",
    "Niğde,TR", "Ordu,TR", "Rize,TR", "Sakarya,TR", "Samsun,TR",
    "Siirt,TR", "Sinop,TR", "Sivas,TR", "Tekirdağ,TR", "Tokat,TR",
    "Trabzon,TR", "Tunceli,TR", "Şanlıurfa,TR", "Uşak,TR", "Van,TR",
    "Yozgat,TR", "Zonguldak,TR", "Aksaray,TR", "Bayburt,TR", "Karaman,TR",
    "Kirikkale,TR", "Batman,TR", "Şırnak,TR", "Bartın,TR", "Ardahan,TR",
    "Iğdır,TR", "Yalova,TR", "Karabük,TR", "Kilis,TR", "Osmaniye,TR",
    "Düzce,TR"
]

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lutfen-bu-anahtari-degistirin-cok-onemli'
    OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')
    
    CITIES = TURKISH_PROVINCES_API_FRIENDLY
    
    DATA_FETCH_INTERVAL = 180 # 3 dakika - Tüm şehirler için bir tur yaklaşık 1.5-2dk sürer, sonra 3dk beklenir.
    
    MAX_HISTORY_POINTS_SETTING = 30 # data_processor ve template için ortak nokta