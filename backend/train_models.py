# -*- coding: utf-8 -*-
import os
import sys
import numpy as np

# Asegurar que el directorio backend esté en el path
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from ml_engine import (
    TrafficPredictor, TrafficClassifier, MLModelManager,
    cargar_datos_entrenamiento
)
from rl_agent import SemaforoRLAgent


def pretrain_models():
    print("=== INICIANDO PRE-ENTRENAMIENTO DE MODELOS ML ===")

    models_dir = os.path.join(_BACKEND_DIR, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)

    # ── 1. Cargar datos desde aforo_vehicular.csv ──────────────────────────────
    # El CSV fue generado a partir del Excel de aforo vehicular de Cusco
    # (conteo vehicular real por tipo de vehículo, hora y día de semana)
    # usando process_dataset.py.  La función cargar_datos_entrenamiento() lo lee,
    # filtra filas vacías y construye los arrays de features/etiquetas.
    print("Cargando datos desde data/aforo_vehicular.csv ...")
    X, y_reg, y_clf = cargar_datos_entrenamiento()

    if X is None:
        print("ERROR: No se pudo cargar data/aforo_vehicular.csv.")
        print("  Ejecuta process_dataset.py apuntando al Excel de aforo para generarlo.")
        return

    print(f"  {len(X)} muestras cargadas (filas con total_flow > 0).")
    print(f"  Distribucion de niveles => Fluido:{(y_clf==0).sum()}  "
          f"Moderado:{(y_clf==1).sum()}  "
          f"Congestionado:{(y_clf==2).sum()}  "
          f"Critico:{(y_clf==3).sum()}")

    # ── 2. Entrenar RandomForest Regresor (predictor de congestión) ────────────
    print("\nEntrenando predictor de congestión (RandomForest Regressor)...")
    predictor = TrafficPredictor()
    predictor.train(X, y_reg)
    print("  Predictor entrenado.")

    # ── 3. Entrenar RandomForest Clasificador (nivel de tráfico) ──────────────
    print("Entrenando clasificador de nivel de tráfico (RandomForest Classifier)...")
    classifier = TrafficClassifier()
    classifier.train(X, y_clf)
    print("  Clasificador entrenado.")

    # ── 4. Guardar modelos Scikit-learn ────────────────────────────────────────
    manager = MLModelManager(models_dir)
    manager.save_models(predictor, classifier)

    # ── 5. Pre-entrenar agente RL DQN ──────────────────────────────────────────
    print("\nPre-entrenando agente de semáforos RL (PyTorch DQN)...")
    agent = SemaforoRLAgent(state_dim=20, action_dim=7)
    np.random.seed(42)

    # Poblar replay buffer con experiencias sintéticas basadas en el CSV real
    print("Poblando Replay Buffer con datos del aforo vehicular...")
    for i in range(min(1000, len(X))):
        idx  = np.random.randint(0, len(X))
        feat = X[idx]
        hour, day, flow = feat[0], feat[1], feat[2]
        cong = float(y_reg[idx])

        state = np.zeros(20, dtype=np.float32)
        state[0] = hour / 24.0
        state[1] = day  / 6.0
        state[2] = cong / 100.0
        state[3] = flow / 300.0
        state[4] = (flow * 0.4) / 120.0
        state[5] = (cong * 0.1)
        state[6] = (flow * 0.4) / 100.0
        state[7] = (flow * 0.4) / 100.0
        state[8] = (flow * 0.2) / 100.0
        state[9]  = state[5] * 0.4
        state[10] = state[5] * 0.4
        state[11] = state[5] * 0.2
        phase = np.random.randint(0, 8)
        state[12 + phase] = 1.0

        action = np.random.randint(0, 7)

        next_cong = cong
        if action in [1, 3, 5]:
            next_cong = max(0.0, cong - np.random.uniform(1, 6))
        elif action in [2, 4, 6]:
            next_cong = min(100.0, cong + np.random.uniform(0, 4))

        next_state = state.copy()
        next_state[2] = next_cong / 100.0
        next_state[3] = max(0.0, flow - (cong - next_cong) * 0.5) / 300.0

        reward = -(next_cong * 0.5 + next_state[5] * 10.0 * 0.5)
        agent.buffer.push(state, action, reward, next_state, False)

    print(f"  Replay Buffer: {len(agent.buffer)} experiencias.")

    print("Entrenando red DQN...")
    epochs = 15
    steps_per_epoch = 100
    for epoch in range(epochs):
        epoch_losses = []
        for _ in range(steps_per_epoch):
            loss = agent.train_step()
            if loss is not None:
                epoch_losses.append(loss)
        agent.update_epsilon()
        avg_loss = np.mean(epoch_losses) if epoch_losses else 0.0
        print(f"  Epoch {epoch+1}/{epochs} — Loss: {avg_loss:.5f}  Epsilon: {agent.epsilon:.3f}")

    rl_model_path = os.path.join(models_dir, 'dqn_semaforos.pt')
    agent.save(rl_model_path)
    print("\nPre-entrenamiento finalizado con éxito.")


if __name__ == '__main__':
    pretrain_models()
