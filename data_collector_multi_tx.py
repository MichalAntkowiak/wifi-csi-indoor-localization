import serial
import time
import csv
import os
import numpy as np

# =============================================================================
# KONFIGURACJA
# =============================================================================
SERIAL_PORT = 'COM9'
BAUD_RATE = 115200
DATASET_FILE = "csi_multi_tx_regression.csv"
SAMPLES_PER_POINT = 2500  # Około 12-15 sekund ciągłego pomiaru na jeden punkt

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"[COM] Połączono z {SERIAL_PORT}.")
except Exception as e:
    print(f"⚠️ Błąd portu: {e}")
    exit()

# Czyszczenie bufora startowego z ewentualnych śmieci po resecie
print("[SYS] Czyszczenie bufora szeregowego (0.5s)...")
ser.flushInput()
time.sleep(0.5)
ser.flushInput()

# =============================================================================
# FAZA 1: LIVE DISCOVERY MODE
# =============================================================================
print("\n[DISCOVERY] Szukam 3 nadajników. Rozstaw płytki po pokoju!")
print("Czekam na pakiety radiowe... (Naciśnij Ctrl+C aby przerwać)")

discovered_macs = set()
expected_len = None

try:
    while len(discovered_macs) < 3:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("CSI,"):
                parts = line.split(',')
                if len(parts) > 10:  
                    tx_mac = parts[1]
                    if tx_mac not in discovered_macs:
                        discovered_macs.add(tx_mac)
                        if expected_len is None:
                            expected_len = len(parts) - 2
                        print(f" -> 🎉 WYKRYTO: [ TX_{tx_mac} ] | Stan: {len(discovered_macs)}/3")

except KeyboardInterrupt:
    print("\n[SYS] Przerwano wyszukiwanie nadajników.")
    ser.close()
    exit()

tx_list = sorted(list(discovered_macs))
print(f"\n[OK] Sukces! Wszystkie 3 węzły aktywne: TX_A={tx_list[0]}, TX_B={tx_list[1]}, TX_C={tx_list[2]}")

# Inicjalizacja struktury pliku CSV
if not os.path.exists(DATASET_FILE):
    with open(DATASET_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        headers = []
        for tx in tx_list:
            headers += [f"tx_{tx}_sub_{i}" for i in range(expected_len)]
        headers += ["target_x", "target_y"]
        writer.writerow(headers)

current_room_state = {tx: [0.0]*expected_len for tx in tx_list}

# =============================================================================
# FAZA 2: KALIBRACJA
# =============================================================================
print("\n=== SYSTEM ROZPISYWANIA WSPÓŁRZĘDNYCH 2D ===")

try:
    while True:
        coords = input("\nWpisz pozycję jako X,Y (np. 2.5,4.0) lub 'q' aby wyjść: ").strip()
        if coords.lower() == 'q':
            break
            
        try:
            target_x, target_y = map(float, coords.split(','))
        except ValueError:
            print("⚠️ Błędny format! Wpisz współrzędne po przecinku, np: 0,0")
            continue
            
        print("Idź na miejsce! Odliczanie 10 sekund...")
        for i in range(9, 0, -1):
            time.sleep(1)
            print(f"{i}...")
            
        print(f"🔴 PRÓBKOWANIE POZYCJI X={target_x}m, Y={target_y}m... Stój nieruchomo.")
        
        samples_saved = 0
        while samples_saved < SAMPLES_PER_POINT:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("CSI,"):
                    parts = line.split(',')
                    try:
                        tx_mac = parts[1]
                        subcarrier_data = [float(x) for x in parts[2:]]
                        
                        if tx_mac in current_room_state and len(subcarrier_data) == expected_len:
                            current_room_state[tx_mac] = subcarrier_data
                            
                            if all(sum(current_room_state[tx]) > 0 for tx in tx_list):
                                combined_vector = []
                                for tx in tx_list:
                                    combined_vector += current_room_state[tx]
                                    
                                with open(DATASET_FILE, 'a', newline='') as f:
                                    writer = csv.writer(f)
                                    writer.writerow(combined_vector + [target_x, target_y])
                                
                                samples_saved += 1
                                if samples_saved % 50 == 0:
                                    print(f"  Zapisano {samples_saved}/{SAMPLES_PER_POINT} wektorów...")
                    except (ValueError, IndexError):
                        continue
                        
        print(f"✓ Pozycja X={target_x}, Y={target_y} zmapowana!")

except KeyboardInterrupt:
    print("\nZakończono zbieranie danych.")
finally:
    ser.close()
    print("Port COM zamknięty.")