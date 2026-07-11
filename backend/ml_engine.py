import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

class TrafficPredictor:
    def __init__(self):
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestRegressor(n_estimators=100, random_state=42, max_depth=8))
        ])
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, features):
        if not self.is_trained:
            total_flow = features[0][2] if len(features) > 0 else 0
            return float(min(100.0, (total_flow / 200.0) * 100.0))
            
        pred = self.model.predict(features)
        return np.clip(pred, 0.0, 100.0)

class TrafficClassifier:
    def __init__(self):
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=6))
        ])
        self.classes = ["Fluido", "Moderado", "Congestionado", "Crítico"]
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, features):
        if not self.is_trained:
            total_flow = features[0][2] if len(features) > 0 else 0
            cong = min(100.0, (total_flow / 200.0) * 100.0)
            if cong >= 65: return "Crítico"
            elif cong >= 40: return "Congestionado"
            elif cong >= 18: return "Moderado"
            return "Fluido"
            
        pred_idx = self.model.predict(features)
        return [self.classes[int(i)] for i in pred_idx]

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
        self.predictor_path = os.path.join(self.models_dir, 'predictor_congestion.pkl')
        self.classifier_path = os.path.join(self.models_dir, 'classifier_traffic.pkl')

    def save_models(self, predictor, classifier):
        joblib.dump(predictor, self.predictor_path)
        joblib.dump(classifier, self.classifier_path)
        print("Modelos Scikit-learn guardados con éxito.")

    def load_models(self):
        predictor = None
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
