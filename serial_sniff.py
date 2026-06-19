# Prosty podgląd tego co odbiornik wysyła przez Serial
# Uruchom: python serial_sniff.py
# Zatrzymaj: Ctrl+C

import serial
import time

PORT = 'COM9'
BAUD = 115200

print(f"Łączę z {PORT}...")
try:
    # Otwieramy port COM
    ser = serial.Serial(PORT, BAUD, timeout=1)
    
    # KLUCZOWE ODBLOKOWANIE DTR/RTS DLA NATIVE USB ESP32-S3:
    ser.dtr = True
    ser.rts = True
    
    # Dajemy procesorowi 0.5 sekundy na przetworzenie sygnału startu
    time.sleep(0.5) 
    
    print(f"Połączono! Wyświetlam surowe dane przez 30 sekund...")
except Exception as e:
    print(f"BŁĄD: {e}")
    exit()

print("Połączono! Wyświetlam surowe dane przez 30 sekund...")
print("=" * 60)

start = time.time()
line_count = 0
csi_count = 0

while time.time() - start < 30:
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                line_count += 1
                if line.startswith('CSI'):
                    csi_count += 1
                    # Pokaż tylko pierwsze 80 znaków żeby nie zaśmiecać
                    print(f"[CSI #{csi_count}] {line[:80]}...")
                else:
                    print(f"[MSG] {line}")
        except:
            pass

print("=" * 60)
print(f"Łącznie linii: {line_count}")
print(f"Linii CSI:     {csi_count}")
ser.close()
