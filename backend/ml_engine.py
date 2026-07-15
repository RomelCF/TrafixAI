import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Ruta al CSV de aforo vehicular real (datos de Cusco)
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CSV_PATH = os.path.join(_ROOT_DIR, 'data', 'aforo_vehicular.csv')

def _calcular_congestion_desde_flujo(flow, trucks_r):
    """Fórmula de congestión calibrada con los datos de aforo vehicular real de Cusco."""
    base_cong = (flow / 220.0) ** 1.4 * 70.0
    truck_impact = trucks_r * 30.0
    cong = base_cong + truck_impact
    return float(min(100.0, max(0.0, cong)))

def _nivel_desde_congestion(cong):
    """Umbrales de nivel de tráfico para el entrenamiento del RandomForest.

    Calibrados para ser coherentes con la guardia de fila física:
    el RF solo debe predecir Congestionado/Crítico cuando el flujo
    del aforo real justifica una fila de vehículos (alta densidad).
    """
    if cong >= 75:
        return 3   # Crítico   — flujo muy saturado
    elif cong >= 55:
        return 2   # Congestionado — flujo denso con potencial de fila
    elif cong >= 35:
        return 1   # Moderado   — flujo elevado pero fluido
    return 0       # Fluido     — circulación normal

def cargar_datos_entrenamiento():
    """
    Lee data/aforo_vehicular.csv (generado a partir del Excel de aforo de Cusco
    con process_dataset.py) y construye arrays X, y_reg, y_clf listos para
    entrenar los modelos RandomForest.

    El CSV contiene columnas reales de conteo vehicular por tipo:
        hour, day_of_week, total_flow, AUTOS, PICK UP, BUS,
        SERVICIO DE TRANSP URBANO, CAMION LIGERO, CAMION MEDIANO,
        CAMION PESADO, ARTICULADOS

    Retorna (X, y_reg, y_clf) o (None, None, None) si el CSV no existe.
    """
    if not os.path.exists(_CSV_PATH):
        return None, None, None

    df = pd.read_csv(_CSV_PATH)
    # Filtrar filas sin flujo (cero vehiculos en ese intervalo)
    df = df[df['total_flow'] > 0].copy()

    if len(df) < 10:
        return None, None, None

    X_list, y_reg_list = [], []
    for _, row in df.iterrows():
        hour     = float(row['hour'])
        day      = float(row['day_of_week'])
        flow     = float(row['total_flow'])
        total    = max(1.0, flow)

        auto_r   = float(row['AUTOS'])   / total
        pickup_r = float(row['PICK UP']) / total
        bus_r    = float(row['BUS'])     / total
        urban_r  = float(row['SERVICIO DE TRANSP URBANO']) / total
        trucks   = (float(row['CAMION LIGERO'])  +
                    float(row['CAMION MEDIANO']) +
                    float(row['CAMION PESADO'])  +
                    float(row['ARTICULADOS']))
        trucks_r = trucks / total

        feat = [hour, day, flow, auto_r, pickup_r, bus_r, urban_r, trucks_r]
        X_list.append(feat)

        # Etiqueta de congestión calculada con la misma fórmula de train_models.py
        cong = _calcular_congestion_desde_flujo(flow, trucks_r)
        # Añadir pequeño ruido para variabilidad (igual que train_models.py)
        cong = float(np.clip(cong + np.random.normal(0, 4), 0.0, 100.0))
        y_reg_list.append(cong)

    X     = np.array(X_list,  dtype=np.float32)
    y_reg = np.array(y_reg_list, dtype=np.float32)
    y_clf = np.array([_nivel_desde_congestion(c) for c in y_reg], dtype=np.int64)

    return X, y_reg, y_clf


class TrafficPredictor:
    """Regresor RandomForest que predice el porcentaje de congestión (0-100)."""
    def __init__(self):
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestRegressor(n_estimators=100, random_state=42, max_depth=8))
        ])
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def train_from_csv(self):
        """
        Entrena el predictor usando data/aforo_vehicular.csv.
        Éste es el CSV generado a partir del Excel de aforo vehicular de Cusco
        (conteo vehicular por tipo, hora y día de semana).
        """
        X, y_reg, _ = cargar_datos_entrenamiento()
        if X is not None:
            self.train(X, y_reg)
            return True
        return False

    def predict(self, features):
        if not self.is_trained:
            # Fallback: heurística basada en flujo total (features[0][2])
            total_flow = features[0][2] if len(features) > 0 else 0
            trucks_r   = features[0][7] if len(features[0]) > 7 else 0.1
            return np.array([_calcular_congestion_desde_flujo(total_flow, trucks_r)])

        pred = self.model.predict(features)
        return np.clip(pred, 0.0, 100.0)


class TrafficClassifier:
    """Clasificador RandomForest que predice el nivel de tráfico."""
    CLASSES = ["Fluido", "Moderado", "Congestionado", "Crítico"]

    def __init__(self):
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=6))
        ])
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def train_from_csv(self):
        """
        Entrena el clasificador usando data/aforo_vehicular.csv.
        Éste es el CSV generado a partir del Excel de aforo vehicular de Cusco.
        Los niveles de clase se derivan de la misma fórmula de congestión que
        usa el sistema de reglas (ai_controller._calcular_congestion_reglas).
        """
        X, _, y_clf = cargar_datos_entrenamiento()
        if X is not None:
            self.train(X, y_clf)
            return True
        return False

    def predict(self, features):
        """Devuelve lista de strings con el nivel de tráfico predicho."""
        if not self.is_trained:
            # Fallback coherente con _calcular_congestion_reglas
            total_flow = features[0][2] if len(features) > 0 else 0
            trucks_r   = features[0][7] if len(features[0]) > 7 else 0.1
            cong = _calcular_congestion_desde_flujo(total_flow, trucks_r)
            nivel_idx  = _nivel_desde_congestion(cong)
            return [self.CLASSES[nivel_idx]]

        pred_indices = self.model.predict(features)
        return [self.CLASSES[int(i)] for i in pred_indices]

    def predict_probs(self, features):
        if not self.is_trained:
            return [0.25, 0.25, 0.25, 0.25]
        return self.model.predict_proba(features)[0].tolist()


class MLModelManager:
    def __init__(self, models_dir=None):
        if models_dir is None:
            self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml_models')
        else:
            self.models_dir = models_dir

        os.makedirs(self.models_dir, exist_ok=True)
        self.predictor_path  = os.path.join(self.models_dir, 'predictor_congestion.pkl')
        self.classifier_path = os.path.join(self.models_dir, 'classifier_traffic.pkl')

    def save_models(self, predictor, classifier):
        joblib.dump(predictor, self.predictor_path)
        joblib.dump(classifier, self.classifier_path)
        print("Modelos Scikit-learn guardados con éxito.")

    def load_models(self):
        predictor  = None
        classifier = None

        if os.path.exists(self.predictor_path):
            try:
                predictor = joblib.load(self.predictor_path)
                print("Predictor Scikit-learn cargado.")
            except Exception as e:
                print(f"Error cargando predictor: {e}")

        if os.path.exists(self.classifier_path):
            try:
                classifier = joblib.load(self.classifier_path)
                print("Clasificador Scikit-learn cargado.")
            except Exception as e:
                print(f"Error cargando clasificador: {e}")

        return predictor, classifier
