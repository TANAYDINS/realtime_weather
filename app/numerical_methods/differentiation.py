# app/numerical_methods/differentiation.py
import numpy as np

def central_difference(y_values, x_values):
    """Merkezi fark yöntemi ile türev hesabı."""
    y_arr = np.array(y_values)
    x_arr = np.array(x_values)

    if len(y_arr) < 3 or len(x_arr) < 3 or len(y_arr) != len(x_arr):
        # print("Merkezi fark için yetersiz veri noktası.")
        return np.array([])
    
    # NumPy'nin gradient fonksiyonu, uç noktalar için ileri/geri fark,
    # iç noktalar için merkezi fark kullanır.
    # x_arr parametresi, x koordinatlarını belirtir ve eşit olmayan aralıklarla çalışır.
    try:
        derivatives = np.gradient(y_arr, x_arr)
    except Exception as e:
        # print(f"Türev hesaplamada hata: {e}")
        return np.array([])
    return derivatives

def forward_difference(y_values, x_values):
    """İleri fark yöntemi."""
    y_arr = np.array(y_values)
    x_arr = np.array(x_values)

    if len(y_arr) < 2 or len(x_arr) < 2 or len(y_arr) != len(x_arr):
        return np.array([])
    
    try:
        dy = np.diff(y_arr)
        dx = np.diff(x_arr)
        if np.any(dx == 0): # Sıfıra bölme hatasını önle
            # print("Uyarı: dx değerleri arasında sıfır var, türev hesaplanamıyor.")
            # Bu durumda uygun bir strateji belirlemek gerekir, örn: NaN döndürmek.
            # Şimdilik sorunlu yerlere NaN atayalım.
            derivatives = np.full_like(dx, np.nan, dtype=float)
            non_zero_dx_indices = dx != 0
            derivatives[non_zero_dx_indices] = dy[non_zero_dx_indices] / dx[non_zero_dx_indices]
        else:
            derivatives = dy / dx
        # Son nokta için türev hesaplanamadığından, diziyi orijinal y_values ile aynı boyuta getirmek için
        # sonuna bir NaN ekleyebiliriz.
        return np.append(derivatives, np.nan)
    except Exception as e:
        # print(f"İleri fark hesaplamada hata: {e}")
        return np.array([])


def backward_difference(y_values, x_values):
    """Geri fark yöntemi."""
    y_arr = np.array(y_values)
    x_arr = np.array(x_values)

    if len(y_arr) < 2 or len(x_arr) < 2 or len(y_arr) != len(x_arr):
        return np.array([])
    
    try:
        dy = np.diff(y_arr)
        dx = np.diff(x_arr)
        if np.any(dx == 0):
            # print("Uyarı: dx değerleri arasında sıfır var, türev hesaplanamıyor.")
            derivatives = np.full_like(dx, np.nan, dtype=float)
            non_zero_dx_indices = dx != 0
            derivatives[non_zero_dx_indices] = dy[non_zero_dx_indices] / dx[non_zero_dx_indices]
        else:
            derivatives = dy / dx
        # İlk nokta için türev hesaplanamadığından, diziyi orijinal y_values ile aynı boyuta getirmek için
        # başına bir NaN ekleyebiliriz.
        return np.insert(derivatives, 0, np.nan)
    except Exception as e:
        # print(f"Geri fark hesaplamada hata: {e}")
        return np.array([])