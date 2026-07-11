# TrafixAI — Simulador de Tráfico Urbano con IA

Sistema de simulación de tráfico vehicular para dos zonas de Cusco (Centro Histórico y Angostura) que utiliza inteligencia artificial para optimizar los tiempos de los semáforos en tiempo real.

> **Estado del proyecto:** Este proyecto se encuentra en fase de desarrollo. Aún no está listo al 100% y puede presentar bugs o funcionalidades incompletas.

---

## ¿Qué hace este proyecto?

Este simulador:

- **Visualiza** el tráfico en dos zonas clave de Cusco con gráficos interactivos
- **Predice** la congestión vehicular usando datos reales de conteo
- **Optimiza** los tiempos de semáforo automáticamente con aprendizaje por refuerzo
- **Muestra** métricas en tiempo real a través de un dashboard web

El problema que resuelve: los semáforos actuales tienen tiempos fijos que no se adaptan al flujo real del tráfico, causando colas innecesarias y mayor contaminación.

---

## Estructura del proyecto

```
dataset/
  conteo_vehicular.xlsx          Datos reales de conteo vehicular

backend/
  main.py                        API REST (FastAPI)
  ml_engine.py                   Modelos de predicción (Random Forest)
  rl_agent.py                    Agente de optimización de semáforos
  train_models.py                Entrenamiento de modelos
  ml_models/                     Modelos pre-entrenados

transito_con_ia.py               Simulación Centro Histórico
transito_angostura.py            Simulación Angostura
gestor_ml_trafico.py             Conector entre simulación e IA

dashboard-react/                 Dashboard web (React)
```

**Cómo funciona:** La simulación envía datos del tráfico a los modelos de IA, que predicen la congestión y ajustan los tiempos de semáforo automáticamente. El dashboard muestra todo en tiempo real.

---

## Instalación

### Requisitos previos
- Python 3.11
- Node.js 18 o superior

### Pasos de instalación

1. **Instalar dependencias automáticamente:**
   ```
   instalar_dependencias.bat
   ```
   Este script instala todas las dependencias de Python y Node.js. Si falta Python o Node.js, te ofrece descargarlos.

2. **(Opcional) Re-entrenar modelos:**
   ```
   py -3.11 backend\train_models.py
   ```
   Los modelos ya vienen pre-entrenados, pero puedes re-entrenarlos si deseas.

---

## Cómo ejecutar

### Opción 1: Sistema completo (recomendado)
```
ejecutar_completo.bat
```
Inicia el backend, el dashboard web y abre el navegador automáticamente. El backend estará en `http://localhost:8000` y el dashboard en `http://localhost:5173`.

### Opción 2: Solo simulación visual
```
ejecutar.bat
```
Ejecuta solo la simulación gráfica sin backend ni dashboard.

### Opción 3: Solo backend
```
cd backend
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API REST

El backend expone una API en `http://localhost:8000` con los siguientes endpoints principales:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servidor |
| GET | `/api/metrics?localidad=centro_historico` | Métricas actuales de la simulación |
| GET | `/api/history?localidad=centro_historico` | Historial de flujo vehicular |
| POST | `/api/control` | Controlar la simulación (pausar, reanudar, reiniciar) |
| GET | `/api/stream?localidad=centro_historico` | Video en tiempo real de la simulación |

El parámetro `localidad` puede ser `centro_historico` o `sector_angostura`.

Documentación interactiva disponible en `http://localhost:8000/docs`.

---

## Tecnologías utilizadas

**Backend:**
- FastAPI (API REST)
- Pygame (simulación gráfica)
- scikit-learn (modelos de predicción)
- PyTorch (aprendizaje por refuerzo)
- Pandas (procesamiento de datos)

**Frontend:**
- React (dashboard web)

---

## Notas importantes

- Los modelos de IA fueron entrenados con datos reales de conteo vehicular del sector Angostura
- No requiere GPU - todo funciona en CPU
- El agente de aprendizaje por refuerzo mejora gradualmente mientras corre la simulación
- Los pesos del agente no se guardan automáticamente al cerrar
