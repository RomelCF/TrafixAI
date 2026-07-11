# -*- coding: utf-8 -*-
"""
simulation/road.py
Definición de entidades viales y geometría de calles.
"""
import math
from enum import Enum
from dataclasses import dataclass

COLORES = {
    'ASFALTO':            (45,  45,  45),
    'ASFALTO_VIEJO':      (55,  50,  45),
    'LINEA_AMARILLA':     (255, 255, 100),
    'LINEA_BLANCA':       (220, 220, 220),
    'ACERA':              (180, 180, 180),
    'PIEDRA':             (120, 110, 100),
    'EDIFICIO_COLONIAL':  (160, 82,  45),
    'EDIFICIO_MODERNO':   (100, 100, 120),
    'PLAZA':              (85,  140, 85),
    'PASTO':              (60,  120, 60),
    'TIERRA':             (139, 125, 107),
    'RIO':                (54,  117, 136),
    'RIELES':             (150, 150, 150),
    'DURMIENTE':          (120, 100,  80),
    
    'AUTO_ROJO':          (180, 30,  30),
    'AUTO_AZUL':          (30,  80,  180),
    'AUTO_BLANCO':        (240, 240, 240),
    'AUTO_NEGRO':         (40,  40,  40),
    'AUTO_PLATA':         (180, 180, 195),
    'COMBI_AMARILLA':     (255, 200, 0),
    'COMBI_AZUL':         (0,   120, 200),
    'MOTO_ROJA':          (200, 50,  50),
    'MOTO_NEGRA':         (60,  60,  60),
    'TAXI':               (255, 255, 0),
    
    'PICKUP_ROJO':        (160, 40,  20),
    'PICKUP_VERDE':       (40,  100, 50),
    'PICKUP_GRIS':        (120, 120, 130),
    'BUS_BLANCO':         (230, 230, 230),
    'BUS_AMARILLO':       (210, 190, 30),
    'TRANSP_AMARILLO':    (255, 200, 0),
    'TRANSP_AZUL':        (0,   120, 200),
    'TRANSP_NARANJA':     (220, 100, 20),
    'CAMION_LIG_BLANCO':  (210, 210, 210),
    'CAMION_LIG_ROJO':    (180, 60,  40),
    'CAMION_MED_AZUL':    (40,  80,  150),
    'CAMION_MED_GRIS':    (90,  90,  100),
    'CAMION_PES_ROJO':    (140, 30,  30),
    'CAMION_PES_AZUL':    (20,  50,  120),
    'ARTICULADO_BLANCO':  (200, 200, 210),
    'ARTICULADO_ROJO':    (120, 20,  20),
    
    'SEMAFORO_ROJO':      (255, 50,  50),
    'SEMAFORO_VERDE':     (50,  255, 50),
    'SEMAFORO_AMARILLO':  (255, 255, 50),
    'FONDO':              (25,  35,  25),
    'TEXTO':              (255, 255, 255),
}

class DireccionCalle(Enum):
    HORIZONTAL = 1
    VERTICAL   = 2
    DIAGONAL   = 3

@dataclass(unsafe_hash=True)
class Punto:
    x: float
    y: float

    def distancia_a(self, otro: 'Punto') -> float:
        return math.sqrt((self.x - otro.x) ** 2 + (self.y - otro.y) ** 2)

@dataclass(unsafe_hash=True)
class Calle:
    inicio:          Punto
    fin:             Punto
    ancho:           int
    tipo:            str
    direccion:       DireccionCalle
    velocidad_maxima: float
