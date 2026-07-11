# -*- coding: utf-8 -*-
"""
simulation/__init__.py
Paquete de simulación de tráfico. Exporta todas las entidades clave.
"""
from .road import Punto, Calle, DireccionCalle, COLORES
from .vehicle import TipoVehiculo, Vehiculo
from .traffic_light import EstadoSemaforo, FaseSemaforo, Semaforo
from .metrics import GestorMetricas
from .controllers.ai_controller import GestorIATrafico, GestorMLTrafico
