"""
mundo.py — Representación del mundo de rejilla del juego del explorador.

El mundo es una cuadrícula N x N con coordenadas (x, y), donde x es la columna
y y es la fila, ambas en el rango 1..N. La casilla (1, 1) es la esquina inferior
izquierda: es la entrada, la salida y siempre es segura.

Cada casilla puede contener:
    - un hoyo   (caer en él termina el episodio),
    - una trampa (no es mortal, pero penaliza al agente),
    - un objeto de valor (tesoro).

En la Fase 2 el mundo se usa como MAPA CONOCIDO: el agente planifica sobre él
con algoritmos de búsqueda (ver problema.py). La generación aleatoria reproduce
la configuración de la Fase 1 (hoyos con probabilidad p = 0.2, k objetos y
m trampas colocados al azar), pero con una semilla fija para que todos los
algoritmos se evalúen exactamente sobre el mismo estado inicial.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Tuple

Casilla = Tuple[int, int]

INICIO: Casilla = (1, 1)


@dataclass(frozen=True)
class Mundo:
    """Configuración completa (y conocida) de un tablero N x N."""

    n: int
    hoyos: FrozenSet[Casilla] = field(default_factory=frozenset)
    trampas: FrozenSet[Casilla] = field(default_factory=frozenset)
    objetos: FrozenSet[Casilla] = field(default_factory=frozenset)

    # ------------------------------------------------------------------ #
    # Consultas básicas
    # ------------------------------------------------------------------ #
    def dentro(self, c: Casilla) -> bool:
        """True si la casilla está dentro de los muros perimetrales."""
        x, y = c
        return 1 <= x <= self.n and 1 <= y <= self.n

    def vecinos(self, c: Casilla) -> Iterable[Casilla]:
        """Casillas ortogonalmente adyacentes (sin diagonales) dentro del tablero."""
        x, y = c
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (x + dx, y + dy)
            if self.dentro(v):
                yield v

    def hay_brisa(self, c: Casilla) -> bool:
        """Percepción Breeze: algún vecino directo contiene un hoyo."""
        return any(v in self.hoyos for v in self.vecinos(c))

    def alcanzables(self) -> set:
        """Casillas alcanzables desde (1,1) sin pisar hoyos (BFS sobre la rejilla)."""
        vistos = {INICIO}
        cola = deque([INICIO])
        while cola:
            c = cola.popleft()
            for v in self.vecinos(c):
                if v not in vistos and v not in self.hoyos:
                    vistos.add(v)
                    cola.append(v)
        return vistos

    def es_resoluble(self) -> bool:
        """Todos los objetos pueden recogerse y el agente puede volver a (1,1)."""
        return set(self.objetos) <= self.alcanzables()

    # ------------------------------------------------------------------ #
    # Visualización
    # ------------------------------------------------------------------ #
    def dibujar(self, ruta: Iterable[Casilla] = ()) -> str:
        """
        Dibuja el tablero en ASCII (fila N arriba, fila 1 abajo).

            A = inicio/salida   P = hoyo (pit)   T = trampa
            G = objeto (gold)   * = casilla recorrida por la solución
            ~ = brisa percibida  . = casilla vacía
        """
        ruta = set(ruta)
        filas = []
        for y in range(self.n, 0, -1):
            celdas = []
            for x in range(1, self.n + 1):
                c = (x, y)
                if c == INICIO:
                    s = "A"
                elif c in self.hoyos:
                    s = "P"
                elif c in self.objetos:
                    s = "G"
                elif c in self.trampas:
                    s = "T"
                elif c in ruta:
                    s = "*"
                elif self.hay_brisa(c):
                    s = "~"
                else:
                    s = "."
                celdas.append(s)
            filas.append(f"{y:>2} " + " ".join(celdas))
        filas.append("   " + " ".join(str(x % 10) for x in range(1, self.n + 1)))
        return "\n".join(filas)


def generar_mundo(n: int, k: int, m: int, p: float = 0.2, semilla: int = 0) -> Mundo:
    """
    Genera un mundo aleatorio RESOLUBLE y reproducible.

    Args:
        n: tamaño de la rejilla (n x n).
        k: número de objetos de valor.
        m: número de trampas.
        p: probabilidad independiente de hoyo por casilla (excepto (1,1)).
        semilla: semilla del generador; misma semilla => mismo mundo.

    Se repite el sorteo (incrementando la semilla interna) hasta obtener un
    tablero en el que todos los objetos sean alcanzables sin pisar hoyos.
    También se mantienen libres de hoyos (1,1) y sus vecinos, para que el
    agente no quede encerrado desde el inicio.
    """
    rng = random.Random(semilla)
    protegidas = {INICIO, (1, 2), (2, 1)}
    for _ in range(10_000):
        casillas = [(x, y) for x in range(1, n + 1) for y in range(1, n + 1)]
        hoyos = {c for c in casillas if c not in protegidas and rng.random() < p}
        libres = [c for c in casillas if c not in hoyos and c != INICIO]
        if len(libres) < k + m:
            continue
        rng.shuffle(libres)
        objetos = frozenset(libres[:k])
        trampas = frozenset(libres[k:k + m])
        mundo = Mundo(n, frozenset(hoyos), trampas, objetos)
        if mundo.es_resoluble():
            return mundo
    raise RuntimeError("No se pudo generar un mundo resoluble con esos parámetros")
