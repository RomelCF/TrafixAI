# -*- coding: utf-8 -*-
"""
simulation/traffic_light.py
Clase Semaforo y enumeraciones asociadas para el control de intersecciones.
"""
import time
import random
from enum import Enum
from simulation.road import Punto

class EstadoSemaforo(Enum):
    ROJO     = 1
    AMARILLO = 2
    VERDE    = 3

class FaseSemaforo(Enum):
    NORTE_SUR          = 1
    NORTE_SUR_AMARILLO = 2
    ESTE_OESTE         = 3
    ESTE_OESTE_AMARILLO= 4
    GIRO               = 5
    GIRO_AMARILLO      = 6
    PEATON             = 7
    PEATON_AMARILLO    = 8

class Semaforo:
    def __init__(self, posicion: Punto, tipo: str = 'normal'):
        self.posicion = posicion
        self.tipo = tipo
        if tipo == 'principal':
            self.duracion_norte_sur = random.uniform(8, 15)
            self.duracion_este_oeste = random.uniform(8, 15)
        else:
            self.duracion_norte_sur = random.uniform(5, 10)
            self.duracion_este_oeste = random.uniform(5, 10)
            
        self.duracion_giro = random.uniform(4, 8)
        self.duracion_peaton = random.uniform(5, 10)
        self.duracion_amarillo = 3.0
        
        self.duracion_norte_sur_original = self.duracion_norte_sur
        self.duracion_este_oeste_original = self.duracion_este_oeste
        self.duracion_giro_original = self.duracion_giro
        self.duracion_peaton_original = self.duracion_peaton
        
        self.fases_ciclo = [
            FaseSemaforo.NORTE_SUR,
            FaseSemaforo.NORTE_SUR_AMARILLO,
            FaseSemaforo.ESTE_OESTE,
            FaseSemaforo.ESTE_OESTE_AMARILLO,
            FaseSemaforo.GIRO,
            FaseSemaforo.GIRO_AMARILLO,
            FaseSemaforo.PEATON,
            FaseSemaforo.PEATON_AMARILLO
        ]
        self.indice_fase = 0
        self.fase = self.fases_ciclo[self.indice_fase]
        self.tiempo_cambio = time.time() + self.duracion_norte_sur
        
    def restaurar_original(self):
        self.duracion_norte_sur = self.duracion_norte_sur_original
        self.duracion_este_oeste = self.duracion_este_oeste_original
        self.duracion_giro = self.duracion_giro_original
        self.duracion_peaton = self.duracion_peaton_original
        
    def actualizar(self):
        tiempo_actual = time.time()
        if tiempo_actual >= self.tiempo_cambio:
            self.indice_fase = (self.indice_fase + 1) % len(self.fases_ciclo)
            self.fase = self.fases_ciclo[self.indice_fase]
            
            durs = {
                FaseSemaforo.NORTE_SUR: self.duracion_norte_sur,
                FaseSemaforo.ESTE_OESTE: self.duracion_este_oeste,
                FaseSemaforo.GIRO: self.duracion_giro,
                FaseSemaforo.PEATON: self.duracion_peaton
            }
            duracion = durs.get(self.fase, self.duracion_amarillo)
            self.tiempo_cambio = tiempo_actual + duracion

    def dibujar(self, pantalla):
        from simulation.render import dibujar_semaforo
        dibujar_semaforo(pantalla, self)
