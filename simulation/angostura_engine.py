# -*- coding: utf-8 -*-

import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time

ANCHO = 1600
ALTO  = 900
FPS   = 60

from simulation.road import COLORES, DireccionCalle, Punto, Calle
from simulation.vehicle import TipoVehiculo, Vehiculo
from simulation.traffic_light import EstadoSemaforo, FaseSemaforo, Semaforo
from simulation.metrics import GestorMetricas
from simulation.controllers.ai_controller import GestorIATrafico

class SimulacionAngostura:
    def __init__(self):
        self.pantalla = pygame.Surface((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.vehiculos: List[Vehiculo] = []
        self.semaforos: List[Semaforo] = []
        self.calles:    List[Calle]    = self._crear_red_calles()
        self._crear_semaforos()
        self.vehiculos_generados = 0
        self.tiempo_ultima_generacion = time.time()
        self.estadisticas = {
            'autos': 0, 'pickups': 0, 'buses': 0, 'transp_urbanos': 0,
            'camiones_ligeros': 0, 'camiones_medianos': 0, 'camiones_pesados': 0,
            'articulados': 0, 'promedio_velocidad': 0, 'congestion': 0,
        }
        self.patrones_horarios = self._crear_patrones_horarios()
        self.hora_simulada = 8.0
        self.ia_activa = True
        _stats0 = {'frames':0,'congestion_acumulada':0.0,'velocidad_acumulada':0.0,
                   'detenidos_acumulados':0,'tiempo_espera_total':0,'vehiculos_unicos':0,
                   'vehiculos_completados':0,'vehiculos_desviados':0,
                   'tiempo_movimiento_total':0,'tiempo_espera_semaforo':0}
        self.stats_sin_ia = dict(_stats0)
        self.stats_con_ia = dict(_stats0)
        self.benchmark_activo = False
        self.benchmark_fase = 0
        self.benchmark_frames_fase = 1000
        self.benchmark_frames_restantes = 0
        self.ia_trafico   = GestorIATrafico(self, is_angostura=True)
        self.gestor_metricas = GestorMetricas(self)
        self.nodos_interseccion: set = set()
        for c in self.calles:
            self.nodos_interseccion.add((int(c.inicio.x), int(c.inicio.y)))
            self.nodos_interseccion.add((int(c.fin.x),   int(c.fin.y)))
        self.adyacencias = {n: [] for n in self.nodos_interseccion}
        for c in self.calles:
            sn = (int(c.inicio.x), int(c.inicio.y))
            en = (int(c.fin.x),   int(c.fin.y))
            self.adyacencias[sn].append((en, c))

        self._edificios_cache = self._precomputar_edificios()

    def _precomputar_edificios(self) -> list:
        import math as _m
        SX = ANCHO / 1200; SY = ALTO / 568
        def px(x): return round(x * SX)
        def py(y): return round(y * SY)

        def dist_seg(p, s1, s2):
            px2, py2 = p; x1, y1 = s1; x2, y2 = s2
            dx, dy = x2-x1, y2-y1
            if dx == 0 and dy == 0:
                return _m.sqrt((px2-x1)**2 + (py2-y1)**2)
            t = max(0, min(1, ((px2-x1)*dx + (py2-y1)*dy) / (dx*dx + dy*dy)))
            return _m.sqrt((px2-x1-t*dx)**2 + (py2-y1-t*dy)**2)

        road_paths_raw = [
            ([(0, 400), (100, 405), (200, 410), (250, 412), (400, 420), (480, 430), (600, 445), (780, 477), (800, 480), (950, 510), (1000, 520), (1135, 545), (1207, 560)], 24),
            ([(480, 225), (650, 225), (800, 250), (940, 310), (1100, 370)], 16),
            ([(200, 140), (480, 140)], 14),
            ([(200, 140), (200, 320)], 14),
            ([(200, 320), (480, 320)], 14),
            ([(480, 140), (480, 430)], 14),
            ([(780, 248), (780, 477)], 14),
            ([(950, 312), (950, 510)], 14),
            ([(1100, 370), (1125, 460), (1135, 545)], 14),
            ([(780, 0), (780, 248)], 14),
            ([(40, 568), (80, 430), (120, 350), (200, 350), (250, 412)], 14),
        ]
        road_paths_px = [
            ([(px(x), py(y)) for x, y in path], w)
            for path, w in road_paths_raw
        ]

        rio_raw = [(30,0),(55,100),(100,150),(350,60),(550,65),(750,65),(900,110),(1020,190),(1100,310),(1180,460),(1207,510)]
        rio_px = [(px(x), py(y)) for x, y in rio_raw]
        rio_branch_raw = [(100,150),(150,250),(110,350),(60,430),(30,568)]
        rio_branch_px = [(px(x), py(y)) for x, y in rio_branch_raw]

        railway_raw = [(0, 370), (100, 375), (200, 380), (400, 390), (600, 415), (800, 450), (1000, 490), (1207, 530)]
        railway_px  = [(px(x), py(y)) for x, y in railway_raw]

        building_colors = [
            COLORES['EDIFICIO_COLONIAL'], COLORES['EDIFICIO_MODERNO'],
            (210, 180, 140), COLORES['TIERRA'], COLORES['PIEDRA'],
        ]

        rng = random.Random(42)

        step_x = max(1, round(25 * SX))
        step_y = max(1, round(20 * SY))

        schools_data = [
            (290, 160, 120, 36, (190, 70, 50)),
            (210, 160, 70, 36, (170, 90, 70))
        ]

        edificios = []
        for sx_c, sy_c, sw_c, sh_c, scolor in schools_data:
            edificios.append((px(sx_c), py(sy_c), px(sw_c), py(sh_c), scolor))

        for gx in range(step_x, ANCHO, step_x):
            for gy in range(step_y, ALTO, step_y):
                in_school = False
                for sx_c, sy_c, sw_c, sh_c, _ in schools_data:
                    if px(sx_c - 10) <= gx <= px(sx_c + sw_c + 10) and py(sy_c - 10) <= gy <= py(sy_c + sh_c + 10):
                        in_school = True; break
                if in_school: continue

                bx = gx + rng.randint(-3, 3)
                by = gy + rng.randint(-3, 3)

                too_close = False
                for path, w in road_paths_px:
                    for i in range(len(path) - 1):
                        if dist_seg((bx, by), path[i], path[i+1]) < w * 0.9:
                            too_close = True; break
                    if too_close: break
                if too_close: continue

                for i in range(len(rio_px) - 1):
                    if dist_seg((bx, by), rio_px[i], rio_px[i+1]) < round(32 * min(SX, SY)) * 0.9:
                        too_close = True; break
                if too_close: continue

                for i in range(len(rio_branch_px) - 1):
                    if dist_seg((bx, by), rio_branch_px[i], rio_branch_px[i+1]) < round(32 * min(SX, SY)) * 0.9:
                        too_close = True; break
                if too_close: continue

                for i in range(len(railway_px) - 1):
                    if dist_seg((bx, by), railway_px[i], railway_px[i+1]) < round(14 * min(SX, SY)):
                        too_close = True; break
                if too_close: continue

                bw    = rng.randint(round(12 * SX), round(22 * SX))
                bh    = rng.randint(round(10 * SY), round(18 * SY))
                color = rng.choice(building_colors)
                edificios.append((bx - bw//2, by - bh//2, bw, bh, color))
        return edificios

    def _crear_red_calles(self) -> List[Calle]:
        SX = ANCHO / 1200
        SY = ALTO  / 568
        def P(x, y): return Punto(round(x*SX), round(y*SY))

        calles = []
        calles.extend([
            Calle(P(0,400),   P(100,405), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(100,405), P(200,410), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(200,410), P(250,412), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(250,412), P(400,420), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(400,420), P(480,430), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(480,430), P(600,445), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(600,445), P(780,477), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(780,477), P(800,480), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(800,480), P(950,510), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(950,510), P(1000,520),45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(1000,520),P(1135,545),45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(1135,545),P(1207,560),45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
        ])

        calles.extend([
            Calle(P(1207,560),P(1135,545),45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(1135,545),P(1000,520),45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(1000,520),P(950,510), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(950,510), P(800,480), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(800,480), P(780,477), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(780,477), P(600,445), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(600,445), P(480,430), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(480,430), P(400,420), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(400,420), P(250,412), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(250,412), P(200,410), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(200,410), P(100,405), 45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
            Calle(P(100,405), P(0,400),   45, 'principal', DireccionCalle.HORIZONTAL, 3.0),
        ])

        calles.extend([
            Calle(P(200,140), P(480,140), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.2),
            Calle(P(480,140), P(200,140), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.2),
        ])

        calles.extend([
            Calle(P(200,140), P(200,320), 28, 'secundaria', DireccionCalle.VERTICAL,   2.2),
            Calle(P(200,320), P(200,140), 28, 'secundaria', DireccionCalle.VERTICAL,   2.2),
        ])

        calles.extend([
            Calle(P(200,320), P(480,320), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.2),
            Calle(P(480,320), P(200,320), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.2),
        ])

        calles.extend([
            Calle(P(480,225), P(650,225), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.2),
            Calle(P(650,225), P(800,250), 28, 'secundaria', DireccionCalle.DIAGONAL,   2.0),
            Calle(P(800,250), P(940,310), 28, 'secundaria', DireccionCalle.DIAGONAL,   2.0),
            Calle(P(940,310), P(1100,370),28, 'secundaria', DireccionCalle.DIAGONAL,   2.0),

            Calle(P(1100,370),P(940,310), 28, 'secundaria', DireccionCalle.DIAGONAL,   2.0),
            Calle(P(940,310), P(800,250), 28, 'secundaria', DireccionCalle.DIAGONAL,   2.0),
            Calle(P(800,250), P(650,225), 28, 'secundaria', DireccionCalle.DIAGONAL,   2.0),
            Calle(P(650,225), P(480,225), 28, 'secundaria', DireccionCalle.HORIZONTAL, 2.2),
        ])

        calles.extend([
            Calle(P(480,140), P(480,225), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(480,225), P(480,320), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(480,320), P(480,430), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),

            Calle(P(480,430), P(480,320), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(480,320), P(480,225), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(480,225), P(480,140), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
        ])

        calles.extend([
            Calle(P(780,248), P(780,350), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(780,350), P(780,477), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(780,477), P(780,350), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(780,350), P(780,248), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
        ])

        calles.extend([
            Calle(P(950,312), P(950,420), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(950,420), P(950,510), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(950,510), P(950,420), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(950,420), P(950,312), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
        ])

        calles.extend([
            Calle(P(1100,370),P(1125,460), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(P(1125,460),P(1135,545), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(P(1135,545),P(1125,460), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(P(1125,460),P(1100,370), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
        ])

        calles.extend([
            Calle(P(780,0),   P(780,65),  22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(780,65),  P(780,248), 22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(780,248), P(780,65),  22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
            Calle(P(780,65),  P(780,0),   22, 'secundaria', DireccionCalle.VERTICAL, 1.8),
        ])

        calles.extend([
            Calle(P(40,568),  P(80,430),  28, 'bypass', DireccionCalle.DIAGONAL,   3.5),
            Calle(P(80,430),  P(120,350), 28, 'bypass', DireccionCalle.DIAGONAL,   3.5),
            Calle(P(120,350), P(200,350), 28, 'bypass', DireccionCalle.HORIZONTAL, 3.5),
            Calle(P(200,350), P(250,412), 28, 'bypass', DireccionCalle.DIAGONAL,   3.5),

            Calle(P(250,412), P(200,350), 28, 'bypass', DireccionCalle.DIAGONAL,   3.5),
            Calle(P(200,350), P(120,350), 28, 'bypass', DireccionCalle.HORIZONTAL, 3.5),
            Calle(P(120,350), P(80,430),  28, 'bypass', DireccionCalle.DIAGONAL,   3.5),
            Calle(P(80,430),  P(40,568),  28, 'bypass', DireccionCalle.DIAGONAL,   3.5),
        ])

        calles.extend([
            Calle(P(780,248), P(800,250), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(P(800,250), P(780,248), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(P(940,310), P(950,312), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
            Calle(P(950,312), P(940,310), 22, 'secundaria', DireccionCalle.DIAGONAL, 1.8),
        ])
        return calles

    def _crear_semaforos(self):
        SX = ANCHO / 1200; SY = ALTO / 568
        def P(x, y): return Punto(round(x*SX), round(y*SY))

        intersecciones = [
            (P(480,140), 'principal'),
            (P(480,225), 'principal'),
            (P(780,248), 'principal'),
            (P(950,312), 'principal'),
            (P(1100,370), 'normal'),
            (P(1135,545), 'normal'),
            (P(480,430), 'normal'),
            (P(780,477), 'normal'),
            (P(950,510), 'normal'),
            (P(780,65),  'normal'),
        ]
        for posicion, tipo in intersecciones:
            self.semaforos.append(Semaforo(posicion, tipo))

    def _crear_patrones_horarios(self) -> dict:
        TV = TipoVehiculo
        return {
            'pico_manana': {
                'factor': 1.5,
                'tipos': [
                    TV.AUTO, TV.AUTO, TV.AUTO,
                    TV.PICKUP, TV.PICKUP,
                    TV.TRANSP_URBANO, TV.TRANSP_URBANO, TV.TRANSP_URBANO,
                    TV.BUS,
                    TV.CAMION_LIGERO,
                ],
            },
            'manana': {
                'factor': 1.0,
                'tipos': [
                    TV.AUTO, TV.AUTO,
                    TV.PICKUP,
                    TV.TRANSP_URBANO, TV.TRANSP_URBANO,
                    TV.BUS,
                    TV.CAMION_LIGERO, TV.CAMION_LIGERO,
                    TV.CAMION_MEDIANO,
                ],
            },
            'mediodia': {
                'factor': 0.8,
                'tipos': [
                    TV.AUTO, TV.AUTO,
                    TV.PICKUP,
                    TV.CAMION_LIGERO, TV.CAMION_LIGERO,
                    TV.CAMION_MEDIANO, TV.CAMION_MEDIANO,
                    TV.CAMION_PESADO,
                    TV.ARTICULADO,
                ],
            },
            'pico_tarde': {
                'factor': 1.5,
                'tipos': [
                    TV.AUTO, TV.AUTO, TV.AUTO,
                    TV.PICKUP, TV.PICKUP,
                    TV.TRANSP_URBANO, TV.TRANSP_URBANO, TV.TRANSP_URBANO,
                    TV.BUS,
                    TV.CAMION_LIGERO,
                    TV.CAMION_MEDIANO,
                ],
            },
            'noche': {
                'factor': 0.7,
                'tipos': [
                    TV.AUTO, TV.AUTO,
                    TV.PICKUP,
                    TV.CAMION_LIGERO,
                    TV.CAMION_MEDIANO, TV.CAMION_MEDIANO,
                    TV.CAMION_PESADO, TV.CAMION_PESADO,
                    TV.ARTICULADO,
                ],
            },
            'madrugada': {
                'factor': 0.3,
                'tipos': [
                    TV.AUTO,
                    TV.CAMION_MEDIANO,
                    TV.CAMION_PESADO, TV.CAMION_PESADO,
                    TV.ARTICULADO, TV.ARTICULADO,
                ],
            },
        }

    def _puntos_acceso_red(self) -> tuple[list[Punto], list[Punto]]:
        perimetro = [
            Punto(0,    400),
            Punto(1207, 560),
            Punto(40,   568),
            Punto(780,  0),
        ]
        internos = [
            Punto(340, 140),
            Punto(200, 230),
            Punto(340, 320),
            Punto(480, 280),
            Punto(565, 225),
            Punto(820, 280),
            Punto(780, 248),
            Punto(950, 312),
            Punto(1020, 340),
        ]
        return perimetro, internos

    def _distancia_punto_a_calle(self, punto: Punto, calle: Calle) -> tuple[float, float]:
        SX = ANCHO / 1200
        SY = ALTO / 568
        px, py = punto.x, punto.y
        x1, y1 = calle.inicio.x / SX, calle.inicio.y / SY
        x2, y2 = calle.fin.x / SX, calle.fin.y / SY
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2), 0.0
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2), t

    def _calle_opuesta(self, calle: Calle) -> Calle | None:
        for c2 in self.calles:
            if (c2.inicio.distancia_a(calle.fin) < 10 and
                    c2.fin.distancia_a(calle.inicio) < 10 and c2 is not calle):
                return c2
        return None

    def _resolver_calle_en_punto(self, punto: Punto, radio: float = 28) -> Calle | None:
        mejor: Calle | None = None
        mejor_dist = radio
        mejor_t = 0.0
        for c in self.calles:
            if c.tipo == 'bypass':
                continue
            dist, t = self._distancia_punto_a_calle(punto, c)
            if dist < mejor_dist:
                mejor_dist = dist
                mejor = c
                mejor_t = t
        if mejor is None:
            return None
        if mejor_t > 0.55:
            op = self._calle_opuesta(mejor)
            if op:
                mejor = op
        return mejor

    def _resolver_calle_destino_en_punto(self, punto: Punto, radio: float = 28) -> Calle | None:
        mejor: Calle | None = None
        mejor_dist = radio
        mejor_t = 0.0
        for c in self.calles:
            if c.tipo == 'bypass':
                continue
            dist, t = self._distancia_punto_a_calle(punto, c)
            if dist < mejor_dist:
                mejor_dist = dist
                mejor = c
                mejor_t = t
        if mejor is None:
            return None
        if mejor_t < 0.45:
            op = self._calle_opuesta(mejor)
            if op:
                mejor = op
        return mejor

    def _generar_vehiculo_inteligente(self):
        ahora = time.time()
        h = self.hora_simulada
        if   6  <= h < 9:  patron = self.patrones_horarios['pico_manana']
        elif 9  <= h < 12: patron = self.patrones_horarios['manana']
        elif 12 <= h < 14: patron = self.patrones_horarios['mediodia']
        elif 14 <= h < 19: patron = self.patrones_horarios['pico_tarde']
        elif 19 <= h < 22: patron = self.patrones_horarios['noche']
        else:              patron = self.patrones_horarios['madrugada']

        intervalo = random.uniform(1.0,3.0) / patron['factor']
        if ahora - self.tiempo_ultima_generacion < intervalo: return
        if len(self.vehiculos) >= 100: return

        tipo = random.choice(patron['tipos'])

        perimetro, internos = self._puntos_acceso_red()

        if random.random() < 0.55:
            p_spawn = random.choice(internos if random.random() < 0.75 else internos + perimetro)
            candidatos_dest = [p for p in internos + perimetro
                               if p.distancia_a(p_spawn) > 80]
            if not candidatos_dest:
                candidatos_dest = [p for p in perimetro if p.distancia_a(p_spawn) > 80]
            if not candidatos_dest:
                return
            p_dest = random.choice(candidatos_dest)
        else:
            p_spawn = random.choice(perimetro)
            candidatos_dest = [p for p in perimetro if p.distancia_a(p_spawn) > 120]
            if not candidatos_dest:
                return
            p_dest = random.choice(candidatos_dest)

        c_ini = self._resolver_calle_en_punto(p_spawn)
        c_dst = self._resolver_calle_destino_en_punto(p_dest)
        if c_ini is None or c_dst is None:
            return

        if self._calle_bloqueada_por_ia(c_ini):
            return

        pos = Punto(
            c_ini.inicio.x + random.uniform(0, 0.05) * (c_ini.fin.x - c_ini.inicio.x),
            c_ini.inicio.y + random.uniform(0, 0.05) * (c_ini.fin.y - c_ini.inicio.y),
        )
        v = Vehiculo(tipo, pos, c_ini)

        criterio = v.criterio_ruta
        if p_spawn in internos or p_dest in internos:
            criterio = random.choice(['corta', 'comoda', 'economica'])

        ruta = self.obtener_ruta_inteligente(c_ini, c_dst, criterio, v.tipo)
        if len(ruta) <= 1:
            ruta = self._generar_ruta_realista(c_ini)

        if len(ruta) > 1:
            r0 = ruta[0]
            r1 = ruta[1]
            if r1.inicio.distancia_a(r0.fin) < 10 and r1.fin.distancia_a(r0.inicio) < 10:
                ruta = ruta[1:]
                v.calle_actual = ruta[0]
                v.posicion = Punto(
                    v.calle_actual.inicio.x + random.uniform(0, 0.1) * (v.calle_actual.fin.x - v.calle_actual.inicio.x),
                    v.calle_actual.inicio.y + random.uniform(0, 0.1) * (v.calle_actual.fin.y - v.calle_actual.inicio.y)
                )
                v.direccion = v._calcular_direccion_inicial()

        v.establecer_ruta(ruta)
        self.vehiculos.append(v)
        self.vehiculos_generados += 1

        clave_map = {
            TipoVehiculo.AUTO:           'autos',
            TipoVehiculo.PICKUP:         'pickups',
            TipoVehiculo.BUS:            'buses',
            TipoVehiculo.TRANSP_URBANO:  'transp_urbanos',
            TipoVehiculo.CAMION_LIGERO:  'camiones_ligeros',
            TipoVehiculo.CAMION_MEDIANO: 'camiones_medianos',
            TipoVehiculo.CAMION_PESADO:  'camiones_pesados',
            TipoVehiculo.ARTICULADO:     'articulados',
        }
        clave = clave_map.get(tipo)
        if clave:
            self.estadisticas[clave] += 1
        self.tiempo_ultima_generacion = ahora
        active = self.stats_con_ia if self.ia_activa else self.stats_sin_ia
        active['vehiculos_unicos'] += 1

    def _calle_bloqueada_por_ia(self, calle) -> bool:
        for nombre in self.ia_trafico.zonas_con_ingreso_reducido:
            x1,y1,x2,y2 = self.ia_trafico.zonas[nombre]
            for p in [calle.inicio, calle.fin]:
                if x1<=p.x<=x2 and y1<=p.y<=y2: return True
        return False

    def _generar_ruta_realista(self, c_ini: Calle) -> List[Calle]:
        ruta = [c_ini]; ca = c_ini
        for i in range(10):
            if i >= 3:
                f = ca.fin
                if f.x < 80 or f.x > ANCHO-80 or f.y < 80 or f.y > ALTO-80: break
            conectadas = []
            for c in self.calles:
                if c == ca or c in ruta:
                    continue
                if (ca.tipo == 'bypass' and c.tipo not in ('bypass', 'principal')) or \
                   (c.tipo == 'bypass' and ca.tipo not in ('bypass', 'principal')):
                    continue
                if ca.fin.distancia_a(c.inicio) < 60 and c.fin.distancia_a(ca.inicio) > 30:
                    conectadas.append(c)
            if not conectadas: break
            if i >= 5:
                borde = [c for c in conectadas
                         if c.fin.x<80 or c.fin.x>ANCHO-80 or c.fin.y<80 or c.fin.y>ALTO-80]
                ca = random.choice(borde if borde else conectadas)
            else:
                ca = random.choice(conectadas)
            ruta.append(ca)
        return ruta

    def _calcular_peso_calle(self, calle: Calle, criterio: str, tipo: TipoVehiculo) -> float:
        from simulation.intersection import calcular_peso_calle
        return calcular_peso_calle(self, calle, criterio, tipo)

    def obtener_ruta_inteligente(self, c_ini: Calle, c_fin: Calle,
                                  criterio: str, tipo: TipoVehiculo) -> List[Calle]:
        from simulation.intersection import obtener_ruta_inteligente as dijkstra_ruta
        return dijkstra_ruta(self, c_ini, c_fin, criterio, tipo)

    def _actualizar_estadisticas(self):
        if not self.vehiculos:
            self.estadisticas['promedio_velocidad'] = 0
            self.estadisticas['congestion'] = 0
            return
        vel = sum(v.velocidad_actual for v in self.vehiculos)/len(self.vehiculos)
        self.estadisticas['promedio_velocidad'] = vel
        lentos = sum(1 for v in self.vehiculos
                     if v.velocidad_actual < v.velocidad_maxima*0.5
                     and not (self.ia_trafico._vehiculo_detenido_por_semaforo(v)
                               and v.tiempo_espera_acumulado <= 360))
        esc = min(1.0, len(self.vehiculos)/40.0)
        self.estadisticas['congestion'] = min(100.0, (lentos/len(self.vehiculos))*100.0*esc)

    def paso(self):
        self.hora_simulada += 0.001
        if self.hora_simulada >= 24: self.hora_simulada = 0

        h = self.hora_simulada
        if   6  <= h < 9:   prob_gen = 0.55
        elif 9  <= h < 12:  prob_gen = 0.40
        elif 12 <= h < 14:  prob_gen = 0.35
        elif 14 <= h < 19:  prob_gen = 0.55
        elif 19 <= h < 22:  prob_gen = 0.30
        else:               prob_gen = 0.15
        if len(self.vehiculos) < 80 and random.random() < prob_gen:
            self._generar_vehiculo_inteligente()
        for sem in self.semaforos: sem.actualizar()
        for v in self.vehiculos[:]:
            if not v.actualizar(self.vehiculos, self.semaforos):
                if v.indice_ruta >= len(v.ruta):
                    (self.stats_con_ia if self.ia_activa else self.stats_sin_ia)['vehiculos_completados'] += 1
                self.vehiculos.remove(v)
        self._actualizar_estadisticas()
        self.ia_trafico.actualizar()
        active = self.stats_con_ia if self.ia_activa else self.stats_sin_ia
        active['frames'] += 1
        if active['frames'] % 60 == 0: self.gestor_metricas.guardar_historial()
        active['congestion_acumulada']   += self.estadisticas['congestion']
        active['velocidad_acumulada']    += self.estadisticas['promedio_velocidad']
        vd = sum(1 for v in self.vehiculos if v.velocidad_actual < 0.2)
        active['detenidos_acumulados']   += vd
        active['tiempo_espera_total']    += vd
        vm = sum(1 for v in self.vehiculos if v.velocidad_actual >= 0.2)
        vs_sem = sum(1 for v in self.vehiculos
                     if v.velocidad_actual < 0.2
                     and self.ia_trafico._vehiculo_detenido_por_semaforo(v))
        active['tiempo_movimiento_total']  += vm
        active['tiempo_espera_semaforo']   += vs_sem

    def renderizar(self, superficie: pygame.Surface):
        self._dibujar_mapa_detallado(superficie)
        self.ia_trafico.dibujar_zonas(superficie)
        for sem in self.semaforos: sem.dibujar(superficie)
        for v   in self.vehiculos: v.dibujar(superficie)

    def _dibujar_mapa_detallado(self, superficie: pygame.Surface):
        superficie.fill(COLORES['FONDO'])
        SX = ANCHO / 1200; SY = ALTO / 568

        def px(x): return round(x * SX)
        def py(y): return round(y * SY)
        def seg(path, w, color):
            for i in range(len(path)-1):
                pygame.draw.line(superficie, color, path[i], path[i+1], w)

        rio = [(px(30),py(0)),(px(55),py(100)),(px(100),py(150)),(px(350),py(60)),(px(550),py(65)),
               (px(750),py(65)),(px(900),py(110)),(px(1020),py(190)),(px(1100),py(310)),
               (px(1180),py(460)),(px(1207),py(510))]
        seg(rio, round(32*min(SX,SY)), COLORES['RIO'])

        rio_branch = [(px(100),py(150)),(px(150),py(250)),(px(110),py(350)),(px(60),py(430)),(px(30),py(568))]
        seg(rio_branch, round(32*min(SX,SY)), COLORES['RIO'])

        for (ex, ey, ew, eh, ecolor) in self._edificios_cache:
            pygame.draw.rect(superficie, ecolor, (ex, ey, ew, eh))
            pygame.draw.rect(superficie, (40, 40, 40), (ex, ey, ew, eh), 1)

        import math as _m
        for calle in self.calles:
            if calle.tipo == 'bypass':
                continue
            color = (COLORES['ASFALTO'] if calle.tipo=='principal'
                      else COLORES['ASFALTO_VIEJO'])
            dx = calle.fin.x-calle.inicio.x; dy = calle.fin.y-calle.inicio.y
            lg = _m.sqrt(dx*dx+dy*dy)
            if lg > 0:
                ux=-dy/lg; uy=dx/lg; am=calle.ancho/2
                pts = [(calle.inicio.x+ux*am, calle.inicio.y+uy*am),
                       (calle.inicio.x-ux*am, calle.inicio.y-uy*am),
                       (calle.fin.x  -ux*am, calle.fin.y  -uy*am),
                       (calle.fin.x  +ux*am, calle.fin.y  +uy*am)]
                pygame.draw.polygon(superficie, color, pts)
                if calle.tipo=='principal' and calle.ancho>35:
                    pygame.draw.line(superficie, COLORES['LINEA_AMARILLA'],
                                     (int(calle.inicio.x),int(calle.inicio.y)),
                                     (int(calle.fin.x),int(calle.fin.y)), 2)
                else:
                    steps = max(2, int(lg/20))
                    for s in range(steps):
                        if s%2==0:
                            t1=s/steps; t2=(s+1)/steps
                            x1=calle.inicio.x+(calle.fin.x-calle.inicio.x)*t1
                            y1=calle.inicio.y+(calle.fin.y-calle.inicio.y)*t1
                            x2=calle.inicio.x+(calle.fin.x-calle.inicio.x)*t2
                            y2=calle.inicio.y+(calle.fin.y-calle.inicio.y)*t2
                            pygame.draw.line(superficie, COLORES['LINEA_BLANCA'],
                                             (int(x1),int(y1)),(int(x2),int(y2)), 1)

        railway_raw = [(0, 370), (100, 375), (200, 380), (400, 390), (600, 415), (800, 450), (1000, 490), (1207, 530)]
        railway_px  = [(px(x), py(y)) for x, y in railway_raw]
        for i in range(len(railway_px)-1):
            p1,p2 = railway_px[i],railway_px[i+1]
            dx,dy = p2[0]-p1[0],p2[1]-p1[1]; lg=_m.sqrt(dx*dx+dy*dy)
            if lg==0: continue
            nx,ny=-dy/lg,dx/lg
            cur=0
            while cur<lg:
                t=cur/lg
                mx=p1[0]+(p2[0]-p1[0])*t; my=p1[1]+(p2[1]-p1[1])*t
                off=round(6*min(SX,SY))
                pygame.draw.line(superficie,COLORES['DURMIENTE'],
                                 (round(mx+off*nx),round(my+off*ny)),
                                 (round(mx-off*nx),round(my-off*ny)),2)
                cur += round(12*min(SX,SY))
            pygame.draw.line(superficie,COLORES['RIELES'],
                             (round(p1[0]+2*nx),round(p1[1]+2*ny)),
                             (round(p2[0]+2*nx),round(p2[1]+2*ny)),1)
            pygame.draw.line(superficie,COLORES['RIELES'],
                             (round(p1[0]-2*nx),round(p1[1]-2*ny)),
                             (round(p2[0]-2*nx),round(p2[1]-2*ny)),1)

        for calle in self.calles:
            if calle.tipo != 'bypass':
                continue
            color = (55, 55, 65)
            dx = calle.fin.x-calle.inicio.x; dy = calle.fin.y-calle.inicio.y
            lg = _m.sqrt(dx*dx+dy*dy)
            if lg > 0:
                ux=-dy/lg; uy=dx/lg; am=calle.ancho/2
                pts = [(calle.inicio.x+ux*am, calle.inicio.y+uy*am),
                       (calle.inicio.x-ux*am, calle.inicio.y-uy*am),
                       (calle.fin.x  -ux*am, calle.fin.y  -uy*am),
                       (calle.fin.x  +ux*am, calle.fin.y  +uy*am)]

                x1_unscaled = round(calle.inicio.x / SX)
                x2_unscaled = round(calle.fin.x / SX)
                is_bridge = not (110 <= x1_unscaled <= 210 and 110 <= x2_unscaled <= 210)

                if is_bridge:
                    am_deck = am + round(2 * SX)
                    pts_deck = [(calle.inicio.x+ux*am_deck, calle.inicio.y+uy*am_deck),
                                (calle.inicio.x-ux*am_deck, calle.inicio.y-uy*am_deck),
                                (calle.fin.x  -ux*am_deck, calle.fin.y  -uy*am_deck),
                                (calle.fin.x  +ux*am_deck, calle.fin.y  +uy*am_deck)]
                    pygame.draw.polygon(superficie, (90, 95, 100), pts_deck)
                    pygame.draw.line(superficie, (200, 200, 205), pts_deck[0], pts_deck[3], 2)
                    pygame.draw.line(superficie, (200, 200, 205), pts_deck[1], pts_deck[2], 2)

                pygame.draw.polygon(superficie, color, pts)
                pygame.draw.line(superficie, (180, 180, 180), pts[0], pts[3], 1)
                pygame.draw.line(superficie, (180, 180, 180), pts[1], pts[2], 1)

                steps = max(2, int(lg/15))
                for s in range(steps):
                    if s%2==0:
                        t1=s/steps; t2=(s+1)/steps
                        x1=calle.inicio.x+(calle.fin.x-calle.inicio.x)*t1
                        y1=calle.inicio.y+(calle.fin.y-calle.inicio.y)*t1
                        x2=calle.inicio.x+(calle.fin.x-calle.inicio.x)*t2
                        y2=calle.inicio.y+(calle.fin.y-calle.inicio.y)*t2
                        pygame.draw.line(superficie, COLORES['LINEA_AMARILLA'],
                                         (int(x1),int(y1)),(int(x2),int(y2)), 1)

        font = pygame.font.Font(None, max(14, round(20*min(SX,SY))))
        lugares = [
            ("VÍA EVITAMIENTO",  px(250 + 200), py(455)),
            ("CALLE 2",          px(450 + 200), py(215)),
            ("CALLE 3",          px(255 + 200), py(270)),
            ("CALLE 4",          px(555 + 200), py(340)),
            ("CALLE 5",          px(755 + 200), py(400)),
            ("CALLE 6",          px(885 + 200), py(430)),
            ("CALLE 7",          px(80 + 200),  py(130)),
            ("CALLE 8",          px(555 + 200), py(130)),
            ("RÍO HUATANAY",     px(640 + 200), py( 80)),
            ("CALLE 10 (BYPASS)",px(140),       py(330)),
        ]
        for nombre, x, y in lugares:
            ts = font.render(nombre, True, COLORES['TEXTO'])
            aw, ah = font.size(nombre)
            bg = pygame.Surface((aw+12, ah+8), pygame.SRCALPHA)
            bg.fill((10,15,25,195))
            pygame.draw.rect(bg,(40,80,150,130),bg.get_rect(),1)
            superficie.blit(bg, (x-6, y-4))
            superficie.blit(font.render(nombre,True,(0,0,0)),(x+1,y+1))
            superficie.blit(ts,(x,y))
