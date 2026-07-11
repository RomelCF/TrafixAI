# -*- coding: utf-8 -*-
"""
simulation/render.py
Funciones de visualización y dibujo con Pygame.
Desacopla la lógica de simulación de las instrucciones de renderizado.
"""
import pygame
import math
from simulation.road import Punto
from simulation.vehicle import TipoVehiculo
from simulation.traffic_light import FaseSemaforo

def _rotar_puntos(vehiculo, pts, dx=0.0, dy=0.0):
    cos_a = math.cos(vehiculo.direccion)
    sin_a = math.sin(vehiculo.direccion)
    cx = vehiculo.posicion.x + dx
    cy = vehiculo.posicion.y + dy
    return [(px * cos_a - py * sin_a + cx, px * sin_a + py * cos_a + cy) for px, py in pts]

def dibujar_vehiculo(pantalla, vehiculo):
    w, h = vehiculo.tamano
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]

    pygame.draw.polygon(pantalla, (15, 15, 20), _rotar_puntos(vehiculo, pts, 2, 2))
    pygame.draw.polygon(pantalla, vehiculo.color, _rotar_puntos(vehiculo, pts))
    
    if vehiculo.tipo in (TipoVehiculo.CAMION_PESADO, TipoVehiculo.ARTICULADO):
        cab_x = vehiculo.posicion.x + math.cos(vehiculo.direccion) * (w/2 - 6)
        cab_y = vehiculo.posicion.y + math.sin(vehiculo.direccion) * (w/2 - 6)
        pygame.draw.circle(pantalla, (20, 20, 20), (int(cab_x), int(cab_y)), 3)
        
    if vehiculo.tiempo_parada > 0:
        if vehiculo.tipo in (TipoVehiculo.BUS, TipoVehiculo.TRANSP_URBANO):
            c_ind = (255, 200, 0)
        elif vehiculo.tipo == TipoVehiculo.TAXI:
            c_ind = (0, 255, 255)
        else:
            c_ind = (255, 255, 0)
        pygame.draw.circle(pantalla, c_ind, (int(vehiculo.posicion.x), int(vehiculo.posicion.y - 20)), 4)

def dibujar_semaforo(pantalla, semaforo):
    pygame.draw.rect(pantalla, (60, 60, 60), (semaforo.posicion.x - 2, semaforo.posicion.y - 16, 4, 32))
    
    caja = pygame.Rect(semaforo.posicion.x - 12, semaforo.posicion.y - 12, 24, 24)
    pygame.draw.rect(pantalla, (20, 25, 30), caja)
    pygame.draw.rect(pantalla, (80, 100, 140), caja, 1)
    
    c_ns = (255, 50, 50)
    c_eo = (255, 50, 50)
    c_g  = (255, 50, 50)
    c_p  = (255, 50, 50)
    
    if semaforo.fase == FaseSemaforo.NORTE_SUR:
        c_ns = (50, 255, 50)
    elif semaforo.fase == FaseSemaforo.NORTE_SUR_AMARILLO:
        c_ns = (255, 230, 50)
        
    if semaforo.fase == FaseSemaforo.ESTE_OESTE:
        c_eo = (50, 255, 50)
    elif semaforo.fase == FaseSemaforo.ESTE_OESTE_AMARILLO:
        c_eo = (255, 230, 50)
        
    if semaforo.fase == FaseSemaforo.GIRO:
        c_g = (50, 255, 50)
    elif semaforo.fase == FaseSemaforo.GIRO_AMARILLO:
        c_g = (255, 230, 50)
        
    if semaforo.fase == FaseSemaforo.PEATON:
        c_p = (50, 255, 50)
    elif semaforo.fase == FaseSemaforo.PEATON_AMARILLO:
        c_p = (255, 230, 50)
        
    pygame.draw.circle(pantalla, c_ns, (int(semaforo.posicion.x - 5), int(semaforo.posicion.y - 5)), 3)
    pygame.draw.circle(pantalla, c_eo, (int(semaforo.posicion.x + 5), int(semaforo.posicion.y - 5)), 3)
    pygame.draw.circle(pantalla, c_g, (int(semaforo.posicion.x - 5), int(semaforo.posicion.y + 5)), 3)
    pygame.draw.circle(pantalla, c_p, (int(semaforo.posicion.x + 5), int(semaforo.posicion.y + 5)), 3)

