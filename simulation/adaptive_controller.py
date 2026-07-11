# -*- coding: utf-8 -*-
"""
simulation/adaptive_controller.py
Controlador adaptativo de semáforos basado en reglas físicas de congestión local.
"""
from simulation.road import DireccionCalle

class AdaptiveController:
    def __init__(self, semaforos):
        self.semaforos = semaforos

    def actualizar(self, sim):
        """Ajusta tiempos de semáforo por fase según congestión local por carril/dirección por reglas."""
        for semaforo in self.semaforos:
            cercanos = [
                v for v in sim.vehiculos
                if v.posicion.distancia_a(semaforo.posicion) < 150
            ]
            if not cercanos:
                semaforo.actualizar()
                continue
                
            v_vertical = [v for v in cercanos if v.calle_actual.direccion == DireccionCalle.VERTICAL]
            v_horizontal = [v for v in cercanos if v.calle_actual.direccion == DireccionCalle.HORIZONTAL]
            v_diagonal = [v for v in cercanos if v.calle_actual.direccion == DireccionCalle.DIAGONAL]
            
            if v_vertical:
                lentos_v = sum(1 for v in v_vertical if v.velocidad_actual < v.velocidad_maxima * 0.45)
                cong_v = lentos_v / len(v_vertical)
                if len(v_vertical) >= 2 and cong_v > 0.40:
                    semaforo.duracion_norte_sur = min(30.0, semaforo.duracion_norte_sur + 0.4)
                else:
                    semaforo.duracion_norte_sur = max(5.0, semaforo.duracion_norte_sur - 0.05)
            else:
                semaforo.duracion_norte_sur = max(5.0, semaforo.duracion_norte_sur - 0.02)
                
            if v_horizontal:
                lentos_h = sum(1 for v in v_horizontal if v.velocidad_actual < v.velocidad_maxima * 0.45)
                cong_h = lentos_h / len(v_horizontal)
                if len(v_horizontal) >= 2 and cong_h > 0.40:
                    semaforo.duracion_este_oeste = min(30.0, semaforo.duracion_este_oeste + 0.4)
                else:
                    semaforo.duracion_este_oeste = max(5.0, semaforo.duracion_este_oeste - 0.05)
            else:
                semaforo.duracion_este_oeste = max(5.0, semaforo.duracion_este_oeste - 0.02)
                
            if v_diagonal:
                lentos_d = sum(1 for v in v_diagonal if v.velocidad_actual < v.velocidad_maxima * 0.45)
                cong_d = lentos_d / len(v_diagonal)
                if len(v_diagonal) >= 2 and cong_d > 0.40:
                    semaforo.duracion_giro = min(20.0, semaforo.duracion_giro + 0.3)
                else:
                    semaforo.duracion_giro = max(4.0, semaforo.duracion_giro - 0.04)
            else:
                semaforo.duracion_giro = max(4.0, semaforo.duracion_giro - 0.02)
            
            semaforo.actualizar()
