## Ewolucja projektu i przebieg prac

### 1. Pierwsze odebrane fale CSI
Pierwsze testy transmisji i parsowania surowych podnośnych CSI przesyłanych przez port szeregowy z mikrokontrolera ESP32 do skryptu wizualizacyjnego w Pythonie.

<p align="center">
  <img src="images/01_pierwsze_fale.jpg" width="600" alt="Pierwsze fale CSI"><br>
  <em>Rys. 1: Pierwsze pakiety CSI odebrane i wyrysowane w czasie rzeczywistym.</em>
</p>

---

### 2. Zsynchronizowany strumień danych
Optymalizacja bufora szeregowego (`ser.read(ser.in_waiting)`), co pozwoliło na uzyskanie stabilnego, ciągłego odczytu podnośnych z częstotliwością ~100 Hz bez gubienia pakietów.

<p align="center">
  <img src="images/02_strumien_zsynchronizowany.png" width="600" alt="Zsynchronizowany strumień CSI"><br>
  <em>Rys. 2: Stabilny strumień podnośnych po zsynchronizowaniu transmisji.</em>
</p>

---

### 3. Pierwsze widoczne amplitudy podczas przechodzenia pomiędzy płytkami
Rejestracja fizycznego tłumienia fal przez ciało człowieka. Przejście na linii wzroku (Line of Sight) między nadajnikiem TX a odbiornikiem RX powoduje wyraźny spadek amplitudy sygnału, co posłużyło jako podstawa do klasyfikacji strefowej (np. Biurko vs Kanapa).

<p align="center">
  <img src="images/03_amplitudy_przechodzenie.png" width="600" alt="Tłumienie sygnału przy ruchu"><br>
  <em>Rys. 3: Wyraźny spadek amplitudy podczas przecięcia linii fal oraz wczesny moduł klasyfikacji strefowej.</em>
</p>

---

### 4. Trenowanie modelu uczenia maszynowego
Proces uczenia pierwszego modelu klasyfikacji na zebranym zbiorze danych pomiarowych wraz z analizą macierzy pomyłek (Confusion Matrix) oraz raportem metryk (Precision / Recall).

<p align="center">
  <img src="images/04_trenowanie_ai.png" width="600" alt="Trenowanie modelu AI"><br>
  <em>Rys. 4: Raport trenowania modelu na bazie próbek kalibracyjnych.</em>
</p>

---

### 5. Wielowęzłowy układ współrzędnych 2D
Rozbudowa systemu do konfiguracji z wieloma nadajnikami (Multi-TX) oraz przejście z klasyfikacji strefowej na ciągłą regresję współrzędnych kartezjańskich (X, Y).

<p align="center">
  <img src="images/05_radar_wielowezlowy.png" width="450" alt="Wielowęzłowy radar 2D"><br>
  <em>Rys. 5: Testy pozycjonowania 2D z wykorzystaniem fuzji danych z wielu węzłów.</em>
</p>

---

### 6. Finalny projekt: Pasywny radar 2D w pokoju 1.6m x 4.6m
Ostateczna wersja systemu integrująca fuzję danych z 3 nadajników ESP32, normalizację wektora cech L2, model KNN oraz dwuwymiarowy filtr Kalmana tłumiący szumy wielodrogowości.

<p align="center">
  <img src="images/06_finalny_projekt.png" width="400" alt="Finalny projekt radaru 2D"><br>
  <em>Rys. 6: Finalny radar 2D śledzący pozycję człowieka na żywo w zdefiniowanym obszarze pokoju.</em>
</p>
