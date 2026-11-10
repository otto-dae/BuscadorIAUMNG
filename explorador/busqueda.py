"""
busqueda.py — Algoritmos de búsqueda en grafos: BFS, DFS y A*.

Implementación propia basada en el pseudocódigo de Russell y Norvig (2016,
cap. 3) y en la estructura de AIMA-Python (clases Problem y Node). Las tres
funciones usan BÚSQUEDA EN GRAFOS (conjunto de explorados), porque el espacio
de rutas tiene ciclos (por ejemplo, girar cuatro veces a la izquierda regresa
al mismo estado) y una búsqueda en árbol no terminaría con DFS.

Las funciones son genéricas: sirven para cualquier problema que ofrezca
initial, actions(s), result(s, a), goal_test(s) y path_cost(c, s, a, s').
El agente (agente.py) las usa como PLANIFICADOR DE RUTAS cada vez que necesita
ir de su posición actual a otra casilla segura.

Todas devuelven un objeto Resultado con las métricas del benchmark:
    nodos_expandidos  : nodos sacados de la frontera y expandidos
    nodos_generados   : nodos hijos creados
    max_frontera      : tamaño máximo de la frontera (memoria pico)
    max_memoria       : máximo de |frontera| + |explorados| (nodos en memoria)
    costo             : costo de la solución, g(meta)
    profundidad       : número de acciones de la solución
    tiempo_ms         : tiempo de reloj de pared en milisegundos
"""

from __future__ import annotations

import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from typing import Any

Estado = Any              # cualquier estado hashable
ProblemaExplorador = Any  # cualquier problema con la interfaz de AIMA


# ---------------------------------------------------------------------- #
# Nodo del árbol de búsqueda
# ---------------------------------------------------------------------- #
class Nodo:
    """Nodo de búsqueda: estado + padre + acción + costo acumulado g(n)."""

    __slots__ = ("estado", "padre", "accion", "g", "profundidad")

    def __init__(self, estado: Estado, padre: Optional["Nodo"] = None,
                 accion: Optional[str] = None, g: int = 0):
        self.estado = estado
        self.padre = padre
        self.accion = accion
        self.g = g
        self.profundidad = 0 if padre is None else padre.profundidad + 1

    def hijo(self, problema: ProblemaExplorador, accion: str) -> "Nodo":
        s2 = problema.result(self.estado, accion)
        return Nodo(s2, self, accion, problema.path_cost(self.g, self.estado, accion, s2))

    def expandir(self, problema: ProblemaExplorador) -> List["Nodo"]:
        return [self.hijo(problema, a) for a in problema.actions(self.estado)]

    def solucion(self) -> List[str]:
        """Secuencia de acciones desde la raíz hasta este nodo."""
        acciones, n = [], self
        while n.padre is not None:
            acciones.append(n.accion)
            n = n.padre
        return acciones[::-1]

    def camino(self) -> List[Estado]:
        estados, n = [], self
        while n is not None:
            estados.append(n.estado)
            n = n.padre
        return estados[::-1]


# ---------------------------------------------------------------------- #
# Resultado y métricas
# ---------------------------------------------------------------------- #
@dataclass
class Resultado:
    algoritmo: str
    nodo: Optional[Nodo] = None
    nodos_expandidos: int = 0
    nodos_generados: int = 0
    max_frontera: int = 0
    max_memoria: int = 0
    tiempo_ms: float = 0.0
    acciones: List[str] = field(default_factory=list)

    @property
    def encontrado(self) -> bool:
        return self.nodo is not None

    @property
    def costo(self) -> Optional[int]:
        return self.nodo.g if self.nodo else None

    @property
    def profundidad(self) -> Optional[int]:
        return self.nodo.profundidad if self.nodo else None


def _cerrar(res: Resultado, nodo: Optional[Nodo], t0: float) -> Resultado:
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    res.nodo = nodo
    res.acciones = nodo.solucion() if nodo else []
    return res