def dibujar_zonas(pantalla, ia_trafico):
    sup = pygame.Surface((pantalla.get_width(), pantalla.get_height()), pygame.SRCALPHA)
    c_fondo = {
        "Fluido": (46, 204, 113, 20),
        "Moderado": (241, 196, 15, 25),
        "Congestionado": (230, 126, 34, 30),
        "Crítico": (231, 76, 60, 35)
    }
    c_borde = {
        "Fluido": (46, 204, 113, 100),
        "Moderado": (241, 196, 15, 120),
        "Congestionado": (230, 126, 34, 150),
        "Crítico": (231, 76, 60, 180)
    }
    font = pygame.font.Font(None, 16)
    for nombre, (x1, y1, x2, y2) in ia_trafico.zonas.items():
        datos = ia_trafico.metricas_zona.get(nombre, {
            "nivel": "Fluido", "vehiculos": 0, "velocidad": 0.0, "detenidos": 0
        })
        nivel = datos["nivel"]
        
        color_fondo = c_fondo.get(nivel, (46, 204, 113, 20))
        color_borde = c_borde.get(nivel, (46, 204, 113, 100))
        
        pygame.draw.rect(sup, color_fondo, (x1, y1, x2 - x1, y2 - y1))
        pygame.draw.rect(sup, color_borde, (x1, y1, x2 - x1, y2 - y1), 1)
        
        label = f"{nombre.upper()} | {nivel} ({datos['vehiculos']} veh, {datos['detenidos']} det)"
        ts = font.render(label, True, color_borde[:3])
        bg = ts.get_rect(topleft=(x1 + 6, y1 + 6))
        pygame.draw.rect(sup, (20, 25, 30, 220), bg.inflate(8, 4))
        sup.blit(ts, (x1 + 6, y1 + 6))
    pantalla.blit(sup, (0, 0))

def dibujar_panel(pantalla, ia_trafico):
    if getattr(ia_trafico, 'is_angostura', False):
        dibujar_panel_angostura(pantalla, ia_trafico)
    else:
        dibujar_panel_centro(pantalla, ia_trafico)

