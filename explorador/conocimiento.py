"""
conocimiento.py — Modelo interno del agente (lo que sabe del tablero).

El agente empieza sin conocer el mapa. Cada vez que llega a una casilla recibe
la percepción [Breeze, Glitter, Bump, Trapped] y actualiza su modelo con dos
reglas lógicas (razonamiento lógico de la Fase 1):

  R1. Toda casilla visitada es segura (el agente sigue vivo).
  R2. Si en una casilla visitada NO hay brisa, ninguna de sus vecinas tiene
      hoyo, así que todas sus vecinas son seguras.

Además registra las trampas que ya activó (percepción Trapped) para que el
planificador les asigne su costo y las evite en adelante.

El agente es CONSERVADOR: solo entra a casillas demostradas como seguras.
Nunca arriesga, por lo que nunca cae en un hoyo; a cambio, puede dejar sin
recoger objetos que estén rodeados de brisa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set, Tuple

Casilla = Tuple[int, int]


@dataclass
class BaseConocimiento:
    n: int
    visitadas: Set[Casilla] = field(default_factory=set)
    seguras: Set[Casilla] = field(default_factory=lambda: {(1, 1)})
    con_brisa: Set[Casilla] = field(default_factory=set)
    trampas: Set[Casilla] = field(default_factory=set)

    def vecinos(self, c: Casilla):
        x, y = c
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (x + dx, y + dy)
            if 1 <= v[0] <= self.n and 1 <= v[1] <= self.n:
                yield v

    def actualizar(self, casilla: Casilla, brisa: bool, atrapado: bool) -> None:
        """Incorpora la percepción recibida en `casilla`."""
        self.visitadas.add(casilla)
        self.seguras.add(casilla)                 # R1
        if atrapado:
            self.trampas.add(casilla)
        if brisa:
            self.con_brisa.add(casilla)
        else:
            self.seguras.update(self.vecinos(casilla))  # R2

    def seguras_sin_visitar(self) -> Set[Casilla]:
        """Frontera de exploración: casillas seguras a las que aún no ha ido."""
        return self.seguras - self.visitadas