# ---------------------------------------------------------------------- #
# BFS — búsqueda primero en anchura
# ---------------------------------------------------------------------- #
def bfs(problema: ProblemaExplorador) -> Resultado:
    """
    Frontera FIFO. La prueba de meta se aplica al GENERAR el nodo (versión de
    Russell y Norvig, fig. 3.11), lo que ahorra expandir el último nivel.
    Óptima en NÚMERO DE ACCIONES, pero no en costo cuando hay trampas
    (costos de paso distintos).
    Tiempo y espacio: O(b^d).
    """
    res, t0 = Resultado("BFS"), time.perf_counter()
    raiz = Nodo(problema.initial)
    if problema.goal_test(raiz.estado):
        return _cerrar(res, raiz, t0)
    frontera = deque([raiz])
    en_frontera = {raiz.estado}
    explorados = set()
    while frontera:
        res.max_frontera = max(res.max_frontera, len(frontera))
        res.max_memoria = max(res.max_memoria, len(frontera) + len(explorados))
        nodo = frontera.popleft()
        en_frontera.discard(nodo.estado)
        explorados.add(nodo.estado)
        res.nodos_expandidos += 1
        for hijo in nodo.expandir(problema):
            res.nodos_generados += 1
            if hijo.estado not in explorados and hijo.estado not in en_frontera:
                if problema.goal_test(hijo.estado):
                    return _cerrar(res, hijo, t0)
                frontera.append(hijo)
                en_frontera.add(hijo.estado)
    return _cerrar(res, None, t0)


# ---------------------------------------------------------------------- #
# DFS — búsqueda primero en profundidad
# ---------------------------------------------------------------------- #
def dfs(problema: ProblemaExplorador) -> Resultado:
    """
    Frontera LIFO (pila) con conjunto de explorados. Completa en espacios
    finitos, pero NO óptima: devuelve el primer camino que encuentra.
    Tiempo: O(b^m). Espacio: O(b·m) en la versión de árbol; con el conjunto de
    explorados (necesario aquí para evitar ciclos) el peor caso es O(|S|).
    """
    res, t0 = Resultado("DFS"), time.perf_counter()
    frontera = [Nodo(problema.initial)]
    explorados = set()
    while frontera:
        res.max_frontera = max(res.max_frontera, len(frontera))
        res.max_memoria = max(res.max_memoria, len(frontera) + len(explorados))
        nodo = frontera.pop()
        if nodo.estado in explorados:
            continue
        if problema.goal_test(nodo.estado):
            return _cerrar(res, nodo, t0)
        explorados.add(nodo.estado)
        res.nodos_expandidos += 1
        # Se apilan en orden inverso para que la primera acción aplicable
        # (Forward) sea la primera en explorarse.
        for hijo in reversed(nodo.expandir(problema)):
            res.nodos_generados += 1
            if hijo.estado not in explorados:
                frontera.append(hijo)
    return _cerrar(res, None, t0)


# ---------------------------------------------------------------------- #
# A* — búsqueda informada
# ---------------------------------------------------------------------- #
def astar(problema: ProblemaExplorador, h: Callable[[Estado], int],
          nombre: str = "A*") -> Resultado:
    """
    Frontera de prioridad ordenada por f(n) = g(n) + h(n). La prueba de meta se
    aplica al EXPANDIR el nodo, condición necesaria para garantizar
    optimalidad en costo. Si h es consistente, A* es óptimo y cada estado se
    expande a lo sumo una vez.
    Tiempo y espacio en el peor caso: O(b^d); con una buena heurística el
    número de nodos expandidos se reduce a O(b*^d), con b* < b.
    """
    res, t0 = Resultado(nombre), time.perf_counter()
    contador = itertools.count()  # desempate FIFO estable
    raiz = Nodo(problema.initial)
    frontera = [(h(raiz.estado), next(contador), raiz)]
    mejor_g = {raiz.estado: 0}
    explorados = set()
    while frontera:
        res.max_frontera = max(res.max_frontera, len(frontera))
        res.max_memoria = max(res.max_memoria, len(frontera) + len(explorados))
        _, _, nodo = heapq.heappop(frontera)
        if nodo.estado in explorados:
            continue  # entrada obsoleta (se encontró antes un camino mejor)
        if problema.goal_test(nodo.estado):
            return _cerrar(res, nodo, t0)
        explorados.add(nodo.estado)
        res.nodos_expandidos += 1
        for hijo in nodo.expandir(problema):
            res.nodos_generados += 1
            s = hijo.estado
            if s in explorados:
                continue
            if hijo.g < mejor_g.get(s, float("inf")):
                mejor_g[s] = hijo.g
                heapq.heappush(frontera, (hijo.g + h(s), next(contador), hijo))
    return _cerrar(res, None, t0)