def dibujar_panel_centro(pantalla, ia_trafico):
    font_titulo = pygame.font.Font(None, 21)
    font_hdr  = pygame.font.Font(None, 19)
    font_body = pygame.font.Font(None, 17)

    colores_nivel_texto = {
        "Fluido":       (80,  220, 120),
        "Moderado":     (255, 220,  60),
        "Congestionado":(255, 140,  30),
        "Crítico":      (255,  60,  60),
    }

    panel_ancho_izq = 390
    filas_zona = len(ia_trafico.zonas)
    alto_izq = 28 + filas_zona * 18 + 10
    surf_izq = pygame.Surface((panel_ancho_izq, alto_izq), pygame.SRCALPHA)
    surf_izq.fill((8, 18, 32, 210))
    pygame.draw.rect(surf_izq, (30, 70, 130, 180), surf_izq.get_rect(), 1)
    pantalla.blit(surf_izq, (10, 840))

    hdr = font_hdr.render("  ZONA                  NIVEL         VEH  VEL  DET", True, (100, 180, 255))
    pantalla.blit(hdr, (16, 843))
    pygame.draw.line(pantalla, (30, 70, 130), (10, 862), (400, 862), 1)

    for i, (nombre, datos) in enumerate(ia_trafico.metricas_zona.items()):
        nivel = datos.get("nivel", "Fluido")
        veh   = datos.get("vehiculos", 0)
        vel   = datos.get("velocidad", 0.0)
        det   = datos.get("detenidos", 0)
        color = colores_nivel_texto.get(nivel, (200, 200, 200))

        ind_x, ind_y = 16, 865 + i * 18
        pygame.draw.rect(pantalla, color, (ind_x, ind_y + 2, 6, 10))

        nombre_corto = nombre[:18].ljust(18)
        nivel_corto  = nivel[:13].ljust(13)
        linea = f"  {nombre_corto}  {nivel_corto}  {veh:3d}  {vel:4.1f}  {det:2d}"
        texto = font_body.render(linea, True, color)
        pantalla.blit(texto, (ind_x, ind_y))

    panel_ancho_mid = 590
    alto_mid = 200
    surf_mid = pygame.Surface((panel_ancho_mid, alto_mid), pygame.SRCALPHA)
    surf_mid.fill((8, 18, 32, 210))
    pygame.draw.rect(surf_mid, (30, 70, 130, 180), surf_mid.get_rect(), 1)
    pantalla.blit(surf_mid, (415, 780))

    titulo_mid = font_titulo.render("📊 IA PREDICTIVA · EVALUACIÓN DE IMPACTO", True, (100, 255, 200))
    pantalla.blit(titulo_mid, (425, 785))
    pygame.draw.line(pantalla, (30, 70, 130), (425, 802), (995, 802), 1)

    evals = ia_trafico._evaluar_impacto_predictivo()
    if evals:
        hdr_mid = font_hdr.render("ZONA / ACCIÓN PROSPECTIVA    VEL  DESBORDE    SECUNDARIA  TRANSP.", True, (120, 200, 255))
        pantalla.blit(hdr_mid, (425, 806))
        pygame.draw.line(pantalla, (20, 45, 90), (425, 821), (995, 821), 1)
        
        for idx, ev in enumerate(evals[:8]):
            row_y = 824 + idx * 18
            if row_y > 962:
                break
            
            zona_accion = f"{ev['zona'][:9]}: {ev['accion'][:14]}"
            zona_surf = font_body.render(zona_accion.ljust(25), True, (255, 255, 255))
            pantalla.blit(zona_surf, (425, row_y))
            
            vel_surf = font_body.render(f"{ev['mejora_vel']:>6}", True, (50, 255, 120))
            pantalla.blit(vel_surf, (625, row_y))
            
            desb_surf = font_body.render(f"{ev['desborde'][:15]}", True, ev['color_desborde'])
            pantalla.blit(desb_surf, (685, row_y))
            
            sec_surf = font_body.render(f"{ev['bloqueo_sec'][:12]}", True, (255, 100, 100) if "Alto" in ev['bloqueo_sec'] or "Moderado" in ev['bloqueo_sec'] else (180, 180, 180))
            pantalla.blit(sec_surf, (815, row_y))
            
            trans_surf = font_body.render(f"{ev['transporte'][:15]}", True, ev['color_transporte'])
            pantalla.blit(trans_surf, (915, row_y))
    else:
        txt_no_eval = font_body.render("Sin congestiones activas. No se requieren acciones correctivas.", True, (150, 150, 150))
        pantalla.blit(txt_no_eval, (425, 820))

    panel_ancho_der = 570
    alto_der = 200
    surf_der = pygame.Surface((panel_ancho_der, alto_der), pygame.SRCALPHA)
    surf_der.fill((8, 18, 32, 210))
    pygame.draw.rect(surf_der, (30, 70, 130, 180), surf_der.get_rect(), 1)
    pantalla.blit(surf_der, (1020, 780))

    titulo_rec = font_titulo.render("🤖 IA · RECOMENDACIONES", True, (100, 200, 255))
    pantalla.blit(titulo_rec, (1030, 785))
    pygame.draw.line(pantalla, (30, 70, 130), (1030, 802), (1582, 802), 1)

    for i, rec in enumerate(ia_trafico.recomendaciones[:3]):
        col_r = (255, 80, 80) if "Crítico" in rec else (
                (255, 180, 60) if "Congestión" in rec else (200, 200, 200))
        pantalla.blit(font_body.render(f"• {rec}", True, col_r), (1032, 806 + i * 17))

    pygame.draw.line(pantalla, (30, 70, 130), (1030, 860), (1582, 860), 1)

    titulo_acc = font_titulo.render("⚙  IA · ACCIONES EJECUTADAS", True, (100, 255, 180))
    pantalla.blit(titulo_acc, (1030, 864))
    pygame.draw.line(pantalla, (30, 70, 130), (1030, 881), (1582, 881), 1)

    for i, accion in enumerate(ia_trafico.log_acciones[:5]):
        col_a = (120, 255, 160) if ("normal" in accion or "cancel" in accion) else (255, 220, 90)
        pantalla.blit(font_body.render(f"▶ {accion}", True, col_a), (1032, 884 + i * 17))

