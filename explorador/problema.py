"""
problema.py — Problema de búsqueda que resuelve el agente cada vez que planifica
una ruta (Russell & Norvig, 2016, cap. 3 y sec. 7.7, función PlanRoute).

ABSTRACCIÓN
-----------
El agente NO conoce el mapa. Lo que sí conoce con certeza es su MODELO INTERNO:
las casillas que ya demostró que son seguras (ver conocimiento.py). Dentro de
esa zona segura el entorno es determinista y discreto: cada acción tiene un
único resultado conocido. Por eso la búsqueda se hace solo sobre casillas
seguras, y nunca sobre casillas desconocidas.

ESPACIO DE ESTADOS (de cada búsqueda)
-------------------------------------
Estado s = (x, y, d)
    x, y : casilla del agente (debe ser segura)
    d    : orientación, 0=Este, 1=Norte, 2=Oeste, 3=Sur
Estado inicial  : posición y orientación actuales del agente
Acciones        : {Forward, TurnLeft, TurnRight}
                  (Grab y Climb no mueven al agente; las ejecuta el agente
                  directamente al llegar, fuera de la búsqueda)
Transición      : Forward avanza una casilla en la dirección d, solo si la
                  casilla destino es segura; los giros cambian d en ±90°.
Prueba de meta  : (x, y) == casilla objetivo (en cualquier orientación)
Costo de paso   : 1 por acción; +50 si Forward entra a una trampa YA CONOCIDA
"""

from __future__ import annotations

from typing import FrozenSet, List, NamedTuple, Tuple

Casilla = Tuple[int, int]

# Orientaciones en sentido antihorario: girar a la izquierda suma 1 (mod 4).
ESTE, NORTE, OESTE, SUR = 0, 1, 2, 3
DELTA = {ESTE: (1, 0), NORTE: (0, 1), OESTE: (-1, 0), SUR: (0, -1)}
NOMBRE_DIR = {ESTE: "E", NORTE: "N", OESTE: "O", SUR: "S"}

FORWARD, TURN_LEFT, TURN_RIGHT, GRAB, CLIMB = (
    "Forward", "TurnLeft", "TurnRight", "Grab", "Climb")

COSTO_ACCION = 1
PENALIZACION_TRAMPA = 50


class Pose(NamedTuple):
    """Estado de la búsqueda: casilla y orientación del agente."""
    x: int
    y: int
    d: int

    @property
    def casilla(self) -> Casilla:
        return (self.x, self.y)

    def adelante(self) -> Casilla:
        dx, dy = DELTA[self.d]
        return (self.x + dx, self.y + dy)


class ProblemaRuta:
    """
    Ir desde la pose actual hasta la casilla `destino` pasando solo por
    casillas `seguras`. Sigue la interfaz de AIMA-Python.
    """

    def __init__(self, inicio: Pose, destino: Casilla,
                 seguras: FrozenSet[Casilla], trampas_conocidas: FrozenSet[Casilla] = frozenset()):
        self.initial = inicio
        self.destino = destino
        self.seguras = seguras
        self.trampas = trampas_conocidas

    def actions(self, s: Pose) -> List[str]:
        acciones = [TURN_LEFT, TURN_RIGHT]
        if s.adelante() in self.seguras:
            acciones.insert(0, FORWARD)
        return acciones

    def result(self, s: Pose, a: str) -> Pose:
        if a == FORWARD:
            x, y = s.adelante()
            return Pose(x, y, s.d)
        if a == TURN_LEFT:
            return Pose(s.x, s.y, (s.d + 1) % 4)
        if a == TURN_RIGHT:
            return Pose(s.x, s.y, (s.d - 1) % 4)
        raise ValueError(f"Acción no válida en la búsqueda: {a}")

    def goal_test(self, s: Pose) -> bool:
        return s.casilla == self.destino

    def step_cost(self, s: Pose, a: str, s2: Pose) -> int:
        costo = COSTO_ACCION
        if a == FORWARD and s2.casilla in self.trampas:
            costo += PENALIZACION_TRAMPA
        return costo

    def path_cost(self, c: int, s: Pose, a: str, s2: Pose) -> int:
        return c + self.step_cost(s, a, s2)

    def tamano_espacio(self) -> int:
        """|S| = 4 · (número de casillas seguras)."""
        return 4 * len(self.seguras)
