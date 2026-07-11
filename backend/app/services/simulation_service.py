# -*- coding: utf-8 -*-
"""
backend/app/services/simulation_service.py
Servicio para administrar el ciclo de vida y la ejecución headless de las simulaciones.
Contiene la clase EjecutorSimulacion e instancias de ejecución global.
"""
import os
import sys
import threading
import time
import ctypes
import pygame
import numpy as np
from PIL import Image

try:
    ctypes.windll.winmm.timeBeginPeriod(1)
except Exception:
    pass

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from simulation import (
    TipoVehiculo, FaseSemaforo, DireccionCalle
)
from simulation.engine import (
    SimulacionTrafico, SimulacionAngostura, _HeadlessCentro
)
from simulation.cusco_engine import ANCHO, ALTO, FPS
from simulation.angostura_engine import ANCHO as ANCHO_A, ALTO as ALTO_A, FPS as FPS_A

class EjecutorSimulacion:
    def __init__(self, sim_cls, ancho: int, alto: int, fps: int,
                 tipo_veh_cls, nombres_intersecciones: list[str],
                 sim_speed: float = 1.5):
        self._sim_cls   = sim_cls
        self._ancho     = ancho
        self._alto      = alto
        self._fps       = fps
        self._tipo_veh  = tipo_veh_cls
        self._nombres_int = nombres_intersecciones

        self._lock  = threading.Lock()
        self._frame_lock = threading.Lock()
        self._sim   = None
        self._screen = None
        self._running = False
        self._paused  = False
        self._thread: threading.Thread | None = None
        self._frame_bytes: bytes = b""
        self._raw_frame_rgb: bytes = b""
        self._clientes_activos = 0
        self._frame_index = 0
        self._sim_speed = sim_speed
        self._dirty = True
        self._history: list = []
        self._max_history = 300
        self._render_interval = 1.0 / 30.0
        self._last_render_time = 0.0

    def incrementar_clientes(self):
        self._clientes_activos += 1
        self._dirty = True

    def decrementar_clientes(self):
        self._clientes_activos = max(0, self._clientes_activos - 1)

    def tiene_clientes_activos(self) -> bool:
        return self._clientes_activos > 0

    def obtener_raw_frame(self) -> tuple[bytes, int]:
        with self._frame_lock:
            return self._raw_frame_rgb, self._frame_index

    def iniciar(self):
        pygame.init()
        self._screen = pygame.Surface((self._ancho, self._alto))
        self._sim    = self._sim_cls()
        self._sim.pantalla = self._screen
        self._running = True
        self._thread  = threading.Thread(target=self._bucle, daemon=True)
        self._thread.start()

    def detener(self):
        self._running = False

    def aplicar_control(self, accion: str):
        if accion == "restart":
            nueva_sim = self._sim_cls()
            nueva_sim.pantalla = self._screen
            with self._lock:
                if self._sim is None:
                    return
                self._sim = nueva_sim
                self._history.clear()
                self._paused = False
            print(f"[Runner] Simulación reiniciada: {self._sim_cls.__name__}")
            return

        with self._lock:
            if self._sim is None:
                return
            if accion == "pause":
                self._paused = True
            elif accion == "resume":
                self._paused = False
            elif accion == "toggle_ai":
                self._sim.ia_activa = not self._sim.ia_activa
                if not self._sim.ia_activa:
                    for sem in self._sim.semaforos:
                        sem.restaurar_original()
                    self._sim.ia_trafico.zonas_con_ingreso_reducido.clear()
                    self._sim.ia_trafico.zonas_con_desvio_activo.clear()
                    self._sim.ia_trafico._registrar_accion("IA: Desactivada por usuario")
                else:
                    self._sim.ia_trafico._registrar_accion("IA: Activada por usuario")
            elif accion == "fast_forward":
                self._sim.hora_simulada = (self._sim.hora_simulada + 1.0) % 24.0
            elif accion == "benchmark":
                self._sim.benchmark_activo = True
                self._sim.benchmark_fase = 1
                self._sim.ia_activa = False
                self._sim.benchmark_frames_restantes = self._sim.benchmark_frames_fase
                self._sim.vehiculos.clear()
                if hasattr(self._sim, '_sync_indice_vehiculos'):
                    self._sim._sync_indice_vehiculos()
                self._sim.vehiculos_generados = 0
                for k in list(self._sim.estadisticas.keys()):
                    self._sim.estadisticas[k] = 0
                for stats in [self._sim.stats_sin_ia, self._sim.stats_con_ia]:
                    for k in list(stats.keys()):
                        stats[k] = 0
                for sem in self._sim.semaforos:
                    sem.restaurar_original()
                self._sim.ia_trafico.zonas_con_ingreso_reducido.clear()
                self._sim.ia_trafico.zonas_con_desvio_activo.clear()
                if hasattr(self._sim.ia_trafico, 'log_acciones'):
                    self._sim.ia_trafico.log_acciones.clear()
                self._sim.ia_trafico._registrar_accion("IA: Benchmark - Iniciando Escenario 1 (Sin IA): 0/1000 pasos")
                self._paused = False
            elif accion == "cancel_benchmark":
                self._sim.benchmark_activo = False
                self._sim.benchmark_fase = 0
                self._sim.benchmark_frames_restantes = 0
                self._sim.ia_activa = True
                for sem in self._sim.semaforos:
                    sem.restaurar_original()
                self._sim.ia_trafico.zonas_con_ingreso_reducido.clear()
                self._sim.ia_trafico.zonas_con_desvio_activo.clear()
                self._sim.ia_trafico._registrar_accion("IA: Benchmark cancelado por el usuario")
                print(f"[Runner] Benchmark cancelado para {self._sim_cls.__name__}")

    def obtener_bytes_frame(self) -> bytes:
        with self._lock:
            return self._frame_bytes

    def obtener_metricas(self) -> dict:
        with self._lock:
            if self._sim is None:
                return {}
            return self._construir_metricas()

    def obtener_historial(self) -> list:
        with self._lock:
            return list(self._history)

    def obtener_kpis(self) -> dict:
        with self._lock:
            if self._sim is None:
                return {}
            return self._sim.gestor_metricas.calcular_kpis()

    def obtener_semaforos(self) -> list:
        with self._lock:
            if self._sim is None:
                return []
            semaforos_data = []
            now = time.time()
            for idx, sem in enumerate(self._sim.semaforos):
                restante = max(0.0, sem.tiempo_cambio - now)
                semaforos_data.append({
                    "id": idx,
                    "posicion": {"x": sem.posicion.x, "y": sem.posicion.y},
                    "tipo": sem.tipo,
                    "fase": sem.fase.name,
                    "fases_ciclo": [f.name for f in sem.fases_ciclo],
                    "duracion_norte_sur": sem.duracion_norte_sur,
                    "duracion_este_oeste": sem.duracion_este_oeste,
                    "duracion_giro": sem.duracion_giro,
                    "duracion_peaton": sem.duracion_peaton,
                    "tiempo_restante": round(restante, 2)
                })
            return semaforos_data

    def esta_ia_activa(self) -> bool:
        with self._lock:
            return self._sim.ia_activa if self._sim else True

    def esta_pausado(self) -> bool:
        return self._paused

    def _bucle(self):
        frame_count  = 0
        last_hist_ts = time.time()
        last_tick_ts = time.time()
        ancho_stream = self._ancho // 2
        alto_stream  = self._alto  // 2
        time_step = 1.0 / (self._fps * self._sim_speed)
        max_catchup = 8
        accumulator = 0.0

        while self._running:
            try:
                now = time.time()
                elapsed = now - last_tick_ts
                last_tick_ts = now
                accumulator += elapsed

                if not self._paused and self._sim:
                    steps = 0
                    with self._lock:
                        while accumulator >= time_step and steps < max_catchup:
                            self._sim.paso()
                            self._dirty = True
                            accumulator -= time_step
                            steps += 1

                            if getattr(self._sim, 'benchmark_activo', False):
                                self._sim.benchmark_frames_restantes -= 1

                                completados = self._sim.benchmark_frames_fase - self._sim.benchmark_frames_restantes
                                if completados % 200 == 0 and 0 < completados < self._sim.benchmark_frames_fase:
                                    f_nom = "Escenario 1 (Sin IA)" if self._sim.benchmark_fase == 1 else "Escenario 2 (Con IA)"
                                    self._sim.ia_trafico._registrar_accion(f"IA: Benchmark - {f_nom}: {completados}/1000 pasos")

                                if self._sim.benchmark_frames_restantes <= 0:
                                    if self._sim.benchmark_fase == 1:
                                        self._sim.benchmark_fase = 2
                                        self._sim.ia_activa = True
                                        self._sim.benchmark_frames_restantes = self._sim.benchmark_frames_fase
                                        self._sim.vehiculos.clear()
                                        if hasattr(self._sim, '_sync_indice_vehiculos'):
                                            self._sim._sync_indice_vehiculos()
                                        self._sim.vehiculos_generados = 0
                                        for k in list(self._sim.estadisticas.keys()):
                                            self._sim.estadisticas[k] = 0
                                        self._sim.ia_trafico._registrar_accion("IA: Benchmark - Iniciando Escenario 2 (Con IA): 0/1000 pasos")
                                        print(f"[Runner] Benchmark: Fase 2 (Con IA) para {self._sim_cls.__name__}")
                                    elif self._sim.benchmark_fase == 2:
                                        self._sim.benchmark_activo = False
                                        self._sim.benchmark_fase = 3
                                        self._paused = True
                                        self._sim.ia_trafico._registrar_accion("IA: Benchmark finalizado. Escenarios 1 y 2 completados al 100% (1000/1000)")
                                        print(f"[Runner] Benchmark completado para {self._sim_cls.__name__}. Resultados listos.")

                    if accumulator > time_step * max_catchup:
                        accumulator = time_step * max_catchup

                frame_count += 1

                if (self._clientes_activos > 0 and self._sim
                        and self._dirty
                        and now - self._last_render_time >= self._render_interval):
                    with self._lock:
                        self._sim.renderizar(self._screen)
                        scaled = pygame.transform.scale(self._screen, (ancho_stream, alto_stream))
                        raw = pygame.image.tobytes(scaled, 'RGB')
                    with self._frame_lock:
                        self._raw_frame_rgb = raw
                        self._frame_index += 1
                    self._dirty = False
                    self._last_render_time = now

                if not self._paused and now - last_hist_ts >= 2.0 and self._sim:
                    with self._lock:
                        snap = self._construir_instantanea_historial()
                        self._history.append(snap)
                        if len(self._history) > self._max_history:
                            self._history.pop(0)
                    last_hist_ts = now

                if accumulator < time_step:
                    sleep_time = time_step - accumulator
                    if sleep_time > 0.001:
                        time.sleep(sleep_time)

            except Exception as exc:
                print(f"[Runner] Error en frame (continuando): {exc}")
                time.sleep(0.01)

    def _construir_metricas(self) -> dict:
        sim = self._sim
        gm  = sim.gestor_metricas
        globales = gm.calcular_metricas_globales()
        try:
            zonas = sim.ia_trafico.metricas_zona
        except Exception:
            zonas = {}

        total_veh = len(sim.vehiculos)
        TipoV = self._tipo_veh
        if total_veh > 0:
            if hasattr(TipoV, 'PICKUP'):
                autos    = sum(1 for v in sim.vehiculos if v.tipo == TipoV.AUTO)
                pickups  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.PICKUP)
                buses    = sum(1 for v in sim.vehiculos if v.tipo == TipoV.BUS)
                urbanos  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.TRANSP_URBANO)
                cam_lig  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.CAMION_LIGERO)
                cam_med  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.CAMION_MEDIANO)
                cam_pes  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.CAMION_PESADO)
                articu   = sum(1 for v in sim.vehiculos if v.tipo == TipoV.ARTICULADO)
                particulares = autos + pickups
                publico      = buses + urbanos
                carga        = cam_lig + cam_med + cam_pes + articu
                fleet = {
                    "particulares":       round(particulares / total_veh * 100, 1),
                    "transporte_publico": round(publico      / total_veh * 100, 1),
                    "carga":              round(carga        / total_veh * 100, 1),
                    "motos":              0.0,
                    "detalle": {
                        "Autos":          round(autos   / total_veh * 100, 1),
                        "Pick-ups":       round(pickups / total_veh * 100, 1),
                        "Buses":          round(buses   / total_veh * 100, 1),
                        "Transp. Urbano": round(urbanos / total_veh * 100, 1),
                        "C. Ligero":      round(cam_lig / total_veh * 100, 1),
                        "C. Mediano":     round(cam_med / total_veh * 100, 1),
                        "C. Pesado":      round(cam_pes / total_veh * 100, 1),
                        "Articulado":     round(articu  / total_veh * 100, 1),
                    },
                }
            else:
                autos  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.AUTO)
                combis = sum(1 for v in sim.vehiculos if v.tipo == TipoV.COMBI)
                motos  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.MOTO)
                taxis  = sum(1 for v in sim.vehiculos if v.tipo == TipoV.TAXI)
                publico = combis + taxis
                fleet = {
                    "particulares":       round(autos  / total_veh * 100, 1),
                    "transporte_publico": round(publico / total_veh * 100, 1),
                    "carga":              0.0,
                    "motos":              round(motos  / total_veh * 100, 1),
                }
        else:
            fleet = {"particulares": 0, "transporte_publico": 0, "carga": 0, "motos": 0}

        intersecciones = self._construir_intersecciones()
        log_acciones   = list(sim.ia_trafico.log_acciones)
        recomendaciones= list(sim.ia_trafico.recomendaciones)

        cong = globales.get("congestion_promedio", 0)
        los  = ("F" if cong >= 80 else "E" if cong >= 65 else "D" if cong >= 50
                else "C" if cong >= 35 else "B" if cong >= 20 else "A")
        los_labels = {"A":"Óptimo","B":"Bueno","C":"Regular",
                      "D":"Regular","E":"Malo","F":"Crítico"}

        try:
            impacto = sim.ia_trafico._evaluar_impacto_predictivo()
        except Exception:
            impacto = []

        hora_h = int(sim.hora_simulada)
        hora_m = int((sim.hora_simulada - hora_h) * 60)

        ml_stats = {
            "disponible": False,
            "epsilon": 1.0,
            "buffer_size": 0,
            "prediction_probs": [0.25, 0.25, 0.25, 0.25]
        }
        if hasattr(sim, 'ia_trafico') and hasattr(sim.ia_trafico, 'ml_bridge') and sim.ia_trafico.ml_bridge is not None:
            try:
                bridge = sim.ia_trafico.ml_bridge
                if bridge.rl_agent is not None:
                    ml_stats = {
                        "disponible": True,
                        "epsilon": float(bridge.rl_agent.epsilon),
                        "buffer_size": len(bridge.rl_agent.buffer),
                        "prediction_probs": bridge.clasificar_probabilidades(sim)
                    }
            except Exception as e:
                print(f"[ML] Error obteniendo estadísticas para API: {e}")

        s_frames = sim.stats_sin_ia.get('frames', 0)
        c_frames = sim.stats_con_ia.get('frames', 0)

        s_frames_div = max(1, s_frames)
        c_frames_div = max(1, c_frames)

        c_sin = sim.stats_sin_ia.get('congestion_acumulada', 0.0) / s_frames_div
        c_con = sim.stats_con_ia.get('congestion_acumulada', 0.0) / c_frames_div

        v_sin = sim.stats_sin_ia.get('velocidad_acumulada', 0.0) / s_frames_div
        v_con = sim.stats_con_ia.get('velocidad_acumulada', 0.0) / c_frames_div

        d_sin = sim.stats_sin_ia.get('detenidos_acumulados', 0.0) / s_frames_div
        d_con = sim.stats_con_ia.get('detenidos_acumulados', 0.0) / c_frames_div

        esp_sin = (sim.stats_sin_ia.get('tiempo_espera_total', 0) / max(1, sim.stats_sin_ia.get('vehiculos_unicos', 1))) / 60.0
        esp_con = (sim.stats_con_ia.get('tiempo_espera_total', 0) / max(1, sim.stats_con_ia.get('vehiculos_unicos', 1))) / 60.0

        flujo_sin = sim.stats_sin_ia.get('vehiculos_completados', 0) / max(0.1, (s_frames_div / 3600.0))
        flujo_con = sim.stats_con_ia.get('vehiculos_completados', 0) / max(0.1, (c_frames_div / 3600.0))

        desv_sin = sim.stats_sin_ia.get('vehiculos_desviados', 0)
        desv_con = sim.stats_con_ia.get('vehiculos_desviados', 0)

        ef_sin = 100.0 * sim.stats_sin_ia.get('tiempo_movimiento_total', 0) / max(1.0, sim.stats_sin_ia.get('tiempo_movimiento_total', 0) + sim.stats_sin_ia.get('tiempo_espera_semaforo', 0))
        ef_con = 100.0 * sim.stats_con_ia.get('tiempo_movimiento_total', 0) / max(1.0, sim.stats_con_ia.get('tiempo_movimiento_total', 0) + sim.stats_con_ia.get('tiempo_espera_semaforo', 0))

        comparativa = {
            "sin_ia": {
                "congestiva": round(c_sin, 1),
                "velocidad": round(v_sin, 2),
                "detenidos": round(d_sin, 1),
                "espera": round(esp_sin, 1),
                "flujo": round(flujo_sin, 1),
                "desviados": desv_sin,
                "efectividad": round(ef_sin, 1),
                "frames": s_frames
            },
            "con_ia": {
                "congestiva": round(c_con, 1),
                "velocidad": round(v_con, 2),
                "detenidos": round(d_con, 1),
                "espera": round(esp_con, 1),
                "flujo": round(flujo_con, 1),
                "desviados": desv_con,
                "efectividad": round(ef_con, 1),
                "frames": c_frames
            },
            "benchmark_activo": getattr(sim, 'benchmark_activo', False),
            "benchmark_fase": getattr(sim, 'benchmark_fase', 0),
            "benchmark_frames_restantes": getattr(sim, 'benchmark_frames_restantes', 0),
            "benchmark_frames_fase": getattr(sim, 'benchmark_frames_fase', 1000)
        }

        return {
            "hora_simulada": f"{hora_h:02d}:{hora_m:02d}",
            "ia_activa": sim.ia_activa,
            "pausado":   self._paused,
            "globales": {
                "congestion_global":    round(globales.get("congestion_promedio", 0), 1),
                "velocidad_promedio":   round(globales.get("velocidad_promedio", 0), 2),
                "vehiculos_activos":    globales.get("total_vehiculos", 0),
                "vehiculos_max":        120,
                "detenidos":            globales.get("detenidos", 0),
                "espera_promedio":      round(globales.get("espera_promedio", 0), 1),
                "efectividad_semaforos":round(globales.get("efectividad_semaforos", 0), 1),
                "emisiones_co2":        round(globales.get("emisiones_co2_estimadas", 0), 1),
                "accidentes":           0,
                "los":                  los,
                "los_label":            los_labels.get(los, "Regular"),
                "tiempo_medio_viaje":   round(globales.get("espera_promedio", 0) * 8, 1),
            },
            "zonas": zonas,
            "fleet": fleet,
            "intersecciones": intersecciones,
            "log_acciones":   log_acciones,
            "recomendaciones":recomendaciones,
            "impacto_predictivo": impacto[:4],
            "ml_stats": ml_stats,
            "comparativa": comparativa
        }

    def _construir_intersecciones(self) -> list:
        sim = self._sim
        nombres = self._nombres_int
        intersecciones = []
        for i, sem in enumerate(sim.semaforos[:5]):
            cercanos = [v for v in sim.vehiculos if v.posicion.distancia_a(sem.posicion) < 80]
            espera = 0
            if cercanos:
                espera = sum(v.tiempo_espera_acumulado for v in cercanos) / len(cercanos) / 60
            los = ("F" if espera > 60 else "E" if espera > 45 else "D" if espera > 30
                   else "C" if espera > 15 else "B")
            intersecciones.append({
                "nombre": nombres[i] if i < len(nombres) else f"Int. {i+1}",
                "espera": f"{int(espera)} s",
                "los":    los,
                "fase":   sem.fase.name,
            })
        return intersecciones

    def _construir_instantanea_historial(self) -> dict:
        sim   = self._sim
        total = len(sim.vehiculos)
        vel   = sim.estadisticas.get("promedio_velocidad", 0)
        cong  = sim.estadisticas.get("congestion", 0)
        flujo = total / 10.0 if total > 0 else 0
        return {
            "timestamp": time.time(),
            "velocidad": round(vel, 2),
            "congestion":round(cong, 1),
            "flujo":     round(flujo, 2),
            "vehiculos": total,
        }

_NOMBRES_CENTRO = [
    "Plaza Mayor", "Av. Sol / Tullu.", "San Pedro / Sol",
    "San Blas / Hatun", "Eje Av. El Sol",
]
_NOMBRES_ANGOSTURA = [
    "C7×C3 (Hotel)", "C2×C3", "C2×C8 (Puente)",
    "C2×C5", "C6×C1",
]

runner = EjecutorSimulacion(
    sim_cls   = _HeadlessCentro,
    ancho     = ANCHO, alto = ALTO, fps = FPS,
    tipo_veh_cls = TipoVehiculo,
    nombres_intersecciones = _NOMBRES_CENTRO,
    sim_speed = 2.5,
)

runner_angostura = EjecutorSimulacion(
    sim_cls   = SimulacionAngostura,
    ancho     = ANCHO_A, alto = ALTO_A, fps = FPS_A,
    tipo_veh_cls = TipoVehiculo,
    nombres_intersecciones = _NOMBRES_ANGOSTURA,
)

def obtener_runner(localidad: str) -> EjecutorSimulacion:
    """Devuelve el runner correspondiente a la localidad solicitada."""
    if localidad == "sector_angostura":
        return runner_angostura
    return runner
