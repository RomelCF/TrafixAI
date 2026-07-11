# -*- coding: utf-8 -*-
"""
simulation/fixed_time_controller.py
Controlador clásico de semáforos por ciclos de tiempo fijo.
"""

class FixedTimeController:
    def __init__(self, semaforos):
        self.semaforos = semaforos

    def actualizar(self):
        for sem in self.semaforos:
            sem.actualizar()
