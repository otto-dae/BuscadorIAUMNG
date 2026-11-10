r"""
heuristica.py — Funciones heurísticas h(n) para A*.

h_manhattan_giros (heurística principal, ADMISIBLE)
---------------------------------------------------
Estima el costo mínimo para llegar de la pose (x, y, d) a la casilla destino:

    h(n) = |x − x_dest| + |y − y_dest|  +  giros mínimos
           \______ avances ________/

Avances: cada Forward mueve exactamente una casilla, así que hacen falta al
menos tantos avances como la distancia Manhattan (los rodeos solo la alargan).

Giros mínimos: el agente solo avanza hacia donde mira. Sea D el conjunto de
direcciones en las que tiene que avanzar (1 dirección si el destino está en la
misma fila o columna, 2 si no):
  - si D tiene 1 dirección: 0 giros si ya mira hacia ella, 1 si es
    perpendicular, 2 si es la opuesta;
  - si D tiene 2 direcciones: tendrá que mirar hacia ambas, así que al menos
    1 giro si ya mira hacia una de ellas, y 2 si no mira hacia ninguna.

Admisible: cuenta solo acciones que cualquier ruta debe ejecutar sí o sí, y
cada una cuesta ≥ 1; ignora rodeos y trampas, que solo encarecen la ruta.
Las pruebas (tests/) verifican además que es CONSISTENTE.

h_cero
------
h(n) = 0. Con ella A* se convierte en búsqueda de costo uniforme (UCS); sirve
como línea base para medir cuánto ayuda la heurística.
"""

from __future__ import annotations

from .problema import ESTE, NORTE, OESTE, SUR, Pose


def _giros(desde: int, hacia: int) -> int:
    diferencia = (hacia - desde) % 4
    return 2 if diferencia == 2 else (0 if diferencia == 0 else 1)


def h_manhattan_giros(s: Pose, destino) -> int:
    dx, dy = destino[0] - s.x, destino[1] - s.y
    direcciones = []
    if dx:
        direcciones.append(ESTE if dx > 0 else OESTE)
    if dy:
        direcciones.append(NORTE if dy > 0 else SUR)
    avances = abs(dx) + abs(dy)
    if not direcciones:
        giros = 0
    elif len(direcciones) == 1:
        giros = _giros(s.d, direcciones[0])
    else:
        giros = 1 if s.d in direcciones else 2
    return avances + giros


def h_cero(s: Pose, destino) -> int:
    return 0
