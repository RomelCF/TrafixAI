# -*- coding: utf-8 -*-
import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time

pygame.init()

ANCHO = 1600
ALTO = 1000
FPS = 60

from simulation.road import COLORES, DireccionCalle, Punto, Calle
from simulation.vehicle import TipoVehiculo, Vehiculo
from simulation.traffic_light import EstadoSemaforo, FaseSemaforo, Semaforo
from simulation.metrics import GestorMetricas
from simulation.controllers.ai_controller import GestorIATrafico
from simulation.spatial import IndiceEspacial

class SimulacionTrafico:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Simulación Ampliada - Centro Histórico del Cusco")
        self.reloj = pygame.time.Clock()
        
        self.vehiculos = []
        self.semaforos = []
        self.calles = self._crear_red_calles_cusco_ampliada()
        self._crear_semaforos_estrategicos_ampliados()
        
        self.vehiculos_generados = 0
        self.tiempo_ultima_generacion = time.time()
        self.estadisticas = {
            'autos': 0, 'combis': 0, 'motos': 0, 'taxis': 0,
            'promedio_velocidad': 0, 'congestion': 0
        }
        
        self.patrones_horarios = self._crear_patrones_horarios()
        self.hora_simulada = 8.0
        
        self.ia_activa = True
        
        self.stats_sin_ia = {
            'frames': 0,
            'congestion_acumulada': 0.0,
            'velocidad_acumulada': 0.0,
            'detenidos_acumulados': 0,
            'tiempo_espera_total': 0,
            'vehiculos_unicos': 0,
            'vehiculos_completados': 0,
            'vehiculos_desviados': 0,
            'tiempo_movimiento_total': 0,
            'tiempo_espera_semaforo': 0
        }
        
        self.stats_con_ia = {
            'frames': 0,
            'congestion_acumulada': 0.0,
            'velocidad_acumulada': 0.0,
            'detenidos_acumulados': 0,
            'tiempo_espera_total': 0,
            'vehiculos_unicos': 0,
            'vehiculos_completados': 0,
            'vehiculos_desviados': 0,
            'tiempo_movimiento_total': 0,
            'tiempo_espera_semaforo': 0
        }
        
        self.benchmark_activo = False
        self.benchmark_fase = 0
        self.benchmark_frames_fase = 1000
        self.benchmark_frames_restantes = 0
        self.ia_trafico = GestorIATrafico(self)
        self.gestor_metricas = GestorMetricas(self)
        
        self.nodos_interseccion = set()
        for c in self.calles:
            self.nodos_interseccion.add((int(c.inicio.x), int(c.inicio.y)))
            self.nodos_interseccion.add((int(c.fin.x), int(c.fin.y)))
            
        self.adyacencias = {node: [] for node in self.nodos_interseccion}
        for c in self.calles:
            start_node = (int(c.inicio.x), int(c.inicio.y))
            end_node = (int(c.fin.x), int(c.fin.y))
            self.adyacencias[start_node].append((end_node, c))

        self._mapa_estatico = None
        self._indice_semaforos = IndiceEspacial(100)
        self._inicializar_indices()

    def _inicializar_indices(self):
        self._indice_semaforos.reconstruir(self.semaforos)
        if not hasattr(self, '_indice_vehiculos'):
            self._indice_vehiculos = IndiceEspacial(80)
        self._precomputar_mapa_estatico()

    def _vehiculos_cercanos(self, posicion: Punto, vehiculo, radio: float = 80):
        candidatos = self._indice_vehiculos.consultar(posicion.x, posicion.y, radio)
        return [v for v in candidatos if v is not vehiculo]

    def _actualizar_vehiculos(self):
        i = 0
        while i < len(self.vehiculos):
            vehiculo = self.vehiculos[i]
            otros = self._vehiculos_cercanos(vehiculo.posicion, vehiculo)
            sems = self._semaforos_cercanos(vehiculo.posicion)
            if not vehiculo.actualizar(otros, sems):
                if vehiculo.indice_ruta >= len(vehiculo.ruta):
                    active_stats = self.stats_con_ia if self.ia_activa else self.stats_sin_ia
                    active_stats['vehiculos_completados'] += 1
                self._indice_vehiculos.eliminar(vehiculo)
                self.vehiculos.pop(i)
            else:
                self._indice_vehiculos.actualizar(
                    vehiculo, vehiculo.posicion.x, vehiculo.posicion.y
                )
                i += 1

    def _sync_indice_vehiculos(self):
        self._indice_vehiculos.reconstruir(self.vehiculos)

    def _semaforos_cercanos(self, posicion: Punto, radio: float = 80):
        return self._indice_semaforos.consultar(posicion.x, posicion.y, radio)

    def _precomputar_mapa_estatico(self):
        self._mapa_estatico = pygame.Surface((ANCHO, ALTO))
        self._dibujar_capas_estaticas(self._mapa_estatico)

    def _crear_red_calles_cusco_ampliada(self) -> List[Calle]:
        """Red de calles ampliada del centro histórico con más cruces"""
        calles = []
        
        calles.extend([
            Calle(Punto(0, 400), Punto(ANCHO, 400), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(Punto(ANCHO, 425), Punto(0, 425), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
        ])
        
        calles.extend([
            Calle(Punto(800, 0), Punto(800, ALTO), 40, 'principal', DireccionCalle.VERTICAL, 2.8),
            Calle(Punto(825, ALTO), Punto(825, 0), 40, 'principal', DireccionCalle.VERTICAL, 2.8),
        ])
        
        calles.extend([
            Calle(Punto(0, 200), Punto(ANCHO, 200), 40, 'principal', DireccionCalle.HORIZONTAL, 2.8),
            Calle(Punto(ANCHO, 225), Punto(0, 225), 40, 'principal', DireccionCalle.HORIZONTAL, 2.8),
        ])
        
        calles.extend([
            Calle(Punto(0, 600), Punto(ANCHO, 600), 40, 'principal', DireccionCalle.HORIZONTAL, 2.8),
            Calle(Punto(ANCHO, 625), Punto(0, 625), 40, 'principal', DireccionCalle.HORIZONTAL, 2.8),
        ])
        
        calles.extend([
            Calle(Punto(300, 0), Punto(300, ALTO), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
            Calle(Punto(325, ALTO), Punto(325, 0), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
        ])
        
        calles.extend([
            Calle(Punto(500, 0), Punto(500, ALTO), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
            Calle(Punto(525, ALTO), Punto(525, 0), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
        ])
        
        calles.extend([
            Calle(Punto(1100, 0), Punto(1100, ALTO), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
            Calle(Punto(1125, ALTO), Punto(1125, 0), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
        ])
        
        calles.extend([
            Calle(Punto(1300, 0), Punto(1300, ALTO), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
            Calle(Punto(1325, ALTO), Punto(1325, 0), 35, 'principal', DireccionCalle.VERTICAL, 2.5),
        ])
        
        calles.extend([
            Calle(Punto(200, 320), Punto(900, 340), 22, 'empedrada', DireccionCalle.HORIZONTAL, 1.5),
            Calle(Punto(900, 360), Punto(200, 380), 22, 'empedrada', DireccionCalle.HORIZONTAL, 1.5),
            Calle(Punto(250, 280), Punto(850, 300), 20, 'empedrada', DireccionCalle.HORIZONTAL, 1.2),
            Calle(Punto(350, 450), Punto(650, 450), 18, 'empedrada', DireccionCalle.HORIZONTAL, 1.0),
            Calle(Punto(350, 500), Punto(650, 500), 18, 'empedrada', DireccionCalle.HORIZONTAL, 1.0),
            Calle(Punto(400, 520), Punto(400, 720), 16, 'empedrada', DireccionCalle.VERTICAL, 1.0),
            Calle(Punto(600, 480), Punto(600, 650), 15, 'empedrada', DireccionCalle.VERTICAL, 0.8),
            Calle(Punto(650, 300), Punto(750, 500), 25, 'empedrada', DireccionCalle.DIAGONAL, 1.0),
            Calle(Punto(750, 500), Punto(850, 600), 25, 'empedrada', DireccionCalle.DIAGONAL, 1.0),
            Calle(Punto(150, 700), Punto(400, 720), 20, 'empedrada', DireccionCalle.HORIZONTAL, 1.2),
            Calle(Punto(150, 750), Punto(350, 770), 20, 'empedrada', DireccionCalle.HORIZONTAL, 1.2),
        ])
        
        calles.extend([
            Calle(Punto(0, 100), Punto(ANCHO, 100), 30, 'secundaria', DireccionCalle.HORIZONTAL, 2.0),
            Calle(Punto(0, 300), Punto(ANCHO, 300), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.0),
            Calle(Punto(0, 500), Punto(ANCHO, 500), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.0),
            Calle(Punto(0, 700), Punto(ANCHO, 700), 30, 'secundaria', DireccionCalle.HORIZONTAL, 2.0),
            Calle(Punto(0, 800), Punto(ANCHO, 800), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.0),
            
            Calle(Punto(100, 0), Punto(100, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(200, 0), Punto(200, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(600, 0), Punto(600, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(700, 0), Punto(700, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(900, 0), Punto(900, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(1000, 0), Punto(1000, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(1200, 0), Punto(1200, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(Punto(1400, 0), Punto(1400, ALTO), 25, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            
            Calle(Punto(400, 150), Punto(800, 350), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(Punto(900, 150), Punto(1200, 400), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(Punto(200, 600), Punto(500, 800), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(Punto(1000, 600), Punto(1300, 850), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
        ])
        
        calles.extend([
            Calle(Punto(700, 100), Punto(950, 150), 18, 'empedrada', DireccionCalle.DIAGONAL, 1.0),
            Calle(Punto(850, 50), Punto(900, 200), 16, 'empedrada', DireccionCalle.VERTICAL, 0.8),
            Calle(Punto(950, 100), Punto(1100, 180), 18, 'empedrada', DireccionCalle.DIAGONAL, 1.0),
        ])
        
        calles.extend([
            Calle(Punto(100, 150), Punto(250, 180), 20, 'empedrada', DireccionCalle.HORIZONTAL, 1.2),
            Calle(Punto(50, 200), Punto(200, 250), 18, 'empedrada', DireccionCalle.DIAGONAL, 1.0),
        ])
        
        calles.extend([
            Calle(Punto(1200, 700), Punto(1500, 750), 24, 'secundaria', DireccionCalle.HORIZONTAL, 1.8),
            Calle(Punto(1350, 650), Punto(1400, 850), 22, 'secundaria', DireccionCalle.VERTICAL, 1.6),
        ])
        
        return calles
    
    def _crear_semaforos_estrategicos_ampliados(self):
        """Coloca semáforos en todas las intersecciones importantes de la red ampliada"""
        intersecciones_principales = [
            (Punto(300, 200), 'principal'),
            (Punto(500, 200), 'principal'),
            (Punto(800, 200), 'principal'),
            (Punto(1100, 200), 'principal'),
            (Punto(1300, 200), 'principal'),
            
            (Punto(300, 400), 'principal'),
            (Punto(500, 400), 'principal'),
            (Punto(800, 400), 'principal'),
            (Punto(1100, 400), 'principal'),
            (Punto(1300, 400), 'principal'),
            
            (Punto(300, 600), 'principal'),
            (Punto(500, 600), 'principal'),
            (Punto(800, 600), 'principal'),
            (Punto(1100, 600), 'principal'),
            (Punto(1300, 600), 'principal'),
        ]
        
        intersecciones_secundarias = [
            (Punto(100, 200), 'normal'),
            (Punto(200, 200), 'normal'),
            (Punto(600, 200), 'normal'),
            (Punto(700, 200), 'normal'),
            (Punto(900, 200), 'normal'),
            (Punto(1000, 200), 'normal'),
            (Punto(1200, 200), 'normal'),
            (Punto(1400, 200), 'normal'),
            
            (Punto(100, 400), 'normal'),
            (Punto(200, 400), 'normal'),
            (Punto(600, 400), 'normal'),
            (Punto(700, 400), 'normal'),
            (Punto(900, 400), 'normal'),
            (Punto(1000, 400), 'normal'),
            (Punto(1200, 400), 'normal'),
            (Punto(1400, 400), 'normal'),
            
            (Punto(100, 600), 'normal'),
            (Punto(200, 600), 'normal'),
            (Punto(600, 600), 'normal'),
            (Punto(700, 600), 'normal'),
            (Punto(900, 600), 'normal'),
            (Punto(1000, 600), 'normal'),
            (Punto(1200, 600), 'normal'),
            (Punto(1400, 600), 'normal'),
            
            (Punto(300, 100), 'normal'),
            (Punto(500, 100), 'normal'),
            (Punto(800, 100), 'normal'),
            (Punto(1100, 100), 'normal'),
            
            (Punto(300, 300), 'normal'),
            (Punto(500, 300), 'normal'),
            (Punto(800, 300), 'normal'),
            (Punto(1100, 300), 'normal'),
            
            (Punto(300, 500), 'normal'),
            (Punto(500, 500), 'normal'),
            (Punto(800, 500), 'normal'),
            (Punto(1100, 500), 'normal'),
            
            (Punto(300, 700), 'normal'),
            (Punto(500, 700), 'normal'),
            (Punto(800, 700), 'normal'),
            (Punto(1100, 700), 'normal'),
            
            (Punto(300, 800), 'normal'),
            (Punto(500, 800), 'normal'),
            (Punto(800, 800), 'normal'),
            (Punto(1100, 800), 'normal'),
        ]
        
        intersecciones_historicas = [
            (Punto(400, 320), 'normal'),
            (Punto(600, 340), 'normal'),
            (Punto(350, 450), 'normal'),
            (Punto(400, 520), 'normal'),
            (Punto(600, 500), 'normal'),
            (Punto(700, 350), 'normal'),
            (Punto(200, 720), 'normal'),
        ]
        
        for posicion, tipo in intersecciones_principales:
            self.semaforos.append(Semaforo(posicion, tipo))
            
        for posicion, tipo in intersecciones_secundarias:
            self.semaforos.append(Semaforo(posicion, tipo))
            
        for posicion, tipo in intersecciones_historicas:
            self.semaforos.append(Semaforo(posicion, tipo))
            
    def _calcular_peso_calle(self, calle: Calle, criterio: str, tipo_vehiculo: TipoVehiculo) -> float:
        from simulation.intersection import calcular_peso_calle
        return calcular_peso_calle(self, calle, criterio, tipo_vehiculo)

    def obtener_ruta_inteligente(self, calle_inicio: Calle, calle_fin: Calle, criterio: str, tipo_vehiculo: TipoVehiculo) -> List[Calle]:
        """Cálculo de ruta óptima mediante algoritmo Dijkstra sobre el grafo de intersecciones"""
        from simulation.intersection import obtener_ruta_inteligente as dijkstra_ruta
        return dijkstra_ruta(self, calle_inicio, calle_fin, criterio, tipo_vehiculo)
    
    def _crear_patrones_horarios(self) -> dict:
        """Patrones de tráfico según la hora del día"""
        return {
            'mañana': {'factor': 1.2, 'tipos': [TipoVehiculo.AUTO, TipoVehiculo.COMBI, TipoVehiculo.TAXI]},
            'mediodia': {'factor': 0.8, 'tipos': [TipoVehiculo.AUTO, TipoVehiculo.MOTO]},
            'tarde': {'factor': 1.5, 'tipos': [TipoVehiculo.COMBI, TipoVehiculo.AUTO, TipoVehiculo.TAXI]},
            'noche': {'factor': 0.4, 'tipos': [TipoVehiculo.TAXI, TipoVehiculo.AUTO]}
        }
    
    def _generar_vehiculo_inteligente(self):
        """Generación de vehículos basada en patrones realistas"""
        tiempo_actual = time.time()
        
        if 6 <= self.hora_simulada < 12:
            patron = self.patrones_horarios['mañana']
        elif 12 <= self.hora_simulada < 18:
            patron = self.patrones_horarios['tarde']
        elif 18 <= self.hora_simulada < 22:
            patron = self.patrones_horarios['mediodia']
        else:
            patron = self.patrones_horarios['noche']
        
        intervalo_base = random.uniform(1.0, 3.0)
        intervalo_ajustado = intervalo_base / patron['factor']
        
        if tiempo_actual - self.tiempo_ultima_generacion < intervalo_ajustado:
            return
        
        if len(self.vehiculos) >= 120:
            return
        
        tipo = random.choice(patron['tipos'])
        
        calles_borde = []
        for c in self.calles:
            if c.tipo in ['principal', 'secundaria'] and not self._calle_bloqueada_por_ia(c):
                p = c.inicio
                if p.x < 50 or p.x > 1550 or p.y < 50 or p.y > 950:
                    calles_borde.append(c)
                    
        if not calles_borde:
            calles_borde = [
                c for c in self.calles
                if c.tipo in ['principal', 'secundaria'] and 
                (c.inicio.x < 50 or c.inicio.x > 1550 or c.inicio.y < 50 or c.inicio.y > 950)
            ]
            
        if not calles_borde:
            calles_borde = [c for c in self.calles if c.tipo in ['principal', 'secundaria']]
            
        calle_inicial = random.choice(calles_borde)
        
        posicion_inicial = Punto(
            calle_inicial.inicio.x + random.uniform(0, 0.1) * (calle_inicial.fin.x - calle_inicial.inicio.x),
            calle_inicial.inicio.y + random.uniform(0, 0.1) * (calle_inicial.fin.y - calle_inicial.inicio.y)
        )
        
        vehiculo = Vehiculo(tipo, posicion_inicial, calle_inicial)
        
        destinos_candidatos = [c for c in calles_borde if c != calle_inicial]
        if not destinos_candidatos:
            destinos_candidatos = calles_borde
        calle_destino = random.choice(destinos_candidatos)
        
        ruta = self.obtener_ruta_inteligente(calle_inicial, calle_destino, vehiculo.criterio_ruta, vehiculo.tipo)
        
        if len(ruta) <= 1:
            ruta = self._generar_ruta_realista(calle_inicial)
            
        vehiculo.establecer_ruta(ruta)
        
        self.vehiculos.append(vehiculo)
        self._indice_vehiculos.insertar(vehiculo, posicion_inicial.x, posicion_inicial.y)
        self.vehiculos_generados += 1
        self.estadisticas[tipo.name.lower() + 's'] += 1
        self.tiempo_ultima_generacion = tiempo_actual
        
        active_stats = self.stats_con_ia if self.ia_activa else self.stats_sin_ia
        active_stats['vehiculos_unicos'] += 1

    def _calle_bloqueada_por_ia(self, calle):
        """Devuelve True si la calle cae dentro de una zona con ingreso reducido por la IA."""
        for nombre in self.ia_trafico.zonas_con_ingreso_reducido:
            x1, y1, x2, y2 = self.ia_trafico.zonas[nombre]
            for p in [calle.inicio, calle.fin]:
                if x1 <= p.x <= x2 and y1 <= p.y <= y2:
                    return True
        return False
    
    def _generar_ruta_realista(self, calle_inicial: Calle) -> List[Calle]:
        """Genera una ruta realista que empieza y termina estrictamente en los bordes del mapa"""
        ruta = [calle_inicial]
        calle_actual = calle_inicial
        
        for i in range(12):
            if i >= 3:
                f = calle_actual.fin
                if f.x < 50 or f.x > 1550 or f.y < 50 or f.y > 950:
                    break
                    
            calles_conectadas = []
            for calle in self.calles:
                if calle != calle_actual and calle not in ruta:
                    if calle_actual.fin.distancia_a(calle.inicio) < 50:
                        calles_conectadas.append(calle)
            
            if calles_conectadas:
                if i >= 5:
                    calles_borde = [c for c in calles_conectadas if c.fin.x < 50 or c.fin.x > 1550 or c.fin.y < 50 or c.fin.y > 950]
                    if calles_borde:
                        calle_actual = random.choice(calles_borde)
                    else:
                        calle_actual = random.choice(calles_conectadas)
                else:
                    calle_actual = random.choice(calles_conectadas)
                ruta.append(calle_actual)
            else:
                break
                
        f = calle_actual.fin
        if not (f.x < 50 or f.x > 1550 or f.y < 50 or f.y > 950):
            for calle in self.calles:
                if calle_actual.fin.distancia_a(calle.inicio) < 50:
                    cf = calle.fin
                    if cf.x < 50 or cf.x > 1550 or cf.y < 50 or cf.y > 950:
                        ruta.append(calle)
                        break
                        
        return ruta
    
    def _actualizar_estadisticas(self):
        """Actualiza estadísticas en tiempo real"""
        if not self.vehiculos:
            self.estadisticas['promedio_velocidad'] = 0
            self.estadisticas['congestion'] = 0
            return
        
        velocidad_total = sum(v.velocidad_actual for v in self.vehiculos)
        self.estadisticas['promedio_velocidad'] = velocidad_total / len(self.vehiculos)
        
        vehiculos_lentos = sum(
            1 for v in self.vehiculos
            if v.velocidad_actual < v.velocidad_maxima * 0.5
            and not (self.ia_trafico._vehiculo_detenido_por_semaforo(v) and v.tiempo_espera_acumulado <= 360)
        )
        escala_densidad = min(1.0, len(self.vehiculos) / 40.0)
        self.estadisticas['congestion'] = min(100.0, (vehiculos_lentos / len(self.vehiculos)) * 100.0 * escala_densidad)
    
    def _dibujar_mapa_detallado(self):
        """Dibuja el mapa estático cacheado y capas dinámicas."""
        if self._mapa_estatico is not None:
            self.pantalla.blit(self._mapa_estatico, (0, 0))
        else:
            self.pantalla.fill(COLORES['FONDO'])
            self._dibujar_capas_estaticas(self.pantalla)

    def _dibujar_capas_estaticas(self, superficie: pygame.Surface):
        """Capas fijas del mapa (calles, edificios, etiquetas). Se pre-renderizan una sola vez."""
        superficie.fill(COLORES['FONDO'])
        
        plaza_armas = pygame.Rect(345, 445, 125, 115)
        pygame.draw.rect(superficie, COLORES['PLAZA'], plaza_armas)

        pygame.draw.circle(superficie, (100, 100, 150), (407, 502), 18)
        pygame.draw.circle(superficie, (150, 150, 200), (407, 502), 13)

        plaza_sf = pygame.Rect(38, 240, 118, 58)
        pygame.draw.rect(superficie, COLORES['PLAZA'], plaza_sf)

        plaza_regocijo = pygame.Rect(38, 440, 118, 55)
        pygame.draw.rect(superficie, COLORES['PLAZA'], plaza_regocijo)

        edificios = [
            {'rect': pygame.Rect(415, 520, 60, 55), 'tipo': 'catedral'},
            {'rect': pygame.Rect(615, 515, 70, 60), 'tipo': 'iglesia'},
            {'rect': pygame.Rect(715, 520, 30, 55), 'tipo': 'templo'},
            
            {'rect': pygame.Rect(915, 250, 70, 35), 'tipo': 'colonial'},
            {'rect': pygame.Rect(1015, 315, 60, 55), 'tipo': 'colonial'},
            {'rect': pygame.Rect(850, 250, 35, 35), 'tipo': 'iglesia'},
            
            {'rect': pygame.Rect(115, 10, 70, 70), 'tipo': 'colonial'},
            {'rect': pygame.Rect(10, 250, 75, 35), 'tipo': 'iglesia'},
            
            {'rect': pygame.Rect(215, 820, 65, 80), 'tipo': 'mercado'},
            {'rect': pygame.Rect(115, 650, 70, 30), 'tipo': 'colonial'},
            
            {'rect': pygame.Rect(1420, 820, 150, 150), 'tipo': 'colonial'},
            {'rect': pygame.Rect(1215, 650, 65, 30), 'tipo': 'iglesia'},
            
            {'rect': pygame.Rect(1215, 10, 65, 70), 'tipo': 'moderno'},
            {'rect': pygame.Rect(1420, 10, 150, 70), 'tipo': 'moderno'},
            {'rect': pygame.Rect(10, 820, 75, 150), 'tipo': 'moderno'},
            {'rect': pygame.Rect(1145, 820, 40, 150), 'tipo': 'moderno'},
            
            {'rect': pygame.Rect(215, 120, 65, 40), 'tipo': 'colonial'},
            {'rect': pygame.Rect(345, 120, 38, 50), 'tipo': 'colonial'},
            {'rect': pygame.Rect(615, 120, 70, 55), 'tipo': 'colonial'},
            {'rect': pygame.Rect(545, 820, 38, 50), 'tipo': 'colonial'},
            {'rect': pygame.Rect(1145, 250, 40, 35), 'tipo': 'colonial'},
            {'rect': pygame.Rect(115, 820, 70, 60), 'tipo': 'colonial'},
            {'rect': pygame.Rect(350, 820, 120, 60), 'tipo': 'colonial'},
            {'rect': pygame.Rect(848, 720, 36, 60), 'tipo': 'colonial'},
            {'rect': pygame.Rect(1015, 720, 60, 60), 'tipo': 'colonial'},
        ]
        
        for edificio in edificios:
            if edificio['tipo'] == 'catedral':
                pygame.draw.rect(superficie, COLORES['EDIFICIO_COLONIAL'], edificio['rect'])
                torre1 = pygame.Rect(edificio['rect'].x + 20, edificio['rect'].y - 30, 30, 30)
                torre2 = pygame.Rect(edificio['rect'].x + 90, edificio['rect'].y - 30, 30, 30)
                pygame.draw.rect(superficie, COLORES['EDIFICIO_COLONIAL'], torre1)
                pygame.draw.rect(superficie, COLORES['EDIFICIO_COLONIAL'], torre2)
            elif edificio['tipo'] == 'colonial':
                pygame.draw.rect(superficie, COLORES['EDIFICIO_COLONIAL'], edificio['rect'])
                balcon = pygame.Rect(edificio['rect'].x + 10, edificio['rect'].y + 40, 
                                   edificio['rect'].width - 20, 15)
                pygame.draw.rect(superficie, (120, 60, 30), balcon)
            elif edificio['tipo'] == 'moderno':
                pygame.draw.rect(superficie, COLORES['EDIFICIO_MODERNO'], edificio['rect'])
                for i in range(3):
                    for j in range(5):
                        ventana = pygame.Rect(
                            edificio['rect'].x + 15 + i * 25,
                            edificio['rect'].y + 20 + j * 25,
                            15, 15
                        )
                        pygame.draw.rect(superficie, (150, 150, 200), ventana)
            elif edificio['tipo'] == 'iglesia':
                pygame.draw.rect(superficie, COLORES['EDIFICIO_COLONIAL'], edificio['rect'])
                cruz_x = edificio['rect'].centerx
                cruz_y = edificio['rect'].y - 10
                pygame.draw.line(superficie, (200, 200, 200), 
                               (cruz_x, cruz_y - 10), (cruz_x, cruz_y + 10), 3)
                pygame.draw.line(superficie, (200, 200, 200), 
                               (cruz_x - 7, cruz_y - 3), (cruz_x + 7, cruz_y - 3), 3)
            elif edificio['tipo'] == 'mercado':
                pygame.draw.rect(superficie, (139, 125, 107), edificio['rect'])
                for i in range(0, edificio['rect'].width, 20):
                    pygame.draw.arc(superficie, (100, 100, 100),
                                  (edificio['rect'].x + i, edificio['rect'].y - 15, 20, 30),
                                  0, math.pi, 3)
            else:
                pygame.draw.rect(superficie, COLORES['EDIFICIO_COLONIAL'], edificio['rect'])

        for calle in self.calles:
            color = COLORES['ASFALTO']
            if calle.tipo == 'empedrada':
                color = COLORES['PIEDRA']
            elif calle.tipo == 'secundaria':
                color = COLORES['ASFALTO_VIEJO']
            
            dx = calle.fin.x - calle.inicio.x
            dy = calle.fin.y - calle.inicio.y
            longitud = math.sqrt(dx*dx + dy*dy)
            
            if longitud > 0:
                ux = -dy / longitud
                uy = dx / longitud
                ancho_mitad = calle.ancho / 2
                esquinas = [
                    (calle.inicio.x + ux * ancho_mitad, calle.inicio.y + uy * ancho_mitad),
                    (calle.inicio.x - ux * ancho_mitad, calle.inicio.y - uy * ancho_mitad),
                    (calle.fin.x - ux * ancho_mitad, calle.fin.y - uy * ancho_mitad),
                    (calle.fin.x + ux * ancho_mitad, calle.fin.y + uy * ancho_mitad)
                ]
                
                pygame.draw.polygon(superficie, color, esquinas)
                
                if calle.tipo == 'principal' and calle.ancho > 35:
                    pygame.draw.line(superficie, COLORES['LINEA_AMARILLA'],
                                   (calle.inicio.x, calle.inicio.y),
                                   (calle.fin.x, calle.fin.y), 2)

        font = pygame.font.Font(None, 24)
        lugares = [
            ("PLAZA DE ARMAS", 350, 455),
            ("CATEDRAL", 415, 535),
            ("AV. EL SOL", 15, 365),
            ("AV. DE LA CULTURA", 720, 50),
            ("AV. GARCILASO", 15, 165),
            ("AV. TÚPAC AMARU", 15, 565),
            ("SAN BLAS", 820, 80),
            ("SANTA ANA", 80, 100),
            ("SAN PEDRO", 15, 670),
            ("SANTIAGO", 1280, 730),
            ("QORIKANCHA", 690, 500),
            ("MERCADO SAN PEDRO", 215, 800),
        ]
        
        for nombre, x, y in lugares:
            texto = font.render(nombre, True, COLORES['TEXTO'])
            ancho_t, alto_t = font.size(nombre)
            bg_rect = pygame.Rect(x - 6, y - 4, ancho_t + 12, alto_t + 8)
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((10, 15, 25, 195))
            pygame.draw.rect(bg_surf, (40, 80, 150, 130), bg_surf.get_rect(), 1)
            superficie.blit(bg_surf, (bg_rect.x, bg_rect.y))
            
            sombra = font.render(nombre, True, (0, 0, 0))
            superficie.blit(sombra, (x + 1, y + 1))
            superficie.blit(texto, (x, y))
    
    def _mostrar_estadisticas_avanzadas(self):
        panel = pygame.Surface((380, 220))
        panel.set_alpha(180)
        panel.fill((20, 20, 20))
        self.pantalla.blit(panel, (10, 10))
        
        font_titulo = pygame.font.Font(None, 28)
        font_stats = pygame.font.Font(None, 20)
        
        titulo = font_titulo.render("TRÁFICO CUSCO AMPLIADO - TIEMPO REAL", True, COLORES['TEXTO'])
        self.pantalla.blit(titulo, (20, 20))
        
        zona_info = font_stats.render(f"Semáforos activos: {len(self.semaforos)}", True, (150, 200, 255))
        self.pantalla.blit(zona_info, (20, 45))
        
        calles_info = font_stats.render(f"Red de calles: {len(self.calles)} vías", True, (150, 200, 255))
        self.pantalla.blit(calles_info, (200, 45))
        
        hora_texto = f"Hora: {int(self.hora_simulada):02d}:{int((self.hora_simulada % 1) * 60):02d}"
        hora_surface = font_stats.render(hora_texto, True, (200, 200, 255))
        self.pantalla.blit(hora_surface, (20, 65))
        
        stats_vehiculos = [
            f"🚗 Autos: {self.estadisticas['autos']}",
            f"🚐 Combis: {self.estadisticas['combis']}",
            f"🏍️ Motos: {self.estadisticas['motos']}",
            f"🚕 Taxis: {self.estadisticas['taxis']}",
            f"Total activos: {len(self.vehiculos)}",
            f"Generados: {self.vehiculos_generados}"
        ]
        
        for i, stat in enumerate(stats_vehiculos):
            color = COLORES['TEXTO']
            if "Autos" in stat:
                color = COLORES['AUTO_ROJO']
            elif "Combis" in stat:
                color = COLORES['COMBI_AMARILLA']
            elif "Motos" in stat:
                color = COLORES['MOTO_ROJA']
            elif "Taxis" in stat:
                color = COLORES['TAXI']
            
            superficie = font_stats.render(stat, True, color)
            self.pantalla.blit(superficie, (20, 90 + i * 18))
        
        velocidad_promedio = self.estadisticas['promedio_velocidad']
        congestion = self.estadisticas['congestion']
        
        pygame.draw.rect(self.pantalla, (100, 100, 100), (220, 110, 120, 15))
        ancho_velocidad = int((velocidad_promedio / 3.0) * 120)
        color_velocidad = (0, 255, 0) if velocidad_promedio > 2 else (255, 255, 0) if velocidad_promedio > 1 else (255, 0, 0)
        pygame.draw.rect(self.pantalla, color_velocidad, (220, 110, ancho_velocidad, 15))
        
        vel_texto = font_stats.render(f"Velocidad: {velocidad_promedio:.1f}", True, COLORES['TEXTO'])
        self.pantalla.blit(vel_texto, (220, 90))
        
        pygame.draw.rect(self.pantalla, (100, 100, 100), (220, 150, 120, 15))
        ancho_congestion = int((congestion / 100) * 120)
        color_congestion = (255, 0, 0) if congestion > 70 else (255, 255, 0) if congestion > 40 else (0, 255, 0)
        pygame.draw.rect(self.pantalla, color_congestion, (220, 150, ancho_congestion, 15))
        
        cong_texto = font_stats.render(f"Congestión: {congestion:.0f}%", True, COLORES['TEXTO'])
        self.pantalla.blit(cong_texto, (220, 130))
        
        densidad_texto = font_stats.render("Densidad por zona:", True, (200, 200, 200))
        self.pantalla.blit(densidad_texto, (20, 190))
        
        centro = sum(1 for v in self.vehiculos if 400 <= v.posicion.x <= 800 and 300 <= v.posicion.y <= 700)
        norte = sum(1 for v in self.vehiculos if v.posicion.y < 300)
        sur = sum(1 for v in self.vehiculos if v.posicion.y > 700)
        este = sum(1 for v in self.vehiculos if v.posicion.x > 800)
        oeste = sum(1 for v in self.vehiculos if v.posicion.x < 400)
        
        zonas_stats = f"Centro:{centro} N:{norte} S:{sur} E:{este} O:{oeste}"
        zonas_surface = font_stats.render(zonas_stats, True, (180, 180, 180))
        self.pantalla.blit(zonas_surface, (20, 205))
    
    def _mostrar_controles(self):
        """Muestra los controles disponibles"""
        font_small = pygame.font.Font(None, 18)
        controles = [
            "CONTROLES:",
            "ESPACIO - Generar vehículo",
            "R - Reiniciar simulación", 
            "T - Cambiar hora del día",
            "C - Mostrar/ocultar calles",
            "M - Modo de vista",
            "F - Vista limpia (sin paneles)",
            "P - Pausar/Reanudar",
            "I - Activar/Desactivar IA",
            "B - Benchmark Automático",
            "V - Restablecer Métricas",
            "ESC - Salir"
        ]
        
        for i, control in enumerate(controles):
            color = (255, 255, 100) if i == 0 else (200, 200, 200)
            superficie = font_small.render(control, True, color)
            self.pantalla.blit(superficie, (ANCHO - 220, 20 + i * 20))
            
    def _mostrar_panel_comparativo(self):
        """Dibuja el panel comparativo premium de escenarios en la parte superior central"""
        font_titulo = pygame.font.Font(None, 20)
        font_headers = pygame.font.Font(None, 16)
        font_body = pygame.font.Font(None, 15)
        font_alert = pygame.font.Font(None, 18)
        
        panel_ancho = 640
        panel_alto = 220
        panel_x = 400
        panel_y = 10
        
        surf = pygame.Surface((panel_ancho, panel_alto), pygame.SRCALPHA)
        surf.fill((10, 18, 30, 215))
        pygame.draw.rect(surf, (40, 80, 150, 160), surf.get_rect(), 2)
        self.pantalla.blit(surf, (panel_x, panel_y))
        
        tit_texto = "📊 COMPARATIVA DE ESCENARIOS (CON IA vs SIN IA)"
        tit_surf = font_titulo.render(tit_texto, True, (150, 210, 255))
        self.pantalla.blit(tit_surf, (panel_x + 20, panel_y + 12))
        
        if self.benchmark_activo:
            fase_txt = "SIN IA (Fase 1/2)" if self.benchmark_fase == 1 else "CON IA (Fase 2/2)"
            progreso = int(100 * (self.benchmark_frames_fase - self.benchmark_frames_restantes) / self.benchmark_frames_fase)
            info_txt = f"⚙️ BENCHMARK EN CURSO: {fase_txt} | {progreso}%"
            info_color = (255, 180, 50)
            
            pygame.draw.rect(self.pantalla, (50, 50, 50), (panel_x + 20, panel_y + 35, panel_ancho - 40, 6))
            pygame.draw.rect(self.pantalla, info_color, (panel_x + 20, panel_y + 35, int((panel_ancho - 40) * progreso / 100), 6))
        elif self.benchmark_fase == 3:
            info_txt = "🏆 BENCHMARK COMPLETADO (Presiona V para limpiar)"
            info_color = (50, 255, 120)
        else:
            status_ia = "ACTIVADO (Escenario 2)" if self.ia_activa else "DESACTIVADO (Escenario 1)"
            info_txt = f"🤖 MODO IA: {status_ia}"
            info_color = (120, 255, 160) if self.ia_activa else (255, 100, 100)
            
        info_surf = font_alert.render(info_txt, True, info_color)
        self.pantalla.blit(info_surf, (panel_x + panel_ancho - info_surf.get_width() - 20, panel_y + 12))
        
        pygame.draw.line(self.pantalla, (30, 65, 120), (panel_x + 15, panel_y + 45), (panel_x + panel_ancho - 15, panel_y + 45), 1)
        
        hdrs = ["MÉTRICA", "ESC. 1 (SIN IA)", "ESC. 2 (CON IA)", "MEJORA %"]
        col_x = [panel_x + 20, panel_x + 230, panel_x + 370, panel_x + 510]
        
        for h, text in enumerate(hdrs):
            hdr_surf = font_headers.render(text, True, (100, 170, 240) if h == 0 else (170, 190, 220))
            self.pantalla.blit(hdr_surf, (col_x[h], panel_y + 53))
            
        pygame.draw.line(self.pantalla, (35, 70, 130), (panel_x + 15, panel_y + 68), (panel_x + panel_ancho - 15, panel_y + 68), 1)
        
        s_frames = max(1, self.stats_sin_ia['frames'])
        c_frames = max(1, self.stats_con_ia['frames'])
        
        c_sin = self.stats_sin_ia['congestion_acumulada'] / s_frames
        c_con = self.stats_con_ia['congestion_acumulada'] / c_frames
        
        v_sin = self.stats_sin_ia['velocidad_acumulada'] / s_frames
        v_con = self.stats_con_ia['velocidad_acumulada'] / c_frames
        
        d_sin = self.stats_sin_ia['detenidos_acumulados'] / s_frames
        d_con = self.stats_con_ia['detenidos_acumulados'] / c_frames
        
        esp_sin = (self.stats_sin_ia['tiempo_espera_total'] / max(1, self.stats_sin_ia['vehiculos_unicos'])) / 60.0
        esp_con = (self.stats_con_ia['tiempo_espera_total'] / max(1, self.stats_con_ia['vehiculos_unicos'])) / 60.0
        
        flujo_sin = self.stats_sin_ia['vehiculos_completados'] / max(0.1, (s_frames / 3600.0))
        flujo_con = self.stats_con_ia['vehiculos_completados'] / max(0.1, (c_frames / 3600.0))
        
        desv_sin = self.stats_sin_ia['vehiculos_desviados']
        desv_con = self.stats_con_ia['vehiculos_desviados']
        
        ef_sin = 100.0 * self.stats_sin_ia['tiempo_movimiento_total'] / max(1, self.stats_sin_ia['tiempo_movimiento_total'] + self.stats_sin_ia['tiempo_espera_semaforo'])
        ef_con = 100.0 * self.stats_con_ia['tiempo_movimiento_total'] / max(1, self.stats_con_ia['tiempo_movimiento_total'] + self.stats_con_ia['tiempo_espera_semaforo'])
        
        metricas_lista = [
            ("Congestión Promedio", c_sin, c_con, "{:.1f}%", "lower_better"),
            ("Velocidad Promedio", v_sin, v_con, "{:.2f} px/f", "higher_better"),
            ("Vehículos Detenidos (Prom)", d_sin, d_con, "{:.1f}", "lower_better"),
            ("Espera Promedio por Veh.", esp_sin, esp_con, "{:.1f} s", "lower_better"),
            ("Flujo Vehicular (Completados)", flujo_sin, flujo_con, "{:.1f} /min", "higher_better"),
            ("Vehículos Desviados por IA", desv_sin, desv_con, "{:d}", "none"),
            ("Efectividad Semáforos", ef_sin, ef_con, "{:.1f}%", "higher_better")
        ]
        
        for idx, (name, val_sin, val_con, fmt, mejora) in enumerate(metricas_lista):
            row_y = panel_y + 73 + idx * 19
            
            lbl = font_body.render(name, True, (210, 220, 235))
            self.pantalla.blit(lbl, (col_x[0], row_y))
            
            has_data_sin = self.stats_sin_ia['frames'] > 0 or (name == "Vehículos Desviados por IA" and self.stats_sin_ia['vehiculos_unicos'] > 0)
            has_data_con = self.stats_con_ia['frames'] > 0 or (name == "Vehículos Desviados por IA" and self.stats_con_ia['vehiculos_unicos'] > 0)
            
            txt_sin = fmt.format(val_sin) if has_data_sin else "---"
            txt_con = fmt.format(val_con) if has_data_con else "---"
            
            val_sin_surf = font_body.render(txt_sin, True, (160, 170, 185))
            self.pantalla.blit(val_sin_surf, (col_x[1], row_y))
            
            val_con_surf = font_body.render(txt_con, True, (255, 255, 255) if self.ia_activa else (160, 170, 185))
            self.pantalla.blit(val_con_surf, (col_x[2], row_y))
            
            txt_mejora = "---"
            color_mejora = (160, 170, 185)
            
            if has_data_sin and has_data_con and mejora != "none":
                if mejora == 'lower_better':
                    if val_sin > 0:
                        pct = 100 * (val_sin - val_con) / val_sin
                        sign = "+" if pct >= 0 else ""
                        txt_mejora = f"{sign}{pct:.1f}%"
                        color_mejora = (50, 255, 120) if pct >= 0 else (255, 80, 80)
                    elif val_con == 0 and val_sin == 0:
                        txt_mejora = "+0.0%"
                        color_mejora = (50, 255, 120)
                elif mejora == 'higher_better':
                    if val_sin > 0:
                        pct = 100 * (val_con - val_sin) / val_sin
                        sign = "+" if pct >= 0 else ""
                        txt_mejora = f"{sign}{pct:.1f}%"
                        color_mejora = (50, 255, 120) if pct >= 0 else (255, 80, 80)
                    elif val_con == 0 and val_sin == 0:
                        txt_mejora = "+0.0%"
                        color_mejora = (50, 255, 120)
                        
            elif name == "Vehículos Desviados por IA" and has_data_con:
                txt_mejora = f"{val_con:d} total"
                color_mejora = (150, 210, 255)
                
            mejora_surf = font_body.render(txt_mejora, True, color_mejora)
            self.pantalla.blit(mejora_surf, (col_x[3], row_y))
            
            if idx < len(metricas_lista) - 1:
                pygame.draw.line(self.pantalla, (20, 40, 80, 40), (panel_x + 15, row_y + 16), (panel_x + panel_ancho - 15, row_y + 16), 1)

    def ejecutar(self):
        """Bucle principal mejorado de la simulación ampliada"""
        ejecutando = True
        pausado = False
        mostrar_calles = True
        modo_vista = 'normal'
        modo_mapa_limpio = False
        tiempo_inicio = time.time()
        
        while ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        self._generar_vehiculo_inteligente()
                    elif evento.key == pygame.K_r:
                        self.vehiculos.clear()
                        self._sync_indice_vehiculos()
                        self.vehiculos_generados = 0
                        self.estadisticas = {k: 0 for k in self.estadisticas.keys()}
                        print("Simulación reiniciada")
                    elif evento.key == pygame.K_t:
                        self.hora_simulada = (self.hora_simulada + 2) % 24
                        print(f"Hora cambiada a: {int(self.hora_simulada):02d}:00")
                    elif evento.key == pygame.K_c:
                        mostrar_calles = not mostrar_calles
                        print(f"Calles {'visibles' if mostrar_calles else 'ocultas'}")
                    elif evento.key == pygame.K_m:
                        modos = ['normal', 'densidad', 'velocidad']
                        idx_actual = modos.index(modo_vista)
                        modo_vista = modos[(idx_actual + 1) % len(modos)]
                        print(f"Modo de vista: {modo_vista}")
                    elif evento.key == pygame.K_p:
                        pausado = not pausado
                        print(f"Simulación {'pausada' if pausado else 'reanudada'}")
                    elif evento.key == pygame.K_i:
                        self.ia_activa = not self.ia_activa
                        print(f"IA {'activada' if self.ia_activa else 'desactivada'}")
                        if not self.ia_activa:
                            for sem in self.semaforos:
                                sem.restaurar_original()
                            self.ia_trafico.zonas_con_ingreso_reducido.clear()
                            self.ia_trafico.zonas_con_desvio_activo.clear()
                            self.ia_trafico._registrar_accion("IA: Desactivada por usuario")
                        else:
                            self.ia_trafico._registrar_accion("IA: Activada por usuario")
                    elif evento.key == pygame.K_v:
                        for stats in [self.stats_sin_ia, self.stats_con_ia]:
                            for k in stats.keys():
                                stats[k] = 0
                        print("Estadísticas de escenarios restablecidas")
                        self.ia_trafico._registrar_accion("IA: Estadísticas comparativas borradas")
                    elif evento.key == pygame.K_b:
                        self.benchmark_activo = True
                        self.benchmark_fase = 1
                        self.ia_activa = False
                        self.benchmark_frames_restantes = self.benchmark_frames_fase
                        self.vehiculos.clear()
                        self._sync_indice_vehiculos()
                        self.vehiculos_generados = 0
                        self.estadisticas = {k: 0 for k in self.estadisticas.keys()}
                        for stats in [self.stats_sin_ia, self.stats_con_ia]:
                            for k in stats.keys():
                                stats[k] = 0
                        for sem in self.semaforos:
                            sem.restaurar_original()
                        self.ia_trafico.zonas_con_ingreso_reducido.clear()
                        self.ia_trafico.zonas_con_desvio_activo.clear()
                        self.ia_trafico.log_acciones.clear()
                        self.ia_trafico._registrar_accion("IA: Iniciando Benchmark...")
                        print("Benchmark Automático Iniciado: Fase 1 (Sin IA)")
                    elif evento.key == pygame.K_f:
                        modo_mapa_limpio = not modo_mapa_limpio
                        estado = 'ACTIVADO' if modo_mapa_limpio else 'DESACTIVADO'
                        print(f"Modo mapa limpio: {estado}")
                    elif evento.key == pygame.K_ESCAPE:
                        ejecutando = False
            
            if not pausado:
                self.ia_trafico._cache_semaforo.clear()
                self.hora_simulada += 0.001
                if self.hora_simulada >= 24:
                    self.hora_simulada = 0
                
                if len(self.vehiculos) < 120:
                    self._generar_vehiculo_inteligente()
                
                for semaforo in self.semaforos:
                    semaforo.actualizar()
                
                self._actualizar_vehiculos()
                
                self._actualizar_estadisticas()
                self.ia_trafico.actualizar()
                
                active_stats = self.stats_con_ia if self.ia_activa else self.stats_sin_ia
                active_stats['frames'] += 1
                
                if active_stats['frames'] % 60 == 0:
                    self.gestor_metricas.guardar_historial()
                active_stats['congestion_acumulada'] += self.estadisticas['congestion']
                active_stats['velocidad_acumulada'] += self.estadisticas['promedio_velocidad']
                
                vehiculos_detenidos = sum(1 for v in self.vehiculos if v.velocidad_actual < 0.2)
                active_stats['detenidos_acumulados'] += vehiculos_detenidos
                active_stats['tiempo_espera_total'] += vehiculos_detenidos
                
                veh_mov = sum(1 for v in self.vehiculos if v.velocidad_actual >= 0.2)
                veh_semaforo = sum(1 for v in self.vehiculos if v.velocidad_actual < 0.2 and self.ia_trafico._vehiculo_detenido_por_semaforo(v))
                active_stats['tiempo_movimiento_total'] += veh_mov
                active_stats['tiempo_espera_semaforo'] += veh_semaforo
                
                if self.benchmark_activo:
                    self.benchmark_frames_restantes -= 1
                    if self.benchmark_frames_restantes <= 0:
                        if self.benchmark_fase == 1:
                            self.benchmark_fase = 2
                            self.ia_activa = True
                            self.benchmark_frames_restantes = self.benchmark_frames_fase
                            self.vehiculos.clear()
                            self._sync_indice_vehiculos()
                            self.vehiculos_generados = 0
                            self.estadisticas = {k: 0 for k in self.estadisticas.keys()}
                            self.ia_trafico.log_acciones.clear()
                            self.ia_trafico._registrar_accion("IA: Benchmark - Fase 2 (Con IA)")
                            print("Benchmark Automático: Fase 2 (Con IA)")
                        elif self.benchmark_fase == 2:
                            self.benchmark_activo = False
                            self.benchmark_fase = 3
                            pausado = True
                            self.ia_trafico._registrar_accion("IA: Benchmark finalizado")
                            print("Benchmark Automático completado. Resultados listos.")
            
            if mostrar_calles:
                self._dibujar_mapa_detallado()
            else:
                self.pantalla.fill(COLORES['FONDO'])
            
            self.ia_trafico.dibujar_zonas(self.pantalla)
            
            if modo_vista == 'densidad':
                self._dibujar_mapa_densidad()
            elif modo_vista == 'velocidad':
                self._dibujar_mapa_velocidad()
            
            for semaforo in self.semaforos:
                semaforo.dibujar(self.pantalla)
            
            for vehiculo in self.vehiculos:
                vehiculo.dibujar(self.pantalla)
            
            if pausado:
                font_pausa = pygame.font.Font(None, 48)
                texto_pausa = font_pausa.render("PAUSADO", True, (255, 255, 0))
                rect_pausa = texto_pausa.get_rect(center=(ANCHO//2, 50))
                self.pantalla.blit(texto_pausa, rect_pausa)
            
            if not modo_mapa_limpio:
                self._mostrar_estadisticas_avanzadas()
                self._mostrar_controles()
                self._mostrar_panel_comparativo()
                self.ia_trafico.dibujar_panel(self.pantalla)
            
            font_btn = pygame.font.Font(None, 20)
            if modo_mapa_limpio:
                btn_text = "[F] Mostrar paneles"
                btn_color = (80, 220, 120)
                bg_color = (10, 60, 20, 200)
            else:
                btn_text = "[F] Vista limpia"
                btn_color = (200, 200, 200)
                bg_color = (20, 20, 40, 180)
            btn_surf = font_btn.render(btn_text, True, btn_color)
            btn_w = btn_surf.get_width() + 16
            btn_h = btn_surf.get_height() + 8
            btn_x = ANCHO - btn_w - 8
            btn_y = ALTO - btn_h - 8
            bg_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            bg_surf.fill(bg_color)
            pygame.draw.rect(bg_surf, btn_color, (0, 0, btn_w, btn_h), 1)
            self.pantalla.blit(bg_surf, (btn_x, btn_y))
            self.pantalla.blit(btn_surf, (btn_x + 8, btn_y + 4))
            
            pygame.display.flip()
            self.reloj.tick(FPS)
            
        pygame.quit()

    def _dibujar_mapa_densidad(self):
        """Modo de vista que muestra densidad de tráfico por zonas"""
        tamano_celda = 100
        for x in range(0, ANCHO, tamano_celda):
            for y in range(0, ALTO, tamano_celda):
                vehiculos_en_celda = sum(1 for v in self.vehiculos 
                                       if x <= v.posicion.x < x + tamano_celda 
                                       and y <= v.posicion.y < y + tamano_celda)
                if vehiculos_en_celda > 0:
                    intensidad = min(255, vehiculos_en_celda * 30)
                    color = (intensidad, 255 - intensidad, 0, 100)
                    
                    superficie = pygame.Surface((tamano_celda, tamano_celda))
                    superficie.set_alpha(100)
                    superficie.fill(color[:3])
                    self.pantalla.blit(superficie, (x, y))
    
    def _dibujar_mapa_velocidad(self):
        """Modo de vista que muestra velocidades promedio por zona"""
        for vehiculo in self.vehiculos:
            if vehiculo.velocidad_actual > 0:
                longitud = vehiculo.velocidad_actual * 15
                end_x = vehiculo.posicion.x + math.cos(vehiculo.direccion) * longitud
                end_y = vehiculo.posicion.y + math.sin(vehiculo.direccion) * longitud
                
                factor_vel = vehiculo.velocidad_actual / vehiculo.velocidad_maxima
                if factor_vel > 0.8:
                    color = (0, 255, 0)
                elif factor_vel > 0.5:
                    color = (255, 255, 0)
                else:
                    color = (255, 0, 0)
                
                pygame.draw.line(self.pantalla, color, 
                               (vehiculo.posicion.x, vehiculo.posicion.y),
                               (end_x, end_y), 3)

class _HeadlessCentro(SimulacionTrafico):
    """SimulacionTrafico en modo headless: sin ventana, sin bucle principal."""
    def __init__(self):
        import time as _time
        self.pantalla = pygame.Surface((ANCHO, ALTO))
        self.reloj    = pygame.time.Clock()
        self.vehiculos = []
        self.semaforos = []
        self.calles    = self._crear_red_calles_cusco_ampliada()
        self._crear_semaforos_estrategicos_ampliados()
        self.vehiculos_generados       = 0
        self.tiempo_ultima_generacion  = _time.time()
        self.estadisticas = {'autos':0,'combis':0,'motos':0,'taxis':0,
                             'promedio_velocidad':0,'congestion':0}
        self.patrones_horarios = self._crear_patrones_horarios()
        self.hora_simulada  = 8.0
        self.ia_activa      = True
        _s0 = {'frames':0,'congestion_acumulada':0.0,'velocidad_acumulada':0.0,
               'detenidos_acumulados':0,'tiempo_espera_total':0,'vehiculos_unicos':0,
               'vehiculos_completados':0,'vehiculos_desviados':0,
               'tiempo_movimiento_total':0,'tiempo_espera_semaforo':0}
        self.stats_sin_ia = dict(_s0)
        self.stats_con_ia = dict(_s0)
        self.benchmark_activo = False
        self.benchmark_fase   = 0
        self.benchmark_frames_fase      = 1000
        self.benchmark_frames_restantes = 0
        self.ia_trafico      = GestorIATrafico(self)
        self.gestor_metricas = GestorMetricas(self)
        self.nodos_interseccion = set()
        for c in self.calles:
            self.nodos_interseccion.add((int(c.inicio.x), int(c.inicio.y)))
            self.nodos_interseccion.add((int(c.fin.x),   int(c.fin.y)))
        self.adyacencias = {n: [] for n in self.nodos_interseccion}
        for c in self.calles:
            sn = (int(c.inicio.x), int(c.inicio.y))
            en = (int(c.fin.x),   int(c.fin.y))
            self.adyacencias[sn].append((en, c))

        self._mapa_estatico = None
        self._indice_semaforos = IndiceEspacial(100)
        self._inicializar_indices()

    def paso(self):
        self.ia_trafico._cache_semaforo.clear()
        self.hora_simulada += 0.001
        if self.hora_simulada >= 24: self.hora_simulada = 0
        if len(self.vehiculos) < 120:
            self._generar_vehiculo_inteligente()
        for sem in self.semaforos:
            sem.actualizar()
        self._actualizar_vehiculos()
        self._actualizar_estadisticas()
        self.ia_trafico.actualizar()
        active = self.stats_con_ia if self.ia_activa else self.stats_sin_ia
        active['frames'] += 1
        if active['frames'] % 60 == 0:
            self.gestor_metricas.guardar_historial()
        active['congestion_acumulada']  += self.estadisticas['congestion']
        active['velocidad_acumulada']   += self.estadisticas['promedio_velocidad']
        vd  = sum(1 for v in self.vehiculos if v.velocidad_actual < 0.2)
        vm  = sum(1 for v in self.vehiculos if v.velocidad_actual >= 0.2)
        vsem= sum(1 for v in self.vehiculos if v.velocidad_actual < 0.2
                  and self.ia_trafico._vehiculo_detenido_por_semaforo(v))
        active['detenidos_acumulados']  += vd
        active['tiempo_espera_total']   += vd
        active['tiempo_movimiento_total']+= vm
        active['tiempo_espera_semaforo'] += vsem

    def renderizar(self, superficie: pygame.Surface):
        self.pantalla = superficie
        self._dibujar_mapa_detallado()
        self.ia_trafico.dibujar_zonas(superficie)
        for sem in self.semaforos: sem.dibujar(superficie)
        for v   in self.vehiculos: v.dibujar(superficie)

    def ejecutar(self):
        raise RuntimeError("Usar EjecutorSimulacion en lugar de ejecutar() directamente.")

if __name__ == "__main__":
    print("SIMULACIÓN AMPLIADA DE TRÁFICO - CENTRO HISTÓRICO DEL CUSCO")
    sim = SimulacionTrafico()
    sim.ejecutar()
