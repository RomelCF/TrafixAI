# -*- coding: utf-8 -*-
"""
simulation/engine.py
Interfaz unificada para el motor de simulación.
Exporta las simulaciones de Cusco y Angostura.
"""
import sys
from .cusco_engine import SimulacionTrafico, _HeadlessCentro
from .angostura_engine import SimulacionAngostura

if __name__ == "__main__":
    print("=========================================================")
    print("        MOTOR DE SIMULACIÓN DE TRÁFICO - CUSCO & ANGOSTURA")
    print("=========================================================")
    print("1. Iniciar Simulación Centro Histórico (Cusco)")
    print("2. Iniciar Simulación Sector Angostura (Angostura)")
    print("=========================================================")
    
    opcion = "1"
    if len(sys.argv) > 1:
        if sys.argv[1] in ("2", "angostura"):
            opcion = "2"
    else:
        try:
            opcion = input("Seleccione una opción [1]: ").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            sys.exit(0)
            
    if opcion == "2":
        print("\nIniciando simulación interactiva de Angostura...")
        import pygame
        pygame.init()
        sim = SimulacionAngostura()
        sim.pantalla = pygame.display.set_mode((1600, 900))
        pygame.display.set_caption("Simulación Interactiva - Sector Angostura")
        
        ejecutando = True
        while ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                    ejecutando = False
            sim.paso()
            sim.renderizar(sim.pantalla)
            pygame.display.flip()
            sim.reloj.tick(60)
        pygame.quit()
    else:
        print("\nIniciando simulación interactiva de Centro Histórico...")
        sim = SimulacionTrafico()
        sim.ejecutar()
