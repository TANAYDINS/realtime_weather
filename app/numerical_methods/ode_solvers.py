# app/numerical_methods/ode_solvers.py
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d

def solve_newton_cooling_ode(T0, t_span_unix, t_eval_unix, k, 
                             T_ortam_series_times_unix, T_ortam_series_values):
    """
    Newton'un soğuma/ısınma ODE'sini çözer.
    T0: Nesnenin başlangıç sıcaklığı.
    t_span_unix: (t_start_unix, t_end_unix) çözüm aralığı (Unix zaman damgaları).
    t_eval_unix: Sonuçların istendiği zaman noktaları (Unix zaman damgaları).
    k: Soğuma/ısınma katsayısı (1/saniye).
    T_ortam_series_times_unix: Ortam sıcaklığı için geçmiş zaman damgaları (Unix).
    T_ortam_series_values: Ortam sıcaklığı için geçmiş değerler.
    """
    if len(T_ortam_series_times_unix) < 1 or len(T_ortam_series_values) < 1 or \
       len(T_ortam_series_times_unix) != len(T_ortam_series_values):
        # print("ODE Çözümü: Geçersiz T_ortam serisi.")
        return None, None

    # Ortam sıcaklığını interpole etmek için bir fonksiyon oluştur.
    # Zaman damgaları sıralı ve benzersiz olmalı.
    sorted_indices = np.argsort(T_ortam_series_times_unix)
    t_ortam_sorted_unix = np.array(T_ortam_series_times_unix)[sorted_indices]
    val_ortam_sorted = np.array(T_ortam_series_values)[sorted_indices]

    unique_t_unix, unique_idx = np.unique(t_ortam_sorted_unix, return_index=True)
    unique_val_ortam = val_ortam_sorted[unique_idx]

    T_env_func_ref = None
    if len(unique_t_unix) < 2:
        # Yeterli farklı zaman noktası yoksa, son bilinen T_ortam'ı sabit olarak kullan.
        # print("ODE Çözümü: T_ortam için yetersiz farklı zaman noktası, son değer sabit kullanılacak.")
        last_T_env = unique_val_ortam[0] if len(unique_val_ortam) > 0 else 15.0 # Varsayılan T_ortam
        T_env_func_ref = lambda t_abs_unix: last_T_env 
    else:
        # interp1d, t_eval_unix aralığındaki zamanlar için T_ortam değerlerini tahmin edecek.
        # fill_value, t_eval_unix'in T_ortam_series_times_unix aralığının dışına çıkması durumunda kullanılır.
        T_env_interp_func = interp1d(unique_t_unix, unique_val_ortam, 
                                     kind='linear', # 'linear' veya 'nearest' daha güvenli olabilir
                                     bounds_error=False, 
                                     fill_value=(unique_val_ortam[0], unique_val_ortam[-1]))
        T_env_func_ref = lambda t_abs_unix: T_env_interp_func(t_abs_unix)

    # Model fonksiyonu: solve_ivp bu fonksiyonu çağıracak.
    # t_abs: solve_ivp tarafından sağlanan, t_span_unix aralığındaki mutlak Unix zaman damgası.
    # T_obj: Nesnenin o anki sıcaklığı.
    # k_coeff: Soğuma/ısınma katsayısı.
    # T_env_lookup_func: t_abs için T_ortam değerini döndüren fonksiyon.
    def newton_model(t_abs, T_obj, k_coeff, T_env_lookup_func):
        T_env_current = T_env_lookup_func(t_abs)
        return -k_coeff * (T_obj - T_env_current)

    try:
        sol = solve_ivp(
            newton_model, 
            t_span_unix, # (t_start_unix, t_end_unix)
            [T0],        # Başlangıç koşulu [T_nesne_baslangic]
            t_eval=t_eval_unix, # Sonuçların istendiği zamanlar (Unix timestamp)
            args=(k, T_env_func_ref), 
            method='RK45', 
            dense_output=False
        )

        if sol.success:
            return sol.t, sol.y[0] # sol.t (zaman), sol.y[0] (sıcaklık)
        else:
            # print(f"ODE Çözümü Başarısız: {sol.message}")
            return t_eval_unix, np.full_like(t_eval_unix, np.nan) # Başarısızsa NaN dizisi dön
    except Exception as e:
        # print(f"ODE solve_ivp sırasında hata: {e}")
        return t_eval_unix, np.full_like(t_eval_unix, np.nan)