def dibujar_panel_angostura(pantalla, ia_trafico):
    font_titulo = pygame.font.Font(None, 21)
    font_hdr    = pygame.font.Font(None, 19)
    font_body   = pygame.font.Font(None, 17)
    c_nivel = {"Fluido":(80,220,120),"Moderado":(255,220,60),
               "Congestionado":(255,140,30),"Crítico":(255,60,60)}

    pw = 390; fz = len(ia_trafico.zonas)
    ah = 28 + fz*18 + 10
    s = pygame.Surface((pw,ah), pygame.SRCALPHA); s.fill((8,18,32,210))
    pygame.draw.rect(s,(30,70,130,180),s.get_rect(),1)
    pantalla.blit(s,(10,840-ah))
    
    hdr = font_hdr.render("  ZONA              NIVEL         VEH  VEL  DET", True, (100,180,255))
    pantalla.blit(hdr,(16,840-ah+3))
    pygame.draw.line(pantalla,(30,70,130),(10,840-ah+21),(400,840-ah+21),1)
    
    for i,(nombre,datos) in enumerate(ia_trafico.metricas_zona.items()):
        nivel = datos.get("nivel","Fluido")
        color = c_nivel.get(nivel,(200,200,200))
        iy = 840-ah+24+i*18
        pygame.draw.rect(pantalla,color,(16,iy+2,6,10))
        linea = f"  {nombre[:16].ljust(16)}  {nivel[:12].ljust(12)}  {datos.get('vehiculos',0):3d}  {datos.get('velocidad',0):4.1f}  {datos.get('detenidos',0):2d}"
        pantalla.blit(font_body.render(linea,True,color),(16,iy))

    ps = pygame.Surface((560,130),pygame.SRCALPHA); ps.fill((8,18,32,210))
    pygame.draw.rect(ps,(30,70,130,180),ps.get_rect(),1)
    pantalla.blit(ps,(415,770))
    
    pantalla.blit(font_titulo.render("🤖 IA · RECOMENDACIONES ANGOSTURA",True,(100,200,255)),(425,775))
    pygame.draw.line(pantalla,(30,70,130),(425,792),(965,792),1)
    
    for i,rec in enumerate(ia_trafico.recomendaciones[:3]):
        col = (255,80,80) if "Crítico" in rec else ((255,180,60) if "Congestión" in rec else (200,200,200))
        pantalla.blit(font_body.render(f"• {rec}",True,col),(1032-600,796+i*18))

    pygame.draw.line(pantalla,(30,70,130),(425,850),(965,850),1)
    pantalla.blit(font_titulo.render("⚙  IA · ACCIONES EJECUTADAS",True,(100,255,180)),(425,854))
    
    for i,acc in enumerate(ia_trafico.log_acciones[:3]):
        col = (120,255,160) if ("normal" in acc or "cancel" in acc) else (255,220,90)
        pantalla.blit(font_body.render(f"▶ {acc}",True,col),(425,872+i*17))
