# -*- coding: utf-8 -*-
"""
backend/app/api/routes_simulation.py
Definición de las rutas de API REST para controlar y monitorear la simulación de tráfico.
"""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Query, Response, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.core.config import ESCENARIOS_JSON_PATH
from backend.app.schemas.simulation_schema import ControlRequest
from backend.app.services.simulation_service import obtener_runner
from backend.app.services.metrics_service import generar_excel_reporte

router = APIRouter()

@router.get("/metrics")
def obtener_metricas(localidad: str = Query("centro_historico")):
    try:
        return obtener_runner(localidad).obtener_metricas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {e}")

@router.get("/history")
def obtener_historial(localidad: str = Query("centro_historico")):
    try:
        return obtener_runner(localidad).obtener_historial()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {e}")

@router.get("/kpis")
def obtener_kpis(localidad: str = Query("centro_historico")):
    try:
        return obtener_runner(localidad).obtener_kpis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo KPIs: {e}")

@router.get("/scenarios")
def obtener_escenarios():
    try:
        with open(ESCENARIOS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo cargar la configuración de escenarios: {e}")

@router.get("/semaforos")
def obtener_semaforos(localidad: str = Query("centro_historico")):
    try:
        return obtener_runner(localidad).obtener_semaforos()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo semáforos: {e}")

@router.post("/control")
def controlar(req: ControlRequest):
    valid = {"pause", "resume", "toggle_ai", "restart", "fast_forward", "benchmark", "cancel_benchmark"}
    if req.action not in valid:
        raise HTTPException(status_code=400, detail=f"Acción inválida. Valores válidos: {valid}")
    try:
        obtener_runner(req.localidad).aplicar_control(req.action)
        return {"status": "ok", "action": req.action, "localidad": req.localidad}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando control: {e}")

@router.get("/export")
def exportar_datos(localidad: str = Query("centro_historico")):
    try:
        data, filename = generar_excel_reporte(localidad)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response = Response(content=data, media_type=mime)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando datos: {e}")

async def _generador_mjpeg(localidad: str) -> AsyncGenerator[bytes, None]:
    import io
    from PIL import Image
    r = obtener_runner(localidad)
    boundary = b"--frame"
    last_index = -1
    
    r.incrementar_clientes()
    try:
        while True:
            raw_rgb, frame_index = r.obtener_raw_frame()
            if raw_rgb and frame_index != last_index:
                ancho_stream = r._ancho // 2
                alto_stream = r._alto // 2
                
                def comprimir_jpeg():
                    img = Image.frombytes('RGB', (ancho_stream, alto_stream), raw_rgb)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=65)
                    return buf.getvalue()
                
                frame = await asyncio.to_thread(comprimir_jpeg)
                yield (
                    boundary + b"\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"\r\n" + frame + b"\r\n"
                )
                last_index = frame_index
            await asyncio.sleep(0.04)
    finally:
        r.decrementar_clientes()

@router.get("/stream")
async def transmision_video(localidad: str = Query("centro_historico")):
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        _generador_mjpeg(localidad),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers=headers,
    )
