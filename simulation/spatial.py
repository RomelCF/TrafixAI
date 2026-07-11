# -*- coding: utf-8 -*-
"""Índice espacial simple para acelerar consultas de proximidad."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable, List

class IndiceEspacial:
    def __init__(self, cell_size: int = 100):
        self.cell_size = cell_size
        self._grid: dict[tuple[int, int], list[Any]] = defaultdict(list)
        self._celda_por_obj: dict[int, tuple[int, int]] = {}

    def _celda(self, x: float, y: float) -> tuple[int, int]:
        cs = self.cell_size
        return (int(x // cs), int(y // cs))

    def _coords(self, obj: Any, x_attr: str = "x", y_attr: str = "y") -> tuple[float, float]:
        pos = getattr(obj, "posicion", obj)
        return getattr(pos, x_attr), getattr(pos, y_attr)

    def reconstruir(self, objetos: Iterable[Any], x_attr: str = "x", y_attr: str = "y") -> None:
        self._grid.clear()
        self._celda_por_obj.clear()
        for obj in objetos:
            x, y = self._coords(obj, x_attr, y_attr)
            self.insertar(obj, x, y)

    def insertar(self, obj: Any, x: float, y: float) -> None:
        celda = self._celda(x, y)
        oid = id(obj)
        prev = self._celda_por_obj.get(oid)
        if prev == celda and obj in self._grid.get(celda, ()):
            return
        if prev is not None:
            bucket = self._grid.get(prev)
            if bucket and obj in bucket:
                bucket.remove(obj)
        self._grid[celda].append(obj)
        self._celda_por_obj[oid] = celda

    def actualizar(self, obj: Any, x: float, y: float) -> None:
        celda = self._celda(x, y)
        oid = id(obj)
        prev = self._celda_por_obj.get(oid)
        if prev is None:
            self.insertar(obj, x, y)
            return
        if prev == celda:
            return
        bucket = self._grid.get(prev)
        if bucket and obj in bucket:
            bucket.remove(obj)
        self._grid[celda].append(obj)
        self._celda_por_obj[oid] = celda

    def eliminar(self, obj: Any) -> None:
        oid = id(obj)
        celda = self._celda_por_obj.pop(oid, None)
        if celda is None:
            return
        bucket = self._grid.get(celda)
        if bucket and obj in bucket:
            bucket.remove(obj)

    def consultar(self, x: float, y: float, radio: float) -> List[Any]:
        cs = self.cell_size
        cx, cy = int(x // cs), int(y // cs)
        celdas = int(math.ceil(radio / cs))
        vistos: set[int] = set()
        resultados: list[Any] = []
        radio_sq = radio * radio

        for dx in range(-celdas, celdas + 1):
            for dy in range(-celdas, celdas + 1):
                for obj in self._grid.get((cx + dx, cy + dy), ()):
                    oid = id(obj)
                    if oid in vistos:
                        continue
                    pos = getattr(obj, "posicion", obj)
                    ox = getattr(pos, "x")
                    oy = getattr(pos, "y")
                    dist_sq = (ox - x) ** 2 + (oy - y) ** 2
                    if dist_sq <= radio_sq:
                        vistos.add(oid)
                        resultados.append(obj)
        return resultados
