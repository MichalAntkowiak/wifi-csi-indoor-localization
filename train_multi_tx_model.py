import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import r2_score

DATASET_FILE = "csi_multi_tx_regression.csv"
MODEL_FILE = "csi_multi_tx_model.pkl"

if not os.path.exists(DATASET_FILE):
    print(f"⚠️ Błąd: Brak pliku {DATASET_FILE} w bieżącym folderze!")
    exit()

# Wczytanie danych z Twojego pomiaru (55 000 wierszy)
df = pd.read_csv(DATASET_FILE).dropna()
print(f"[INFO] Dane wczytane pomyślnie. Rozmiar matrycy: {df.shape}")

# Separacja cech (192 podnośne) oraz celów (X i Y)
X = df.drop(columns=['target_x', 'target_y']).values
y = df[['target_x', 'target_y']].values

# MATEMATYCZNA NORMALIZACJA L2 (Przeliczenie bezwzględnych amplitud na geometryczny kształt fali)
norms = np.linalg.norm(X, axis=1, keepdims=True)
norms[norms == 0] = 1  # Zabezpieczenie przed dzieleniem przez zero
X_normalized = X / norms

# Podział na zbiór treningowy i testowy
X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.2, random_state=42)

print("🧠 Trenuję odporny model KNN na znormalizowanych profilach radiowych...")
# 15 sąsiadów z wagami dystansowymi idealnie interpoluje pozycję w małej przestrzeni
model = KNeighborsRegressor(n_neighbors=15, weights='distance', metric='euclidean')
model.fit(X_train, y_train)

# Ewaluacja dokładności mapowania
y_pred = model.predict(X_test)
print("\n==================================================")
print(f"🎯 DOKŁADNOŚĆ MAPOWANIA KSZTAŁTU FAL: {r2_score(y_test, y_pred) * 100:.2f}%")
print("==================================================")

# Zapisanie "mózgu" radaru
with open(MODEL_FILE, 'wb') as f:
    pickle.dump(model, f)
print(f"💾 Model KNN zapisany jako: '{MODEL_FILE}'")