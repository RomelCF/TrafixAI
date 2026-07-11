# -*- coding: utf-8 -*-
"""
simulation/vehicle.py
Definición de tipos de vehículos y la entidad Vehiculo.
"""
import math
import random
from enum import Enum
from typing import List, Tuple, Optional
from simulation.road import Punto, Calle, DireccionCalle, COLORES

class TipoVehiculo(Enum):
    AUTO  = 1
    COMBI = 2
    MOTO  = 3
    TAXI  = 4
    PICKUP           = 5
    BUS              = 6
    TRANSP_URBANO    = 7
    CAMION_LIGERO    = 8
    CAMION_MEDIANO   = 9
    CAMION_PESADO    = 10
    ARTICULADO       = 11

class Vehiculo:
    """Entidad vehicular con comportamiento de seguimiento de ruta y respeto a semáforos."""

    def __init__(self, tipo: TipoVehiculo, posicion: Punto, calle_actual: Calle):
        self.tipo           = tipo
        self.posicion       = posicion
        self.calle_actual   = calle_actual
        self.direccion      = self._calcular_direccion_inicial()
        self.velocidad_maxima = self._obtener_velocidad_maxima()
        self.velocidad_actual = 0.0
        self.velocidad_objetivo = 0.0
        self.tamano         = self._obtener_tamano()
        self.color          = self._obtener_color()
        self.ruta: List[Calle] = []
        self.indice_ruta    = 0
        self.tiempo_parada  = 0
        self.tiempo_atascado = 0
        
        if self.tipo in (TipoVehiculo.PICKUP, TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO, 
                         TipoVehiculo.CAMION_LIGERO, TipoVehiculo.CAMION_MEDIANO, 
                         TipoVehiculo.CAMION_PESADO, TipoVehiculo.ARTICULADO):
            self.carril = 1
            if self.tipo in (TipoVehiculo.TRANSP_URBANO, TipoVehiculo.BUS):
                self.criterio_ruta = 'preferente_transporte'
            elif self.tipo in (TipoVehiculo.CAMION_LIGERO, TipoVehiculo.CAMION_MEDIANO,
                               TipoVehiculo.CAMION_PESADO, TipoVehiculo.ARTICULADO):
                self.criterio_ruta = 'rapida'
            else:
                self.criterio_ruta = random.choice(['corta', 'rapida', 'economica', 'evita_ia', 'comoda'])
        else:
            self.carril = random.choice([-1, 1])
            self.criterio_ruta = (
                'preferente_transporte'
                if tipo in (TipoVehiculo.COMBI, TipoVehiculo.TAXI)
                else random.choice(['corta', 'rapida', 'economica', 'evita_ia', 'comoda'])
            )
            
        self.comportamiento       = self._obtener_comportamiento()
        self.tiempo_espera_acumulado = 0

    def _calcular_direccion_inicial(self) -> float:
        dx = self.calle_actual.fin.x - self.calle_actual.inicio.x
        dy = self.calle_actual.fin.y - self.calle_actual.inicio.y
        return math.atan2(dy, dx)

    def _obtener_velocidad_maxima(self) -> float:
        base = {
            TipoVehiculo.AUTO:           2.5,
            TipoVehiculo.COMBI:          1.8,
            TipoVehiculo.MOTO:           3.2,
            TipoVehiculo.TAXI:           2.0,
            TipoVehiculo.PICKUP:         2.3,
            TipoVehiculo.BUS:            1.6,
            TipoVehiculo.TRANSP_URBANO:  1.7,
            TipoVehiculo.CAMION_LIGERO:  2.0,
            TipoVehiculo.CAMION_MEDIANO: 1.6,
            TipoVehiculo.CAMION_PESADO:  1.2,
            TipoVehiculo.ARTICULADO:     0.9,
        }
        if self.tipo in (TipoVehiculo.PICKUP, TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO, 
                         TipoVehiculo.CAMION_LIGERO, TipoVehiculo.CAMION_MEDIANO, 
                         TipoVehiculo.CAMION_PESADO, TipoVehiculo.ARTICULADO):
            f = 1.0
            if self.calle_actual.tipo == 'empedrada':   f = 0.5
            elif self.calle_actual.tipo == 'secundaria': f = 0.75
            elif self.calle_actual.tipo == 'bypass':     f = 1.2
            return base[self.tipo] * f * random.uniform(0.85, 1.15)
        else:
            factor = {'empedrada': 0.6, 'secundaria': 0.8}.get(self.calle_actual.tipo, 1.0)
            return base[self.tipo] * factor * random.uniform(0.8, 1.2)

    def _obtener_tamano(self) -> Tuple[int, int]:
        return {
            TipoVehiculo.AUTO:           (22, 14),
            TipoVehiculo.COMBI:          (35, 18),
            TipoVehiculo.MOTO:           (14, 10),
            TipoVehiculo.TAXI:           (22, 14),
            TipoVehiculo.PICKUP:         (28, 13),
            TipoVehiculo.BUS:            (52, 16),
            TipoVehiculo.TRANSP_URBANO:  (40, 16),
            TipoVehiculo.CAMION_LIGERO:  (36, 14),
            TipoVehiculo.CAMION_MEDIANO: (46, 15),
            TipoVehiculo.CAMION_PESADO:  (56, 16),
            TipoVehiculo.ARTICULADO:     (80, 16),
        }[self.tipo]

    def _obtener_color(self) -> Tuple[int, int, int]:
        opciones = {
            TipoVehiculo.AUTO:  [COLORES['AUTO_ROJO'], COLORES['AUTO_AZUL'],
                                 COLORES['AUTO_BLANCO'], COLORES['AUTO_NEGRO']],
            TipoVehiculo.COMBI: [COLORES['COMBI_AMARILLA'], COLORES['COMBI_AZUL']],
            TipoVehiculo.MOTO:  [COLORES['MOTO_ROJA'], COLORES['MOTO_NEGRA']],
            TipoVehiculo.TAXI:  [COLORES['TAXI']],
            TipoVehiculo.PICKUP: [
                COLORES['PICKUP_ROJO'], COLORES['PICKUP_VERDE'], COLORES['PICKUP_GRIS'],
                COLORES['AUTO_BLANCO'],
            ],
            TipoVehiculo.BUS: [
                COLORES['BUS_BLANCO'], COLORES['BUS_AMARILLO'],
            ],
            TipoVehiculo.TRANSP_URBANO: [
                COLORES['TRANSP_AMARILLO'], COLORES['TRANSP_AZUL'], COLORES['TRANSP_NARANJA'],
            ],
            TipoVehiculo.CAMION_LIGERO: [
                COLORES['CAMION_LIG_BLANCO'], COLORES['CAMION_LIG_ROJO'],
            ],
            TipoVehiculo.CAMION_MEDIANO: [
                COLORES['CAMION_MED_AZUL'], COLORES['CAMION_MED_GRIS'],
            ],
            TipoVehiculo.CAMION_PESADO: [
                COLORES['CAMION_PES_ROJO'], COLORES['CAMION_PES_AZUL'],
            ],
            TipoVehiculo.ARTICULADO: [
                COLORES['ARTICULADO_BLANCO'], COLORES['ARTICULADO_ROJO'],
            ],
        }
        if self.tipo == TipoVehiculo.AUTO:
            return random.choice(opciones[self.tipo] + [COLORES['AUTO_PLATA']])
        return random.choice(opciones[self.tipo])

    def _obtener_comportamiento(self) -> dict:
        c = {
            TipoVehiculo.AUTO:  {'paciencia': random.uniform(0.7, 1.0),
                                 'agresividad': random.uniform(0.3, 0.7),
                                 'tiempo_reaccion': random.uniform(0.5, 1.0)},
            TipoVehiculo.COMBI: {'paciencia': random.uniform(0.4, 0.8),
                                 'agresividad': random.uniform(0.6, 0.9),
                                 'tiempo_reaccion': random.uniform(0.8, 1.5),
                                 'paradas_frecuentes': True},
            TipoVehiculo.MOTO:  {'paciencia': random.uniform(0.2, 0.5),
                                 'agresividad': random.uniform(0.8, 1.0),
                                 'tiempo_reaccion': random.uniform(0.2, 0.5),
                                 'puede_zigzaguear': True},
            TipoVehiculo.TAXI:  {'paciencia': random.uniform(0.5, 0.8),
                                 'agresividad': random.uniform(0.4, 0.8),
                                 'tiempo_reaccion': random.uniform(0.6, 1.0),
                                 'busca_pasajeros': True},
            TipoVehiculo.PICKUP: {
                'paciencia': random.uniform(0.6, 0.9),
                'agresividad': random.uniform(0.4, 0.8),
                'tiempo_reaccion': random.uniform(0.5, 1.0),
            },
            TipoVehiculo.BUS: {
                'paciencia': random.uniform(0.5, 0.8),
                'agresividad': random.uniform(0.3, 0.6),
                'tiempo_reaccion': random.uniform(1.0, 2.0),
                'paradas_frecuentes': True,
            },
            TipoVehiculo.TRANSP_URBANO: {
                'paciencia': random.uniform(0.3, 0.7),
                'agresividad': random.uniform(0.5, 0.9),
                'tiempo_reaccion': random.uniform(0.8, 1.5),
                'paradas_frecuentes': True,
            },
            TipoVehiculo.CAMION_LIGERO: {
                'paciencia': random.uniform(0.6, 0.9),
                'agresividad': random.uniform(0.2, 0.5),
                'tiempo_reaccion': random.uniform(1.0, 1.8),
            },
            TipoVehiculo.CAMION_MEDIANO: {
                'paciencia': random.uniform(0.7, 1.0),
                'agresividad': random.uniform(0.1, 0.4),
                'tiempo_reaccion': random.uniform(1.5, 2.5),
            },
            TipoVehiculo.CAMION_PESADO: {
                'paciencia': random.uniform(0.8, 1.0),
                'agresividad': random.uniform(0.1, 0.3),
                'tiempo_reaccion': random.uniform(2.0, 3.0),
            },
            TipoVehiculo.ARTICULADO: {
                'paciencia': random.uniform(0.9, 1.0),
                'agresividad': random.uniform(0.1, 0.2),
                'tiempo_reaccion': random.uniform(2.5, 4.0),
            },
        }
        return c[self.tipo]

    def establecer_ruta(self, calles: List[Calle]):
        self.ruta = calles
        self.indice_ruta = 0

    def actualizar(self, otros_vehiculos: List['Vehiculo'], semaforos: list) -> bool:
        if not self.ruta or self.indice_ruta >= len(self.ruta):
            return False

        calle_actual = self.ruta[self.indice_ruta]
        self.calle_actual = calle_actual

        if self._calcular_progreso_en_calle() >= 1.0:
            self.indice_ruta += 1
            if self.indice_ruta >= len(self.ruta):
                return False
            self.calle_actual = self.ruta[self.indice_ruta]

        self._actualizar_direccion()

        esperando = False
        vel_obj = self.velocidad_maxima
        for sem in semaforos:
            if self._debe_detenerse_por_semaforo(sem):
                vel_obj = 0.0
                esperando = True
                break

        veh_adelante = None
        dist_adelante = None
        if not esperando:
            veh_adelante = self._encontrar_vehiculo_adelante(otros_vehiculos)
            if veh_adelante:
                dx = veh_adelante.posicion.x - self.posicion.x
                dy = veh_adelante.posicion.y - self.posicion.y
                dist_adelante = math.sqrt(dx * dx + dy * dy)
                if dist_adelante < 40:
                    vel_obj = min(vel_obj, veh_adelante.velocidad_actual * 0.5)
                elif dist_adelante < 60:
                    vel_obj = min(vel_obj, veh_adelante.velocidad_actual * 0.8)

        self.velocidad_objetivo = vel_obj
        self._aplicar_comportamiento_especial()
        self._actualizar_velocidad()

        en_cola = False
        if veh_adelante and dist_adelante is not None and dist_adelante < 55:
            diff = abs(self.direccion - veh_adelante.direccion)
            diff = min(diff, 2 * math.pi - diff)
            if veh_adelante.velocidad_actual < 0.1 and diff < math.pi / 3:
                en_cola = True

        if self.velocidad_actual < 0.05 and not esperando and not en_cola:
            self.tiempo_atascado += 1
        else:
            self.tiempo_atascado = 0

        if self.velocidad_actual < 0.2:
            self.tiempo_espera_acumulado += 1
        else:
            self.tiempo_espera_acumulado = 0

        if self.tiempo_atascado > 720:
            return False

        self._mover()
        return True

    def _calcular_progreso_en_calle(self) -> float:
        if not self.ruta:
            return 1.0
        calle = self.ruta[self.indice_ruta]
        total = calle.inicio.distancia_a(calle.fin)
        if total == 0:
            return 1.0
        dx = calle.fin.x - calle.inicio.x
        dy = calle.fin.y - calle.inicio.y
        px = self.posicion.x - calle.inicio.x
        py = self.posicion.y - calle.inicio.y
        return min(max((px * dx + py * dy) / (total * total), 0.0), 1.0)

    def _actualizar_direccion(self):
        if self.indice_ruta >= len(self.ruta):
            return
        calle = self.ruta[self.indice_ruta]
        dx = calle.fin.x - calle.inicio.x
        dy = calle.fin.y - calle.inicio.y
        total = math.sqrt(dx * dx + dy * dy)
        if total == 0:
            self.direccion = math.atan2(dy, dx)
            return
        px = self.posicion.x - calle.inicio.x
        py = self.posicion.y - calle.inicio.y
        t = min(max((px * dx + py * dy) / (total * total), 0.0), 1.0)
        t_mira = min(1.0, t + 35.0 / total)
        x_mira = calle.inicio.x + t_mira * dx
        y_mira = calle.inicio.y + t_mira * dy
        self.direccion = math.atan2(y_mira - self.posicion.y, x_mira - self.posicion.x)

    def _debe_detenerse_por_semaforo(self, semaforo) -> bool:
        from simulation.traffic_light import FaseSemaforo
        dx = semaforo.posicion.x - self.posicion.x
        dy = semaforo.posicion.y - self.posicion.y
        dist_sq = dx * dx + dy * dy
        if dist_sq > 6400:
            return False
        
        ang = math.atan2(dy, dx)
        dif = abs(self.direccion - ang)
        dif = min(dif, 2 * math.pi - dif)
        if dif >= math.pi / 3:
            return False

        d = self.calle_actual.direccion
        f = semaforo.fase
        if d == DireccionCalle.VERTICAL:
            if f == FaseSemaforo.NORTE_SUR:        return False
            if f == FaseSemaforo.NORTE_SUR_AMARILLO:
                return dist_sq > 625
            return True
        if d == DireccionCalle.HORIZONTAL:
            if f == FaseSemaforo.ESTE_OESTE:         return False
            if f == FaseSemaforo.ESTE_OESTE_AMARILLO:
                return dist_sq > 625
            return True
        if d == DireccionCalle.DIAGONAL:
            if f == FaseSemaforo.GIRO:              return False
            if f == FaseSemaforo.GIRO_AMARILLO:     return dist_sq > 625
            return True
        return True

    def _encontrar_vehiculo_adelante(self, otros: List['Vehiculo']) -> Optional['Vehiculo']:
        mejor, dist_min = None, float('inf')
        calle_sig = (self.ruta[self.indice_ruta + 1]
                     if self.indice_ruta + 1 < len(self.ruta) else None)
        for otro in otros:
            if otro is self:
                continue
            dx = otro.posicion.x - self.posicion.x
            dy = otro.posicion.y - self.posicion.y
            dist_sq = dx * dx + dy * dy
            
            mismo = (otro.calle_actual == self.calle_actual or
                     (calle_sig and otro.calle_actual == calle_sig))
            max_dist = 80 if mismo else 25
            if dist_sq > max_dist * max_dist:
                continue
            
            dist = math.sqrt(dist_sq)
            ang = math.atan2(dy, dx)
            dif = abs(self.direccion - ang)
            dif = min(dif, 2 * math.pi - dif)
            umbral = math.pi / 6 if mismo else math.pi / 9
            if dif < umbral and dist < dist_min:
                dist_min = dist
                mejor = otro
        return mejor

    def _aplicar_comportamiento_especial(self):
        if self.tipo in (TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO) and \
                self.comportamiento.get('paradas_frecuentes') and random.random() < 0.0008:
            self.tiempo_parada = random.uniform(60, 200)
        elif self.tipo == TipoVehiculo.COMBI and self.comportamiento.get('paradas_frecuentes') and random.random() < 0.001:
            self.tiempo_parada = random.uniform(60, 180)
        elif self.tipo == TipoVehiculo.TAXI and self.comportamiento.get('busca_pasajeros') and random.random() < 0.0008:
            self.tiempo_parada = random.uniform(40, 120)
            
        if self.tiempo_parada > 0:
            self.tiempo_parada -= 1
            self.velocidad_objetivo = 0.0

    def _actualizar_velocidad(self):
        aceleracion = 0.08 * self.comportamiento['agresividad']
        frenado = 0.15
        if self.velocidad_actual < self.velocidad_objetivo:
            self.velocidad_actual = min(self.velocidad_actual + aceleracion, self.velocidad_objetivo)
        else:
            self.velocidad_actual = max(self.velocidad_actual - frenado,
                                         max(0.0, self.velocidad_objetivo))

    def _mover(self):
        if self.tipo in (TipoVehiculo.PICKUP, TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO,
                         TipoVehiculo.CAMION_LIGERO, TipoVehiculo.CAMION_MEDIANO,
                         TipoVehiculo.CAMION_PESADO, TipoVehiculo.ARTICULADO):
            ruido = random.uniform(-0.05, 0.05) * (1 - self.comportamiento['paciencia'])
            d = self.direccion + ruido
            self.posicion.x += math.cos(d) * self.velocidad_actual
            self.posicion.y += math.sin(d) * self.velocidad_actual

            ancho_via = self.calle_actual.ancho
            if self.tipo in (TipoVehiculo.ARTICULADO, TipoVehiculo.CAMION_PESADO):
                offset_lateral = ancho_via * 0.18
            elif self.tipo in (TipoVehiculo.CAMION_MEDIANO, TipoVehiculo.BUS):
                offset_lateral = ancho_via * 0.20
            elif self.tipo in (TipoVehiculo.CAMION_LIGERO, TipoVehiculo.TRANSP_URBANO):
                offset_lateral = ancho_via * 0.21
            else:
                offset_lateral = ancho_via * 0.23

            c = self.calle_actual
            dx = c.fin.x - c.inicio.x
            dy = c.fin.y - c.inicio.y
            total = math.sqrt(dx*dx + dy*dy)
            if total > 0:
                ux, uy = dx / total, dy / total
                rx, ry = uy, -ux
                relx = self.posicion.x - c.inicio.x
                rely = self.posicion.y - c.inicio.y
                lateral_actual = relx * rx + rely * ry
                error = offset_lateral - lateral_actual
                factor_correccion = 0.08
                self.posicion.x += rx * error * factor_correccion
                self.posicion.y += ry * error * factor_correccion
        else:
            ruido = random.uniform(-0.1, 0.1) * (1 - self.comportamiento['paciencia'])
            d = self.direccion + ruido
            self.posicion.x += math.cos(d) * self.velocidad_actual
            self.posicion.y += math.sin(d) * self.velocidad_actual

    def dibujar(self, pantalla):
        from simulation.render import dibujar_vehiculo
        dibujar_vehiculo(pantalla, self)
