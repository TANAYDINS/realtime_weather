# app/numerical_methods/integration.py
import numpy as np
from scipy.integrate import trapezoid as scipy_trapezoid, simpson as scipy_simpson

def trapezoidal_rule(y_values, x_values):
    """Verilen y ve x değerleri için trapez kuralı ile entegrasyon."""
    y_arr = np.array(y_values)
    x_arr = np.array(x_values)
    if len(y_arr) < 2 or len(x_arr) < 2 or len(y_arr) != len(x_arr):
        # print("Trapez kuralı için yetersiz veri.")
        return None 
    try:
        # SciPy'nin trapezoid fonksiyonu zaten sıralı olmayan x_values ile de çalışabilir
        # ancak genellikle sıralı olması beklenir.
        # Eğer sıralı değilse, çağıran yer sıralamalı.
        return scipy_trapezoid(y_arr, x_arr)
    except Exception as e:
        # print(f"Trapez entegrasyonunda hata: {e}")
        return None

def simpsons_rule(y_values, x_values):
    """Verilen y ve x değerleri için Simpson kuralı ile entegrasyon."""
    y_arr = np.array(y_values)
    x_arr = np.array(x_values)
    # Simpson kuralı için genellikle tek sayıda nokta (çift sayıda aralık) gerekir.
    if len(y_arr) < 3 or len(x_arr) < 3 or len(y_arr) != len(x_arr):
        # print("Simpson kuralı için yetersiz veri.")
        return None
    
    # SciPy'nin simpson fonksiyonu x_values parametresini de alır.
    # dx='avg' veya dx='trapz' seçenekleri de vardır eğer x_values verilmezse ve aralıklar farklıysa.
    try:
        return scipy_simpson(y_arr, x=x_arr)
    except Exception as e:
        # print(f"Simpson entegrasyonunda hata: {e}")
        return None