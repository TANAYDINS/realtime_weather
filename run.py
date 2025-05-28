# run.py
from app import create_app, socketio
from app.config import Config # Config'i app.config'den import et

app = create_app(Config) # Config objesini create_app'e parametre olarak ver

if __name__ == '__main__':
    print(f"Uygulama başlatılıyor... http://127.0.0.1:{app.config.get('PORT', 5001)}")
    if not Config.OPENWEATHERMAP_API_KEY:
        print("-" * 50)
        print("!!! KRİTİK UYARI !!!")
        print("OpenWeatherMap API Anahtarı bulunamadı veya yüklenemedi.")
        print("Lütfen .env dosyanızı ve app/config.py dosyasını kontrol edin.")
        print("Uygulama API'den veri çekemeyecektir.")
        print("-" * 50)

    # Geliştirme sunucusu için port ve host ayarları
    # debug=True geliştirme sırasında kullanışlıdır.
    # use_reloader=False, Flask'ın kendi yeniden başlatıcısının arka plan thread'ini
    # iki kez başlatmasını engellemek için önemlidir.
    # Eğer host='0.0.0.0' kullanıyorsanız, güvenlik duvarı ayarlarınızı kontrol edin.
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, use_reloader=False, allow_unsafe_werkzeug=True)
    # allow_unsafe_werkzeug=True, Werkzeug'un yeni versiyonlarında debug=True ve reloader=False
    # kombinasyonu için gerekebilir. Eğer hata alırsanız bunu kaldırabilirsiniz.