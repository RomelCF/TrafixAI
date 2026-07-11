# -*- coding: utf-8 -*-
"""
simulation/metrics.py
Gestor de Métricas e Indicadores Clave de Desempeño (KPIs) de Tráfico.
"""
import os
import json
import time
from typing import Dict, List

class GestorMetricas:
    def __init__(self, simulacion):
        self.sim = simulacion
        self.historial: List[dict] = []
        
        self.kpi_metadata = {}
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kpis.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.kpi_metadata = json.load(f)
            print("[Métricas] Metadatos de KPIs cargados con éxito desde kpis.json.")
        except Exception as e:
            print(f"[Métricas] Error cargando kpis.json: {e}. Usando metadatos de fallback.")
            self.kpi_metadata = {
                "velocidad_promedio": {"nombre": "Velocidad Promedio", "descripcion": "Velocidad media", "unidad": "km/h", "umbrales": {"critico": 5.0, "alerta": 15.0}},
                "congestion_global": {"nombre": "Congestión Global", "descripcion": "Porcentaje de congestión", "unidad": "%", "umbrales": {"critico": 70.0, "alerta": 40.0}},
                "tiempo_espera_promedio": {"nombre": "Tiempo de Espera Promedio", "descripcion": "Espera media", "unidad": "s", "umbrales": {"critico": 60.0, "alerta": 30.0}},
                "nivel_servicio": {"nombre": "Nivel de Servicio", "descripcion": "LOS", "unidad": "LOS", "umbrales": {"critico": "F", "alerta": "D"}},
                "efectividad_semaforos": {"nombre": "Efectividad de Semáforos", "descripcion": "Efectividad", "unidad": "%", "umbrales": {"critico": 40.0, "alerta": 65.0}},
                "emisiones_co2_estimadas": {"nombre": "Emisiones de CO2", "descripcion": "CO2", "unidad": "kg/h", "umbrales": {"critico": 15.0, "alerta": 8.0}},
                "throughput": {"nombre": "Throughput", "descripcion": "Throughput", "unidad": "veh/min", "umbrales": {"critico": 2.0, "alerta": 5.0}}
            }

    def calcular_metricas_globales(self) -> dict:
        vehiculos = self.sim.vehiculos
        total_veh = len(vehiculos)
        if total_veh == 0:
            return {
                "total_vehiculos": 0,
                "velocidad_promedio": 0.0,
                "detenidos": 0,
                "espera_promedio": 0.0,
                "congestion_promedio": 0.0,
                "emisiones_co2_estimadas": 0.0,
                "efectividad_semaforos": 100.0
            }
            
        vel_prom = sum(v.velocidad_actual for v in vehiculos) / total_veh
        
        detenidos = sum(
            1 for v in vehiculos 
            if v.velocidad_actual < 0.2 and not self.sim.ia_trafico._vehiculo_detenido_por_semaforo(v)
        )
        
        espera_prom = sum(v.tiempo_espera_acumulado for v in vehiculos) / total_veh / 60.0
        congestion_prom = self.sim.estadisticas.get("congestion", 0.0)
        
        co2_total = sum(0.05 if v.velocidad_actual < 0.2 else 0.02 for v in vehiculos)
        
        stats = self.sim.stats_con_ia if self.sim.ia_activa else self.sim.stats_sin_ia
        t_mov = stats.get('tiempo_movimiento_total', 0)
        t_sem = stats.get('tiempo_espera_semaforo', 0)
        efectividad = 100.0 * t_mov / max(1.0, t_mov + t_sem)
        
        return {
            "total_vehiculos": total_veh,
            "velocidad_promedio": vel_prom,
            "detenidos": detenidos,
            "espera_promedio": espera_prom,
            "congestion_promedio": congestion_prom,
            "emisiones_co2_estimadas": co2_total,
            "efectividad_semaforos": efectividad
        }

    def calcular_metricas_por_zona(self) -> dict:
        return self.sim.ia_trafico._calcular_metricas_zona()

    def calcular_kpis(self) -> Dict[str, dict]:
        """Calcula el estado actual de los KPIs con sus unidades y umbrales correspondientes."""
        globales = self.calcular_metricas_globales()
        
        espera_s = globales["espera_promedio"] * 60.0
        if espera_s < 10.0:
            los = "A"
        elif espera_s < 20.0:
            los = "B"
        elif espera_s < 35.0:
            los = "C"
        elif espera_s < 55.0:
            los = "D"
        elif espera_s < 80.0:
            los = "E"
        else:
            los = "F"
            
        stats = self.sim.stats_con_ia if self.sim.ia_activa else self.sim.stats_sin_ia
        completed = stats.get('vehiculos_completados', 0)
        frames = max(1, stats.get('frames', 1))
        minutos = frames / 3600.0
        throughput = completed / max(0.1, minutos)
        
        co2_kg_h = globales["emisiones_co2_estimadas"] * 3.6
        
        vel_km_h = globales["velocidad_promedio"] * 12.0
        
        kpi_values = {
            "velocidad_promedio": vel_km_h,
            "congestion_global": globales["congestion_promedio"],
            "tiempo_espera_promedio": espera_s,
            "nivel_servicio": los,
            "efectividad_semaforos": globales["efectividad_semaforos"],
            "emisiones_co2_estimadas": co2_kg_h,
            "throughput": throughput
        }
        
        kpis_result = {}
        for key, meta in self.kpi_metadata.items():
            val = kpi_values.get(key, 0.0)
            
            state = "Normal"
            if key == "nivel_servicio":
                if val in ("E", "F"):
                    state = "Crítico"
                elif val == "D":
                    state = "Alerta"
            else:
                crit = meta["umbrales"]["critico"]
                alert = meta["umbrales"]["alerta"]
                
                if key in ("congestion_global", "tiempo_espera_promedio", "emisiones_co2_estimadas"):
                    if val >= crit:
                        state = "Crítico"
                    elif val >= alert:
                        state = "Alerta"
                else:
                    if val <= crit:
                        state = "Crítico"
                    elif val <= alert:
                        state = "Alerta"
                        
            kpis_result[key] = {
                "nombre": meta["nombre"],
                "descripcion": meta["descripcion"],
                "unidad": meta["unidad"],
                "valor": val,
                "estado": state,
                "umbrales": meta["umbrales"]
            }
            
        return kpis_result

    def guardar_historial(self):
        timestamp = time.time()
        metricas_g = self.calcular_metricas_globales()
        try:
            metricas_z = self.calcular_metricas_por_zona()
        except Exception:
            metricas_z = {}
            
        self.historial.append({
            "timestamp": timestamp,
            "globales": metricas_g,
            "zonas": metricas_z
        })
