# -*- coding: utf-8 -*-
"""
backend/app/main.py
Archivo de entrada de FastAPI. Configura CORS, eventos de ciclo de vida e incluye rutas.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.services.simulation_service import runner, runner_angostura
from backend.app.api import routes_simulation

@asynccontextmanager
async def ciclo_vida(app: FastAPI) -> AsyncGenerator:
    print("[Backend] Iniciando simulaciones en background...")
    runner.iniciar()
    runner_angostura.iniciar()
    print("[Backend] Simulaciones en marcha. API lista.")
    yield
    print("[Backend] Deteniendo simulaciones...")
    runner.detener()
    runner_angostura.detener()

app = FastAPI(
    title="Tránsito Cusco API",
    version="2.0",
    lifespan=ciclo_vida
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def salud():
    return {"status": "ok"}

app.include_router(routes_simulation.router, prefix="/api")
