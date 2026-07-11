import os
import argparse
import numpy as np
import pandas as pd
from ml_engine import TrafficPredictor, TrafficClassifier, MLModelManager
from rl_agent import SemaforoRLAgent

def pretrain_models():
    print("=== INICIANDO PRE-ENTRENAMIENTO DE MODELOS ML ===")
    
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'aforo_vehicular.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} no encontrado. Ejecuta process_dataset.py primero.")
        return
        
    df = pd.read_csv(csv_path)
    print(f"Cargados {len(df)} registros para entrenamiento.")
    
    X = []
    y_reg = []
    
    for idx, row in df.iterrows():
        hour = row['hour']
        day = row['day_of_week']
        flow = row['total_flow']
        
        total = max(1.0, flow)
        auto_r = row['AUTOS'] / total
        pickup_r = row['PICK UP'] / total
        bus_r = row['BUS'] / total
        urban_r = row['SERVICIO DE TRANSP URBANO'] / total
        
        trucks = row['CAMION LIGERO'] + row['CAMION MEDIANO'] + row['CAMION PESADO'] + row['ARTICULADOS']
        trucks_r = trucks / total
        
        feat = [hour, day, flow, auto_r, pickup_r, bus_r, urban_r, trucks_r]
        X.append(feat)
        
        base_cong = (flow / 220.0) ** 1.4 * 70.0
        truck_impact = trucks_r * 30.0
        cong = base_cong + truck_impact
        cong += np.random.normal(0, 4)
        cong = min(100.0, max(0.0, cong))
        y_reg.append(cong)
        
    X = np.array(X, dtype=np.float32)
    y_reg = np.array(y_reg, dtype=np.float32)
    
    y_clf = []
    for c in y_reg:
        if c >= 65: y_clf.append(3)
        elif c >= 40: y_clf.append(2)
        elif c >= 18: y_clf.append(1)
        else: y_clf.append(0)
    y_clf = np.array(y_clf, dtype=np.int64)
    
    print("Entrenando regresor de congestión (RandomForest)...")
    predictor = TrafficPredictor()
    predictor.train(X, y_reg)
    
    print("Entrenando clasificador de nivel de tráfico (RandomForest)...")
    classifier = TrafficClassifier()
    classifier.train(X, y_clf)
    
    manager = MLModelManager(models_dir)
    manager.save_models(predictor, classifier)
    
    print("Pre-entrenando agente de semáforos RL (PyTorch DQN)...")
    agent = SemaforoRLAgent(state_dim=20, action_dim=7)
    
    np.random.seed(42)
    
    epochs = 15
    steps_per_epoch = 100
    
    print("Poblando Replay Buffer...")
    for _ in range(1000):
        sample_idx = np.random.randint(0, len(X))
        feat = X[sample_idx]
        hour, day, flow = feat[0], feat[1], feat[2]
        cong = y_reg[sample_idx]
        
        state = np.zeros(20, dtype=np.float32)
        state[0] = hour / 24.0
        state[1] = day / 6.0
        state[2] = cong / 100.0
        state[3] = flow / 300.0
        state[4] = (flow * 0.4) / 120.0
        state[5] = (cong * 0.1)
        state[6] = (flow * 0.4) / 100.0
        state[7] = (flow * 0.4) / 100.0
        state[8] = (flow * 0.2) / 100.0
        state[9] = state[5] * 0.4
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
        
    print(f"Replay Buffer poblado con {len(agent.buffer)} experiencias sintéticas.")
    
    print("Entrenando red DQN...")
    losses = []
    for epoch in range(epochs):
        epoch_losses = []
        for step in range(steps_per_epoch):
            loss = agent.train_step()
            if loss is not None:
                epoch_losses.append(loss)
        agent.update_epsilon()
        avg_loss = np.mean(epoch_losses) if epoch_losses else 0.0
        print(f"Epoch {epoch+1}/{epochs} - Loss promedio: {avg_loss:.5f} - Epsilon: {agent.epsilon:.3f}")
        
    rl_model_path = os.path.join(models_dir, 'dqn_semaforos.pt')
    agent.save(rl_model_path)
    print("Pre-entrenamiento finalizado con éxito.")

if __name__ == '__main__':
    pretrain_models()
