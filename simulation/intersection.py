# -*- coding: utf-8 -*-
"""
simulation/intersection.py
Abstracciones de intersecciones y algoritmo Dijkstra de enrutamiento vehicular.
"""
import heapq
import math
from typing import List, Tuple, Set, Dict, Optional
from simulation.road import Calle, DireccionCalle
from simulation.vehicle import TipoVehiculo

def calcular_peso_calle(sim, calle: Calle, criterio: str, tipo_vehiculo: TipoVehiculo) -> float:
    longitud = calle.inicio.distancia_a(calle.fin)
    
    vehiculos_en_calle = [v for v in sim.vehiculos if v.calle_actual == calle]
    if vehiculos_en_calle:
        vel_promedio = sum(v.velocidad_actual for v in vehiculos_en_calle) / len(vehiculos_en_calle)
        vel_estimada = 0.3 * calle.velocidad_maxima + 0.7 * max(0.1, vel_promedio)
    else:
        vel_estimada = calle.velocidad_maxima
        
    vel_estimada = max(0.2, vel_estimada)
    
    penalizacion_semaforo = 0.0
    for s in sim.semaforos:
        if s.posicion.distancia_a(calle.fin) < 50:
            es_rojo = True
            from simulation.traffic_light import FaseSemaforo
            if calle.direccion == DireccionCalle.VERTICAL and s.fase in (FaseSemaforo.NORTE_SUR, FaseSemaforo.NORTE_SUR_AMARILLO):
                es_rojo = False
            elif calle.direccion == DireccionCalle.HORIZONTAL and s.fase in (FaseSemaforo.ESTE_OESTE, FaseSemaforo.ESTE_OESTE_AMARILLO):
                es_rojo = False
            elif calle.direccion == DireccionCalle.DIAGONAL and s.fase in (FaseSemaforo.GIRO, FaseSemaforo.GIRO_AMARILLO):
                es_rojo = False
            
            if es_rojo:
                penalizacion_semaforo += 120.0
            else:
                penalizacion_semaforo += 20.0
                
    factor_tipo = 1.0
    if criterio == 'preferente_transporte':
        if calle.tipo == 'principal':
            factor_tipo = 0.4
        elif calle.tipo == 'secundaria':
            factor_tipo = 1.2
        elif calle.tipo == 'empedrada':
            factor_tipo = 8.0
    else:
        if calle.tipo == 'principal':
            factor_tipo = 0.7
        elif calle.tipo == 'secundaria':
            factor_tipo = 1.0
        elif calle.tipo == 'empedrada':
            factor_tipo = 2.0

    if criterio == 'corta':
        return longitud
    elif criterio == 'rapida':
        tiempo_viaje = longitud / vel_estimada
        return tiempo_viaje * factor_tipo + 0.15 * len(vehiculos_en_calle) + 0.1 * penalizacion_semaforo
    elif criterio == 'economica':
        tiempo_viaje = longitud / vel_estimada
        return (tiempo_viaje * factor_tipo) * (1.0 + 5.0 * len(vehiculos_en_calle)) + 0.5 * penalizacion_semaforo
    elif criterio == 'evita_ia':
        es_critica = False
        for nombre in sim.ia_trafico.zonas_con_desvio_activo.union(sim.ia_trafico.zonas_con_ingreso_reducido):
            x1, y1, x2, y2 = sim.ia_trafico.zonas[nombre]
            for p in [calle.inicio, calle.fin]:
                if x1 <= p.x <= x2 and y1 <= p.y <= y2:
                    es_critica = True
                    break
        penalty_ia = 1000.0 if es_critica else 0.0
        tiempo_viaje = longitud / vel_estimada
        return (tiempo_viaje * factor_tipo) * (1.0 + 2.0 * len(vehiculos_en_calle)) + penalty_ia + 0.2 * penalizacion_semaforo
    elif criterio == 'comoda':
        tiempo_viaje = longitud / vel_estimada
        return (tiempo_viaje * factor_tipo) + 2.5 * penalizacion_semaforo + 0.5 * len(vehiculos_en_calle)
    elif criterio == 'preferente_transporte':
        tiempo_viaje = longitud / vel_estimada
        return (tiempo_viaje * factor_tipo) * (1.0 + 3.0 * len(vehiculos_en_calle)) + 0.3 * penalizacion_semaforo
        
    return longitud

def obtener_ruta_inteligente(sim, calle_inicio: Calle, calle_fin: Calle, criterio: str, tipo_vehiculo: TipoVehiculo) -> List[Calle]:
    """Cálculo de ruta óptima mediante algoritmo Dijkstra sobre el grafo de intersecciones"""
    start_node = (int(calle_inicio.fin.x), int(calle_inicio.fin.y))
    end_node = (int(calle_fin.fin.x), int(calle_fin.fin.y))
    
    if calle_inicio == calle_fin:
        return [calle_inicio]
        
    distancias = {node: float('inf') for node in sim.nodos_interseccion}
    previo = {node: None for node in sim.nodos_interseccion}
    
    distancias[start_node] = 0.0
    pq = [(0.0, start_node)]
    
    while pq:
        dist_act, u = heapq.heappop(pq)
        
        if u == end_node:
            break
            
        if dist_act > distancias[u]:
            continue
            
        for v, calle in sim.adyacencias.get(u, []):
            peso = calcular_peso_calle(sim, calle, criterio, tipo_vehiculo)
            
            if distancias[u] + peso < distancias[v]:
                distancias[v] = distancias[u] + peso
                previo[v] = (u, calle)
                heapq.heappush(pq, (distancias[v], v))
                
    if distancias[end_node] == float('inf'):
        return [calle_inicio]
        
    camino = []
    actual = end_node
    visitados = set()
    while actual != start_node and actual not in visitados:
        visitados.add(actual)
        prev_info = previo[actual]
        if prev_info is None:
            break
        prev_node, calle = prev_info
        camino.append(calle)
        actual = prev_node
        
    camino.reverse()
    return [calle_inicio] + camino
