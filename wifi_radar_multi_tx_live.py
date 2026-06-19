import serial
import time
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# =============================================================================
# KLASA DWUWYMIAROWEGO FILTRU KALMANA (KINEMATYKA RUCHU)
# =============================================================================
class KalmanFilter2D:
    def __init__(self, dt=0.033, process_noise=0.05, measurement_noise=2):
        """
        Wektor stanu x = [pozycja_x, pozycja_y, predkosc_x, predkosc_y]^T
        """
        # Startujemy na środku pokoju (0.8m, 2.3m) z zerową prędkością
        self.x = np.array([[0.8], [2.3], [0.0], [0.0]])
        
        # Macierz przejścia stanu (Fizyka: pos = pos + v * dt)
        self.A = np.array([[1, 0, dt, 0],
                           [0, 1, 0, dt],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]])
        
        # Macierz pomiaru (Interesują nas tylko pozycje X i Y z modelu KNN)
        self.H = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0]])
        
        # Kovariancja szumu procesu (Jak bardzo pozwalamy kropce przyspieszać)
        self.Q = np.eye(4) * process_noise
        
        # Kovariancja szumu pomiaru (Jak bardzo nie ufamy skokom fal radiowych KNN)
        self.R = np.eye(2) * measurement_noise
        
        # Macierz niepewności początkowej
        self.P = np.eye(4) * 1.0

    def filter_step(self, z_x, z_y):
        # 1. KROK PREDYKCJI (Gdzie kropka POWINNA być według praw fizyki)
        self.x = np.dot(self.A, self.x)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        
        # 2. KROK KOREKTY (Zderzenie teorii z szorstką radiową rzeczywistością KNN)
        z = np.array([[z_x], [z_y]])
        y = z - np.dot(self.H, self.x)  # Innowacja (błąd wektora)
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        
        # Wzmocnienie Kalmana (K) - decyduje komu bardziej ufamy: fizyce czy antenom
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        
        # Aktualizacja stanu
        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(np.dot(K, self.H), self.P)
        
        # Zwracamy odszumione współrzędne X, Y
        return float(self.x[0][0]), float(self.x[1][0])

# =============================================================================
# KONFIGURACJA ZGODNA Z TWOIM SPRZĘTEM
# =============================================================================
SERIAL_PORT = 'COM9'
BAUD_RATE = 115200
MODEL_FILE = "csi_multi_tx_model.pkl"

MAC_ADDRESSES = ['30:30:F9:19:B1:68', '30:30:F9:5A:07:E0', '84:FC:E6:67:93:E0']

# Wstępne wygładzanie surowego wektora podnośnych na antenie
ALPHA_FEATURES = 0.25  

if not os.path.exists(MODEL_FILE):
    print(f"⚠️ Błąd: Brak pliku modelu {MODEL_FILE}! Najpierw odpal trening.")
    exit()

with open(MODEL_FILE, 'rb') as f:
    model = pickle.load(f)
print("[ML] Model załadowany. Inicjalizacja filtrów kinematycznych...")

# Inicjalizacja Filtru Kalmana (dt = 33ms, bo pętla chodzi w ~30 FPS)
# Wyższe measurement_noise (np. 1.2) = kropka stabilniejsza, bardziej "przyklejona"
kalman = KalmanFilter2D(dt=0.033, process_noise=0.03, measurement_noise=1.1)

EXPECTED_FEATURES_PER_TX = 64  
current_data = {mac: None for mac in MAC_ADDRESSES}
packet_counts = {mac: 0 for mac in MAC_ADDRESSES}  
smoothed_features = None  

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    ser.dtr = True
    ser.rts = True
    print(f"[COM] Połączono z portem {SERIAL_PORT}. Aktywowano Filtr Kalmana 2D.")
    ser.flushInput()
except Exception as e:
    print(f"⚠️ Błąd portu COM: {e}")
    exit()

# =============================================================================
# INTERFEJS GRAFICZNY (POKÓJ 1.6m x 4.6m)
# =============================================================================
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(6, 9)) 
fig.patch.set_facecolor('#111111')
ax.set_facecolor('#0a0a1a')

