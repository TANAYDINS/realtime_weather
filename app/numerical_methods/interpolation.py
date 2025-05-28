# app/numerical_methods/interpolation.py
import numpy as np
from scipy.interpolate import interp1d, CubicSpline

def linear_interpolation(x_known, y_known, x_new):
    """Lineer interpolasyon uygular."""
    x_k_arr = np.array(x_known)
    y_k_arr = np.array(y_known)
    x_n_arr = np.array(x_new)

    if len(x_k_arr) < 2 or len(y_k_arr) < 2 or len(x_k_arr) != len(y_k_arr):
        # print("Lineer interpolasyon için yetersiz veri.")
        return np.array([np.nan] * len(x_n_arr)) # x_new ile aynı boyutta NaN dizisi
    
    try:
        f_linear = interp1d(x_k_arr, y_k_arr, kind='linear', fill_value="extrapolate", bounds_error=False)
        return f_linear(x_n_arr)
    except Exception as e:
        # print(f"Lineer interpolasyonda hata: {e}")
        return np.array([np.nan] * len(x_n_arr))


def cubic_spline_interpolation(x_known, y_known, x_new):
    """Kübik spline interpolasyonu uygular."""
    x_k_arr = np.array(x_known)
    y_k_arr = np.array(y_known)
    x_n_arr = np.array(x_new)

    # Kübik spline için genellikle en az 4 nokta daha iyi sonuç verir, ama Scipy daha azıyla da çalışabilir.
    if len(x_k_arr) < 2 or len(y_k_arr) < 2 or len(x_k_arr) != len(y_k_arr):
        # print("Kübik spline için yetersiz veri.")
        return np.array([np.nan] * len(x_n_arr))
    
    if len(x_k_arr) < 4:
        # print("Uyarı: Kübik spline için en az 4 nokta önerilir. Sonuçlar ideal olmayabilir.")
        # Az noktayla lineer interpolasyona fallback yapabilir veya interp1d(kind='cubic') deneyebiliriz.
        # Şimdilik CubicSpline'ı deneyelim, Scipy bir çözüm bulmaya çalışacaktır.
        pass # Scipy'nin daha az nokta ile nasıl başa çıktığını görelim
    
    try:
        # bc_type='natural' veya 'not-a-knot' (varsayılan) gibi sınır koşulları denenebilir.
        cs = CubicSpline(x_k_arr, y_k_arr, extrapolate=True) # extrapolate=True sınır dışı tahminlere izin verir
        return cs(x_n_arr)
    except ValueError as ve: # Örneğin x_known sıralı değilse
        # print(f"Kübik spline interpolasyonunda Değer Hatası (muhtemelen x_known sıralı değil): {ve}")
        return np.array([np.nan] * len(x_n_arr))
    except Exception as e:
        # print(f"Kübik spline interpolasyonunda hata: {e}")
        return np.array([np.nan] * len(x_n_arr))