# -*- coding: utf-8 -*-
"""
backend/app/schemas/simulation_schema.py
Modelos de validación de datos (Pydantic) para las peticiones de la API.
"""
from pydantic import BaseModel, Field

class ControlRequest(BaseModel):
    action: str = Field(..., description="Acción de control: pause, resume, toggle_ai, restart, fast_forward, benchmark, cancel_benchmark")
    localidad: str = Field("centro_historico", description="Localidad a la que aplicar la acción: centro_historico, sector_angostura")