ax.set_xlim(-0.5, 2.1)
ax.set_ylim(-0.5, 5.1)
ax.set_title("Radar Radiowy CSI + Filtr Kalmana 2D", fontsize=12, color='white', pad=15)
ax.set_aspect('equal')
ax.grid(color='#223344', linestyle='--', linewidth=0.5)

room_rect = mpatches.FancyBboxPatch((0, 0), 1.6, 4.6, boxstyle="square,pad=0", linewidth=2.0, edgecolor='#00aaff', facecolor='none', alpha=0.6)
ax.add_patch(room_rect)

presence_dot, = ax.plot([], [], 'o', color='#00ffcc', markersize=24, zorder=10, markeredgecolor='#ffffff', markeredgewidth=1.5)
status_text = ax.text(0.8, 4.8, 'Kalman 2D: Stabilizacja...', color='#00ffcc', fontsize=10, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#334455'))

last_update = time.time()
serial_buffer = ""

# =============================================================================
# PĘTLA GŁÓWNA ŚLEDZENIA REAL-TIME
# =============================================================================
try:
    while True:
        waiting_bytes = ser.in_waiting
        if waiting_bytes > 0:
            raw_data = ser.read(waiting_bytes)
            serial_buffer += raw_data.decode('utf-8', errors='ignore')
            
            if '\n' in serial_buffer:
                lines = serial_buffer.split('\n')
                serial_buffer = lines[-1]
                
                for line in lines[:-1]:
                    line = line.strip()
                    if line.startswith("CSI,"):
                        parts = line.split(',')
                        if len(parts) > 3:
                            mac = parts[1].strip()
                            if mac in current_data:
                                try:
                                    subcarriers = [float(x) for x in parts[2:]]
                                    if len(subcarriers) == EXPECTED_FEATURES_PER_TX:
                                        current_data[mac] = subcarriers
                                        packet_counts[mac] += 1  
                                except ValueError:
                                    continue

        if time.time() - last_update > 0.033:
            all_nodes_ready = all(v is not None for v in current_data.values())
            
            if all_nodes_ready:
                raw_features = []
                for mac in MAC_ADDRESSES:
                    raw_features.extend(current_data[mac])
                
                if smoothed_features is None:
                    smoothed_features = np.array(raw_features)
                else:
                    smoothed_features = ALPHA_FEATURES * np.array(raw_features) + (1 - ALPHA_FEATURES) * smoothed_features
                
                # Normalizacja profilu geometrycznego L2
                norm = np.linalg.norm(smoothed_features)
                X_live = np.array([smoothed_features / norm if norm > 0 else smoothed_features])
                
                # Surowy, skaczący odczyt z modelu KNN
                prediction = model.predict(X_live)[0]
                z_x, z_y = prediction[0], prediction[1]
                
                # Przepuszczenie surowego punktu przez Filtr Kalmana
                x_stable, y_stable = kalman.filter_step(z_x, z_y)
                
                # Ograniczenie kropki, by fizycznie nie wyleciała poza ściany pokoju
                x_stable = max(0.0, min(1.6, x_stable))
                y_stable = max(0.0, min(4.6, y_stable))
                
                presence_dot.set_xdata([x_stable])
                presence_dot.set_ydata([y_stable])
                msg = f"👤 POZYCJA: X={x_stable:.2f}m, Y={y_stable:.2f}m"
            else:
                msg = "⚠️ SYNC ERROR: Czekam na komplet wezlow..."
            
            status_text.set_text(msg)
            p_status = ", ".join([f"TX_{i+1}={packet_counts[mac]}" for i, mac in enumerate(MAC_ADDRESSES)])
            print(f"[RADAR] {msg} | {p_status}      ", end="\r")
                
            try:
                plt.pause(0.001)
            except Exception:
                break
            last_update = time.time()
            
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n[SYS] Zatrzymano radar.")
finally:
    ser.close()