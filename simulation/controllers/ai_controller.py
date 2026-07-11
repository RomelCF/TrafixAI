# -*- coding: utf-8 -*-
"""
simulation/controllers/ai_controller.py
Controlador basado en Inteligencia Artificial y Machine Learning.
Contiene GestorMLTrafico (puente ML) y GestorIATrafico (controlador de desvíos y semáforos por RL/Reglas).
"""
import os
import sys
import json
import math
import random
import time
import numpy as np
from typing import List, Set, Dict, Tuple

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
backend_dir = os.path.join(root_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    import torch
    import joblib
    from ml_engine import TrafficPredictor, TrafficClassifier, MLModelManager
    from rl_agent import SemaforoRLAgent
    ML_LIBRARIES_AVAILABLE = True
except Exception as e:
    print(f"[AI Controller] Advertencia: Error cargando bibliotecas de ML ({e}). Usando modo heurístico.")
    ML_LIBRARIES_AVAILABLE = False

from simulation.road import Punto, Calle, DireccionCalle
from simulation.vehicle import TipoVehiculo, Vehiculo
from simulation.traffic_light import FaseSemaforo

class GestorMLTrafico:
    def __init__(self, is_angostura=False):
        self.is_angostura = is_angostura
        self.models_dir = os.path.join(backend_dir, 'ml_models')
        self.predictor = None
        self.classifier = None
        self.rl_agent = None
        
        if ML_LIBRARIES_AVAILABLE:
            try:
                self.manager = MLModelManager(self.models_dir)
                self.predictor, self.classifier = self.manager.load_models()
            except Exception as e:
                print(f"[ML] Error cargando modelos RandomForest: {e}")
                
            if self.predictor is None:
                self.predictor = TrafficPredictor()
            if self.classifier is None:
                self.classifier = TrafficClassifier()
                
            try:
                self.rl_agent = SemaforoRLAgent(state_dim=20, action_dim=7)
                rl_model_path = os.path.join(self.models_dir, 'dqn_semaforos.pt')
                self.rl_agent.load(rl_model_path)
            except Exception as e:
                print(f"[ML] Error cargando agente RL PyTorch: {e}")
        
        self.last_state = {}
        self.last_action = {}
        self.step_counter = 0
        self.last_prediction_probs = [0.25, 0.25, 0.25, 0.25]

    def obtener_features_globales(self, sim):
        hour = sim.hora_simulada
        day = 0
        
        vehs = sim.vehiculos
        total = len(vehs)
        
        if total == 0:
            return np.array([[hour, day, 0, 0.25, 0.25, 0.1, 0.1, 0.3]], dtype=np.float32)
            
        autos = sum(1 for v in vehs if getattr(v.tipo, 'name', '') in ['AUTO', 'TAXI'])
        pickups = sum(1 for v in vehs if getattr(v.tipo, 'name', '') == 'PICKUP')
        buses = sum(1 for v in vehs if getattr(v.tipo, 'name', '') == 'BUS')
        urbanos = sum(1 for v in vehs if getattr(v.tipo, 'name', '') in ['TRANSP_URBANO', 'COMBI'])
        trucks = sum(1 for v in vehs if getattr(v.tipo, 'name', '') in ['CAMION_LIGERO', 'CAMION_MEDIANO', 'CAMION_PESADO', 'ARTICULADOS', 'ARTICULADO'])
        
        auto_r = autos / total
        pickup_r = pickups / total
        bus_r = buses / total
        urban_r = urbanos / total
        trucks_r = trucks / total
        
        feat = [hour, day, float(total), auto_r, pickup_r, bus_r, urban_r, trucks_r]
        return np.array([feat], dtype=np.float32)

    def obtener_features_zona(self, sim, x1, y1, x2, y2):
        hour = sim.hora_simulada
        day = 0
        
        vehs = [v for v in sim.vehiculos if x1 <= v.posicion.x <= x2 and y1 <= v.posicion.y <= y2]
        total = len(vehs)
        
        if total == 0:
            return np.array([[hour, day, 0.0, 0.25, 0.25, 0.1, 0.1, 0.3]], dtype=np.float32)
            
        autos = sum(1 for v in vehs if getattr(v.tipo, 'name', '') in ['AUTO', 'TAXI'])
        pickups = sum(1 for v in vehs if getattr(v.tipo, 'name', '') == 'PICKUP')
        buses = sum(1 for v in vehs if getattr(v.tipo, 'name', '') == 'BUS')
        urbanos = sum(1 for v in vehs if getattr(v.tipo, 'name', '') in ['TRANSP_URBANO', 'COMBI'])
        trucks = sum(1 for v in vehs if getattr(v.tipo, 'name', '') in ['CAMION_LIGERO', 'CAMION_MEDIANO', 'CAMION_PESADO', 'ARTICULADOS', 'ARTICULADO'])
        
        auto_r = autos / total
        pickup_r = pickups / total
        bus_r = buses / total
        urban_r = urbanos / total
        trucks_r = trucks / total
        
        feat = [hour, day, float(total), auto_r, pickup_r, bus_r, urban_r, trucks_r]
        return np.array([feat], dtype=np.float32)

    def predecir_congestion(self, sim):
        if self.predictor is None or not ML_LIBRARIES_AVAILABLE:
            return 0.0
        feat = self.obtener_features_globales(sim)
        return float(self.predictor.predict(feat)[0])

    def predecir_congestion_zona(self, sim, x1, y1, x2, y2):
        if self.predictor is None or not ML_LIBRARIES_AVAILABLE:
            return 0.0
        feat = self.obtener_features_zona(sim, x1, y1, x2, y2)
        return float(self.predictor.predict(feat)[0])

    def clasificar_trafico(self, sim):
        if self.classifier is None or not ML_LIBRARIES_AVAILABLE:
            return 0
        feat = self.obtener_features_globales(sim)
        return self.classifier.predict(feat)[0]

    def clasificar_trafico_zona(self, sim, x1, y1, x2, y2):
        if self.classifier is None or not ML_LIBRARIES_AVAILABLE:
            return "Fluido"
        feat = self.obtener_features_zona(sim, x1, y1, x2, y2)
        pred = self.classifier.predict(feat)[0]
        mapping = {0: "Fluido", 1: "Moderado", 2: "Congestionado", 3: "Crítico"}
        return mapping.get(pred, "Fluido")

    def clasificar_probabilidades(self, sim):
        return self.last_prediction_probs

    def obtener_rl_state_semaforo(self, sim, semaforo):
        state = np.zeros(20, dtype=np.float32)
        state[0] = sim.hora_simulada / 24.0
        state[1] = 0.0
        
        globales = sim.gestor_metricas.calcular_metricas_globales()
        state[2] = globales.get("congestion_promedio", 0.0) / 100.0
        state[3] = len(sim.vehiculos) / 300.0
        state[4] = len(sim.vehiculos) / 120.0
        state[5] = globales.get("espera_promedio", 0.0) / 10.0
        
        cercanos = [v for v in sim.vehiculos if v.posicion.distancia_a(semaforo.posicion) < 150]
        
        v_vert = [v for v in cercanos if v.calle_actual.direccion == DireccionCalle.VERTICAL]
        v_horiz = [v for v in cercanos if v.calle_actual.direccion == DireccionCalle.HORIZONTAL]
        v_diag = [v for v in cercanos if v.calle_actual.direccion == DireccionCalle.DIAGONAL]
        
        state[6] = len(v_vert) / 30.0
        state[7] = len(v_horiz) / 30.0
        state[8] = len(v_diag) / 30.0
        
        state[9] = sum(v.tiempo_espera_acumulado for v in v_vert) / (max(1, len(v_vert)) * 600.0)
        state[10] = sum(v.tiempo_espera_acumulado for v in v_horiz) / (max(1, len(v_horiz)) * 600.0)
        state[11] = sum(v.tiempo_espera_acumulado for v in v_diag) / (max(1, len(v_diag)) * 600.0)
        
        # One-hot phase encoding: index from 0 to 7 based on phase Enum name
        phase_name = semaforo.fase.name
        phases = ["NORTE_SUR", "NORTE_SUR_AMARILLO", "ESTE_OESTE", "ESTE_OESTE_AMARILLO", 
                  "GIRO", "GIRO_AMARILLO", "PEATON", "PEATON_AMARILLO"]
        if phase_name in phases:
            idx = phases.index(phase_name)
            state[12 + idx] = 1.0
            
        return state

    def optimizar_semaforos_rl(self, sim):
        self.step_counter += 1
        
        if self.rl_agent is None or not ML_LIBRARIES_AVAILABLE:
            return
            
        if self.step_counter % 30 == 0:
            try:
                feat = self.obtener_features_globales(sim)
                self.last_prediction_probs = self.classifier.predict_probs(feat)
            except Exception as e:
                print(f"[ML] Error updating cached classification probabilities: {e}")
        
        for sem_idx, sem in enumerate(sim.semaforos):
            state = self.obtener_rl_state_semaforo(sim, sem)
            
            action = self.rl_agent.select_action(state)
            
            if action == 1:
                sem.duracion_norte_sur = min(40.0, sem.duracion_norte_sur + 2.0)
            elif action == 2:
                sem.duracion_norte_sur = max(5.0, sem.duracion_norte_sur - 2.0)
            elif action == 3:
                sem.duracion_este_oeste = min(40.0, sem.duracion_este_oeste + 2.0)
            elif action == 4:
                sem.duracion_este_oeste = max(5.0, sem.duracion_este_oeste - 2.0)
            elif action == 5:
                sem.duracion_giro = min(25.0, sem.duracion_giro + 1.5)
            elif action == 6:
                sem.duracion_giro = max(4.0, sem.duracion_giro - 1.5)
                
            if action != 0 and self.step_counter % 30 == 0:
                actions_desc = [
                    "Mantener tiempos", "Aumentar verde N-S", "Reducir verde N-S",
                    "Aumentar verde E-O", "Reducir verde E-O", "Aumentar verde Giro", "Reducir verde Giro"
                ]
                sim.ia_trafico._registrar_accion(f"RL: {actions_desc[action]} en Semáforo {sem_idx+1}")
                
            sem_key = f"sem_{sem_idx}"
            if sem_key in self.last_state:
                prev_state = self.last_state[sem_key]
                prev_action = self.last_action[sem_key]
                
                globales = sim.gestor_metricas.calcular_metricas_globales()
                cong = globales.get("congestion_promedio", 0.0)
                wait = globales.get("espera_promedio", 0.0)
                reward = -(cong * 0.4 + wait * 0.6)
                
                self.rl_agent.buffer.push(prev_state, prev_action, reward, state, False)
                
            self.last_state[sem_key] = state
            self.last_action[sem_key] = action
            
            sem.actualizar()
            
        if self.step_counter % 150 == 0:
            import threading
            threading.Thread(target=self.rl_agent.train_step, daemon=True).start()
            self.rl_agent.update_epsilon()

class GestorIATrafico:
    """IA para detectar congestión, recomendar medidas, desviar autos y optimizar semáforos."""

    def __init__(self, simulacion, is_angostura: bool = False):
        self.sim = simulacion
        self.is_angostura = is_angostura
        self.recomendaciones: List[str] = []
        self.metricas_zona: Dict[str, dict] = {}
        self.contador_actualizacion = 0
        
        self.zonas_con_ingreso_reducido: Set[str] = set()
        self.zonas_con_desvio_activo: Set[str] = set()
        self.log_acciones: List[str] = []
        self._cache_semaforo: Dict[int, bool] = {}
        
        self.zonas = {}
        self.capacidades = {}
        
        config_path = os.path.join(root_dir, "data", "escenarios.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                escenarios = json.load(f)
            key = "angostura" if is_angostura else "centro_historico"
            if key in escenarios:
                zonas_config = escenarios[key]["zonas"]
                for nombre, datos in zonas_config.items():
                    self.zonas[nombre] = tuple(datos["box"])
                    self.capacidades[nombre] = datos["capacidad"]
            print(f"[IA] Configuración cargada con éxito para {key} desde escenarios.json.")
        except Exception as e:
            print(f"[IA] Error cargando escenarios.json: {e}. Usando valores por defecto.")
            if is_angostura:
                SX = 1600 / 1200
                SY = 1000 / 568
                self.zonas = {
                    "Calle 1":   (0, int(370*SY), 1600, int(568*SY)),
                    "Calle 2":   (int(480*SX), int(200*SY), int(1100*SX), int(360*SY)),
                    "Calle 3-4": (int(430*SX), int(140*SY), int(830*SX), int(520*SY)),
                    "Calle 5-6": (int(900*SX), int(300*SY), int(1160*SX), int(568*SY)),
                    "Zona Norte":(int(730*SX), 0, int(830*SX), int(260*SY)),
                }
                self.capacidades = {"Calle 1": 30.0, "Calle 2": 20.0, "Calle 3-4": 15.0, "Calle 5-6": 15.0, "Zona Norte": 10.0}
            else:
                self.zonas = {
                    "Centro histórico": (350, 250, 850, 700),
                    "San Pedro": (0, 620, 420, 900),
                    "San Blas": (650, 40, 1120, 320),
                    "Eje Av. El Sol": (0, 340, 1600, 470),
                    "Zona Este": (900, 300, 1600, 900),
                }
                self.capacidades = {"Centro histórico": 25.0, "San Pedro": 15.0, "San Blas": 12.0, "Eje Av. El Sol": 30.0, "Zona Este": 30.0}

        self.ml_bridge = GestorMLTrafico(is_angostura=is_angostura)

    def actualizar(self):
        """Analiza la red cada ciertos frames y aplica acciones automáticas."""
        self.contador_actualizacion += 1
        if self.contador_actualizacion % 30 != 0:
            return
        
        self.metricas_zona = self._calcular_metricas_zona()
        
        if not self.sim.ia_activa:
            self.zonas_con_ingreso_reducido.clear()
            self.zonas_con_desvio_activo.clear()
            self.recomendaciones = ["Modo Sin IA activo: Semáforos y rutas estándar."]
            return
            
        self.recomendaciones = self._generar_recomendaciones()
        
        if self.ml_bridge is not None and ML_LIBRARIES_AVAILABLE:
            self.ml_bridge.optimizar_semaforos_rl(self.sim)
        else:
            self._optimizar_semaforos()

        self._reducir_ingreso_vehicular()
        self._aplicar_desvio_rutas()
        self._priorizar_transporte_publico()

    def _vehiculo_detenido_por_semaforo(self, vehiculo: Vehiculo) -> bool:
        """Devuelve True si el vehículo está parado esperando una fase no habilitada para su dirección."""
        vid = id(vehiculo)
        cachedado = self._cache_semaforo.get(vid)
        if cachedado is not None:
            return cachedado

        if hasattr(self.sim, '_semaforos_cercanos'):
            candidatos = self.sim._semaforos_cercanos(vehiculo.posicion, 70)
        else:
            candidatos = self.sim.semaforos
        for semaforo in candidatos:
            dir_calle = vehiculo.calle_actual.direccion
            fase = semaforo.fase
            if dir_calle == DireccionCalle.VERTICAL and fase == FaseSemaforo.NORTE_SUR:
                continue
            if dir_calle == DireccionCalle.HORIZONTAL and fase == FaseSemaforo.ESTE_OESTE:
                continue
            if dir_calle == DireccionCalle.DIAGONAL and fase == FaseSemaforo.GIRO:
                continue
            dist = vehiculo.posicion.distancia_a(semaforo.posicion)
            if dist < 70:
                self._cache_semaforo[vid] = True
                return True
        self._cache_semaforo[vid] = False
        return False

    def _calcular_metricas_zona(self) -> Dict[str, dict]:
        metricas = {}
        for nombre, (x1, y1, x2, y2) in self.zonas.items():
            vehiculos = [
                v for v in self.sim.vehiculos
                if x1 <= v.posicion.x <= x2 and y1 <= v.posicion.y <= y2
            ]
            total = len(vehiculos)
            cap = self.capacidades.get(nombre, 20.0)
            
            semaforos_en_zona = [s for s in self.sim.semaforos if x1 <= s.posicion.x <= x2 and y1 <= s.posicion.y <= y2]
            num_semaforos = len(semaforos_en_zona)
            
            if total == 0:
                metricas[nombre] = {
                    "vehiculos": 0,
                    "velocidad": 0.0,
                    "detenidos": 0,
                    "congestion": 0.0,
                    "nivel": "Fluido",
                    "densidad_vehicular": 0.0,
                    "detenidos_ratio": 0.0,
                    "lentos_ratio": 0.0,
                    "tiempo_espera_ratio": 0.0,
                    "saturacion_ratio": 0.0,
                    "explicacion": "tránsito fluido",
                    "sugerencia": "monitorear ciclos"
                }
                continue

            velocidad_promedio = sum(v.velocidad_actual for v in vehiculos) / total
            densidad_vehicular = min(100.0, (total / cap) * 100.0)
            
            detenidos = sum(
                1 for v in vehiculos
                if v.velocidad_actual < 0.2 and not self._vehiculo_detenido_por_semaforo(v)
            )
            detenidos_ratio = (detenidos / total) * 100.0

            lentos = sum(
                1 for v in vehiculos
                if v.velocidad_actual < v.velocidad_maxima * 0.45
                and not (self._vehiculo_detenido_por_semaforo(v) and v.tiempo_espera_acumulado <= 360)
            )
            lentos_ratio = (lentos / total) * 100.0

            avg_espera_frames = sum(v.tiempo_espera_acumulado for v in vehiculos) / total
            tiempo_espera_ratio = min(100.0, (avg_espera_frames / 600.0) * 100.0)

            veh_esperando_sem = sum(1 for v in vehiculos if self._vehiculo_detenido_por_semaforo(v))
            saturacion_ratio = min(100.0, (veh_esperando_sem / max(1.0, num_semaforos)) * 50.0)

            if self.ml_bridge is not None and ML_LIBRARIES_AVAILABLE and self.sim.ia_activa:
                try:
                    congestion = self.ml_bridge.predecir_congestion_zona(self.sim, x1, y1, x2, y2)
                    nivel = self.ml_bridge.clasificar_trafico_zona(self.sim, x1, y1, x2, y2)
                except Exception as e:
                    print(f"[ML] Fallback a reglas por error: {e}")
                    congestion, nivel = self._calcular_congestion_reglas(
                        densidad_vehicular, detenidos_ratio, lentos_ratio, 
                        tiempo_espera_ratio, saturacion_ratio, total, velocidad_promedio
                    )
            else:
                congestion, nivel = self._calcular_congestion_reglas(
                    densidad_vehicular, detenidos_ratio, lentos_ratio, 
                    tiempo_espera_ratio, saturacion_ratio, total, velocidad_promedio
                )

            factores = []
            if densidad_vehicular > 45:
                factores.append("acumulación de vehículos")
            if lentos_ratio > 50:
                factores.append("baja velocidad")
            if saturacion_ratio > 35:
                factores.append("semáforo mal sincronizado")
            if tiempo_espera_ratio > 35:
                factores.append("tiempo de espera excesivo")
            if total > cap * 0.8:
                factores.append("exceso de ingreso vehicular")

            if not factores:
                factores.append("retenciones menores")

            explicacion = ", ".join(factores[:-1]) + " y " + factores[-1] if len(factores) > 1 else factores[0]
            sugerencia = "ampliar verde 8s y desviar autos" if nivel == "Crítico" else (
                "ampliar verde 5s y sugerir rutas" if nivel == "Congestionado" else "monitorear ciclos"
            )

            metricas[nombre] = {
                "vehiculos": total,
                "velocidad": velocidad_promedio,
                "detenidos": detenidos,
                "congestion": congestion,
                "nivel": nivel,
                "densidad_vehicular": densidad_vehicular,
                "detenidos_ratio": detenidos_ratio,
                "lentos_ratio": lentos_ratio,
                "tiempo_espera_ratio": tiempo_espera_ratio,
                "saturacion_ratio": saturacion_ratio,
                "explicacion": explicacion,
                "sugerencia": sugerencia
            }
        return metricas

    def _calcular_congestion_reglas(self, dens, det_r, len_r, esp_r, sat_r, total, vel_prom):
        congestion = (dens * 0.30 + det_r * 0.25 + len_r * 0.20 + esp_r * 0.15 + sat_r * 0.10)
        factor_escala = min(1.0, total / 3.0)
        congestion = min(100.0, max(0.0, congestion * factor_escala))
        
        if congestion >= 65 and total >= 4:
            nivel = "Crítico"
        elif congestion >= 40 or (total >= 4 and vel_prom < 0.6):
            nivel = "Congestionado"
        elif congestion >= 18 or vel_prom < 1.5:
            nivel = "Moderado"
        else:
            nivel = "Fluido"
        return congestion, nivel

    def _generar_recomendaciones(self) -> List[str]:
        recomendaciones = []
        for zona, datos in self.metricas_zona.items():
            nivel = datos.get("nivel", "Fluido")
            if nivel in ("Crítico", "Congestionado"):
                explicacion = datos.get("explicacion", "retenciones")
                sug = datos.get("sugerencia", "monitorear ciclos")
                recomendaciones.append(f"{zona}: {nivel} por {explicacion}. Acción: {sug}.")

        vel_global = self.sim.estadisticas.get("promedio_velocidad", 0)
        if vel_global < 0.8 and len(self.sim.vehiculos) > 20:
            recomendaciones.append("Red global lenta por baja velocidad general. Acción: habilitar ondas verdes.")

        if not recomendaciones:
            nom_zona = "Angostura" if self.is_angostura else "Cusco"
            recomendaciones.append(f"Tránsito {nom_zona} estable: monitoreando zonas de análisis.")
        return recomendaciones[:4]

    def _optimizar_semaforos(self):
        """Ajusta tiempos de semáforo por fase según congestión local por carril/dirección por reglas."""
        from simulation.controllers.adaptive_controller import AdaptiveController
        adapt = AdaptiveController(self.sim.semaforos)
        adapt.actualizar(self.sim)

    def _registrar_accion(self, texto: str):
        self.log_acciones.insert(0, texto)
        self.log_acciones = self.log_acciones[:5]

    def _reducir_ingreso_vehicular(self):
        anteriores = set(self.zonas_con_ingreso_reducido)
        self.zonas_con_ingreso_reducido = set()

        for nombre, datos in self.metricas_zona.items():
            if datos["nivel"] in ("Crítico", "Congestionado") and datos["vehiculos"] >= 4:
                self.zonas_con_ingreso_reducido.add(nombre)
                if nombre not in anteriores:
                    self._registrar_accion(f"IA: Ingreso reducido en {nombre}")

        for nombre in anteriores - self.zonas_con_ingreso_reducido:
            self._registrar_accion(f"IA: Ingreso normalizado en {nombre}")

    def _calle_en_zona_critica(self, calle: Calle) -> bool:
        puntos = [calle.inicio, calle.fin]
        for nombre in self.zonas_con_desvio_activo:
            x1, y1, x2, y2 = self.zonas[nombre]
            for p in puntos:
                if x1 <= p.x <= x2 and y1 <= p.y <= y2:
                    return True
        return False

    def _aplicar_desvio_rutas(self):
        anteriores = set(self.zonas_con_desvio_activo)
        self.zonas_con_desvio_activo = set()

        for nombre, datos in self.metricas_zona.items():
            if datos["nivel"] == "Crítico":
                self.zonas_con_desvio_activo.add(nombre)
                if nombre not in anteriores:
                    self._registrar_accion(f"IA: Desvio activo en {nombre}")

        for nombre in anteriores - self.zonas_con_desvio_activo:
            self._registrar_accion(f"IA: Desvio cancelado en {nombre}")

        if not self.zonas_con_desvio_activo:
            return

        desviados = 0
        for vehiculo in self.sim.vehiculos:
            idx_sig = vehiculo.indice_ruta + 1
            if idx_sig >= len(vehiculo.ruta):
                continue
            prox_calle = vehiculo.ruta[idx_sig]
            if self._calle_en_zona_critica(prox_calle):
                calle_origen = vehiculo.calle_actual
                calle_destino = vehiculo.ruta[-1]
                
                from simulation.intersection import obtener_ruta_inteligente
                nueva_ruta_restante = obtener_ruta_inteligente(self.sim, calle_origen, calle_destino, 'evita_ia', vehiculo.tipo)
                if len(nueva_ruta_restante) > 1:
                    vehiculo.ruta = vehiculo.ruta[:vehiculo.indice_ruta] + nueva_ruta_restante
                    desviados += 1

        if desviados > 0:
            self._registrar_accion(f"IA: {desviados} veh. desviados de zonas críticas")
            self.sim.stats_con_ia['vehiculos_desviados'] += desviados

    def _priorizar_transporte_publico(self):
        FASES_ROJO = {
            FaseSemaforo.ESTE_OESTE,
            FaseSemaforo.ESTE_OESTE_AMARILLO,
            FaseSemaforo.GIRO,
            FaseSemaforo.GIRO_AMARILLO,
            FaseSemaforo.PEATON,
            FaseSemaforo.PEATON_AMARILLO,
        }
        
        public_types = (TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO) if self.is_angostura else (TipoVehiculo.COMBI, TipoVehiculo.TAXI)
        
        for semaforo in self.sim.semaforos:
            if semaforo.fase not in FASES_ROJO:
                continue

            transporte_publico = [
                v for v in self.sim.vehiculos
                if v.tipo in public_types
                and v.posicion.distancia_a(semaforo.posicion) < 80
                and v.velocidad_actual < 0.3
            ]
            if not transporte_publico:
                continue

            en_zona_critica = any(
                x1 <= semaforo.posicion.x <= x2 and y1 <= semaforo.posicion.y <= y2
                for nombre, (x1, y1, x2, y2) in self.zonas.items()
                if self.metricas_zona.get(nombre, {}).get("nivel") in ("Crítico", "Congestionado")
            )
            if en_zona_critica:
                semaforo.duracion_norte_sur = min(35.0, semaforo.duracion_norte_sur + 0.3)
                semaforo.duracion_este_oeste = min(35.0, semaforo.duracion_este_oeste + 0.3)

    def _evaluar_impacto_predictivo(self) -> List[dict]:
        evaluaciones = []
        if self.is_angostura:
            conexiones = {"Calle 1": "Calle 2", "Calle 2": "Calle 3-4",
                          "Calle 3-4": "Calle 5-6", "Calle 5-6": "Zona Norte", "Zona Norte": "Límite"}
        else:
            conexiones = {
                "Centro histórico": "Eje Av. El Sol",
                "San Pedro": "Eje Av. El Sol",
                "San Blas": "Centro histórico",
                "Eje Av. El Sol": "Zona Este",
                "Zona Este": "Límite Ciudad (Salida)"
            }

        for nombre, (x1, y1, x2, y2) in self.zonas.items():
            datos = self.metricas_zona.get(nombre, {})
            nivel = datos.get("nivel", "Fluido")
            if nivel not in ("Crítico", "Congestionado"):
                continue
                
            vehiculos = [
                v for v in self.sim.vehiculos
                if x1 <= v.posicion.x <= x2 and y1 <= v.posicion.y <= y2
            ]
            total = len(vehiculos)
            if total == 0:
                continue
                
            det_en_zona = datos.get("detenidos", 0)
            lentos_en_zona = sum(1 for v in vehiculos if v.velocidad_actual < v.velocidad_maxima * 0.45)
            veh_esperando_sem = sum(1 for v in vehiculos if self._vehiculo_detenido_por_semaforo(v))
            
            public_types = (TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO) if self.is_angostura else (TipoVehiculo.COMBI, TipoVehiculo.TAXI)
            combis_taxis = sum(1 for v in vehiculos if v.tipo in public_types and v.velocidad_actual < 0.3)
            vehiculos_secundarios = sum(1 for v in vehiculos if v.calle_actual.tipo in ('secundaria', 'empedrada'))
            
            t_aumento = 8.0 if nivel == "Crítico" else 5.0
            mejora_vel_sem = min(30.0, 5.0 + 1.8 * veh_esperando_sem)
            
            zona_siguiente = conexiones.get(nombre, "Límite")
            if zona_siguiente != "Límite":
                congestion_sig = self.metricas_zona.get(zona_siguiente, {}).get("congestion", 0.0)
                riesgo_desborde_val = min(25.0, 2.0 + 0.6 * veh_esperando_sem + 0.1 * congestion_sig)
                desborde_txt = f"{zona_siguiente} (+{riesgo_desborde_val:.1f}%)"
            else:
                desborde_txt = "Bajo (Salida)"
                
            bloqueo_sec_txt = "Riesgo Alto" if vehiculos_secundarios >= 3 else ("Riesgo Moderado" if vehiculos_secundarios >= 1 else "Riesgo Bajo")
            transporte_txt = f"Favorable (+{combis_taxis} uds)" if combis_taxis >= 2 else ("Favorable (+1 ud)" if combis_taxis >= 1 else "Neutro")
                
            evaluaciones.append({
                "zona": nombre,
                "accion": f"Verde +{int(t_aumento)}s en semáforos",
                "mejora_vel": f"+{mejora_vel_sem:.1f}%",
                "desborde": desborde_txt,
                "bloqueo_sec": bloqueo_sec_txt,
                "transporte": transporte_txt,
                "color_transporte": (100, 255, 120) if "Favorable" in transporte_txt else (200, 200, 200),
                "color_desborde": (255, 100, 100) if "Eje" in desborde_txt or "Centro" in desborde_txt or "Calle" in desborde_txt else (150, 210, 255)
            })
            
            mejora_vel_desv = min(25.0, 4.0 + 1.2 * det_en_zona + 0.3 * lentos_en_zona)
            riesgo_desborde_desv = min(20.0, 3.0 + 0.5 * (total - det_en_zona))
            desborde_desv_txt = f"Alternas (+{riesgo_desborde_desv:.1f}%)"
            bloqueo_sec_desv_txt = "Bajo (Angostura)" if self.is_angostura else "Bajo (Dijkstra)"
            transporte_desv_txt = "Muy Favorable" if combis_taxis >= 1 else "Neutro"
                
            evaluaciones.append({
                "zona": nombre,
                "accion": "Desviar autos particulares",
                "mejora_vel": f"+{mejora_vel_desv:.1f}%",
                "desborde": desborde_desv_txt,
                "bloqueo_sec": bloqueo_sec_desv_txt,
                "transporte": transporte_desv_txt,
                "color_transporte": (100, 255, 120) if "Favorable" in transporte_desv_txt else (200, 200, 200),
                "color_desborde": (255, 200, 100)
            })
            
        return evaluaciones

    def dibujar_zonas(self, pantalla):
        from simulation.render import dibujar_zonas
        dibujar_zonas(pantalla, self)

    def dibujar_panel(self, pantalla):
        from simulation.render import dibujar_panel
        dibujar_panel(pantalla, self)
