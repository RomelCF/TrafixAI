# -*- coding: utf-8 -*-
"""
backend/app/core/config.py
Configuración y rutas base globales para el backend.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DATA_DIR = os.path.join(BASE_DIR, 'data')
ML_MODELS_DIR = os.path.join(BASE_DIR, 'backend', 'ml_models')

ESCENARIOS_JSON_PATH = os.path.join(DATA_DIR, 'escenarios.json')
KPIS_JSON_PATH = os.path.join(DATA_DIR, 'kpis.json')
AFORO_VEHICULAR_CSV_PATH = os.path.join(DATA_DIR, 'aforo_vehicular.csv')

PROJECT_NAME = "Simulador de Tráfico IA"
VERSION = "2.0"
API_PREFIX = "/api"
