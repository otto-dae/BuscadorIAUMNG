"""
agente.py — Agente explorador basado en metas que NO conoce el mapa.

Ciclo del agente (adaptado del agente híbrido de Russell & Norvig, 2016, fig. 7.20):

    1. PERCIBIR    recibe [Breeze, Glitter, Bump, Trapped] en su casilla.
    2. ACTUALIZAR  incorpora la percepción a su modelo (conocimiento.py).
    3. Si hay Glitter -> Grab.
    4. ELEGIR META si ya tiene todos los objetos o no quedan casillas seguras
                   sin visitar -> la meta es (1,1) para salir; si no, la meta es
                   la casilla segura sin visitar más cercana.
    5. PLANIFICAR  busca la ruta con BFS, DFS o A* SOLO sobre casillas seguras.
    6. EJECUTAR    sigue la ruta paso a paso, percibiendo en cada casilla.
    7. Al llegar a (1,1) con la meta de salir -> Climb.

El mundo real (mundo.py) está oculto para el agente: solo lo usa el simulador
para generar las percepciones y aplicar las consecuencias de cada acción.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List

from .busqueda import Resultado, astar, bfs, dfs
from .conocimiento import BaseConocimiento
from .heuristica import h_cero, h_manhattan_giros
from .mundo import INICIO, Mundo
from .problema import (CLIMB, ESTE, FORWARD, GRAB, PENALIZACION_TRAMPA, TURN_LEFT,
                       TURN_RIGHT, Pose, ProblemaRuta)

PUNTOS_OBJETO = 1000


# Planificadores disponibles: reciben un ProblemaRuta y devuelven un Resultado.
PLANIFICADORES = {
    "BFS": lambda p: bfs(p),
    "DFS": lambda p: dfs(p),
    "A* sin heurística": lambda p: astar(p, lambda s: h_cero(s, p.destino), "A* sin heurística"),
    "A* con heurística": lambda p: astar(p, lambda s: h_manhattan_giros(s, p.destino), "A* con heurística"),
}


@dataclass
class Episodio:
    """Métricas de un episodio completo (entrar, explorar y salir)."""
    algoritmo: str
    acciones: List[str] = field(default_factory=list)
    recorrido: List[tuple] = field(default_factory=list)
    objetos: int = 0
    trampas_activadas: int = 0
    salio: bool = False
    murio: bool = False
    busquedas: int = 0
    nodos_expandidos: int = 0
    nodos_generados: int = 0
    memoria_pico: int = 0
    tiempo_busqueda_ms: float = 0.0
    casillas_visitadas: int = 0

    @property
    def puntaje(self) -> int:
        """Medida de desempeño de la Fase 1: +1000/objeto, −1/acción, −50/trampa, −1000 hoyo."""
        if self.murio:
            return -1000 - len(self.acciones)
        return (PUNTOS_OBJETO * self.objetos - len(self.acciones)
                - PENALIZACION_TRAMPA * self.trampas_activadas)


class AgenteExplorador:
    def __init__(self, planificador: str = "A* con heurística"):
        self.nombre = planificador
        self.planificar: Callable[[ProblemaRuta], Resultado] = PLANIFICADORES[planificador]

    def ejecutar(self, mundo: Mundo, max_acciones: int = 10_000) -> Episodio:
        ep = Episodio(self.nombre)
        kb = BaseConocimiento(mundo.n)
        pose = Pose(INICIO[0], INICIO[1], ESTE)
        objetos_restantes = set(mundo.objetos)     # estado real (oculto al agente)
        k = len(mundo.objetos)                     # el agente sabe cuántos objetos hay

        def percibir(llego_ahora: bool):
            c = pose.casilla
            atrapado = llego_ahora and c in mundo.trampas
            if atrapado:
                ep.trampas_activadas += 1
            kb.actualizar(c, brisa=mundo.hay_brisa(c), atrapado=atrapado)
            ep.recorrido.append(c)
            return c in objetos_restantes          # Glitter

        if percibir(llego_ahora=False):
            ep.acciones.append(GRAB); objetos_restantes.discard(pose.casilla); ep.objetos += 1

        while len(ep.acciones) < max_acciones:
            # 4. Elegir meta
            pendientes = kb.seguras_sin_visitar()
            if ep.objetos == k or not pendientes:
                destino = INICIO
            else:
                destino = min(pendientes, key=lambda c: (abs(c[0] - pose.x) + abs(c[1] - pose.y), c))

            if pose.casilla == destino == INICIO and (ep.objetos == k or not pendientes):
                ep.acciones.append(CLIMB)
                ep.salio = True
                break

            # 5. Planificar ruta sobre casillas seguras
            problema = ProblemaRuta(pose, destino, frozenset(kb.seguras), frozenset(kb.trampas))
            res = self.planificar(problema)
            ep.busquedas += 1
            ep.nodos_expandidos += res.nodos_expandidos
            ep.nodos_generados += res.nodos_generados
            ep.memoria_pico = max(ep.memoria_pico, res.max_memoria)
            ep.tiempo_busqueda_ms += res.tiempo_ms
            if not res.encontrado:           # no debería ocurrir: la zona segura es conexa
                break

            # 6. Ejecutar la ruta paso a paso
            for a in res.acciones:
                ep.acciones.append(a)
                if a == FORWARD:
                    pose = Pose(*pose.adelante(), pose.d)
                    if pose.casilla in mundo.hoyos:   # imposible si el modelo es correcto
                        ep.murio = True
                        return self._cerrar(ep, kb)
                    if percibir(llego_ahora=True):
                        ep.acciones.append(GRAB)
                        objetos_restantes.discard(pose.casilla)
                        ep.objetos += 1
                elif a == TURN_LEFT:
                    pose = Pose(pose.x, pose.y, (pose.d + 1) % 4)
                elif a == TURN_RIGHT:
                    pose = Pose(pose.x, pose.y, (pose.d - 1) % 4)
        return self._cerrar(ep, kb)

    @staticmethod
    def _cerrar(ep: Episodio, kb: BaseConocimiento) -> Episodio:
        ep.casillas_visitadas = len(kb.visitadas)
        return ep
