# Juego del explorador: agente con búsqueda BFS, DFS y A*

Proyecto Integrador de Inteligencia Artificial, Fase 2: implementación algorítmica y análisis de complejidad.
Integrantes: Rodrigo Fernández Rojas y Otto de Acha Estrada.

Un agente recorre una rejilla de N × N con hoyos, trampas y objetos de valor **sin conocer el mapa**. Solo recibe pistas locales: brisa si hay un hoyo cerca, destello si hay un objeto en su casilla, golpe si choca con un muro y trampa si pisó una.

Con esas pistas, el agente va deduciendo qué casillas son seguras. Cada vez que necesita moverse, usa **BFS, DFS o A\*** para trazar una ruta **solo por casillas seguras**. Es el esquema del agente híbrido del mundo de Wumpus de Russell y Norvig, con la función *PlanRoute*.

## Requisitos

- Python 3.9 o superior.
- Nada que instalar: solo usa la biblioteca estándar.

## Uso

```bash
git clone https://github.com/rodrigofdzr/explorador-busqueda-ia.git
cd explorador-busqueda-ia

python demo.py                                   # un episodio con cada planificador
python demo.py --algoritmo "A* con heurística" --acciones
python benchmark.py                              # 30 tableros por tamaño -> resultados/
python -m unittest discover -s tests -v          # pruebas
```

## Cómo funciona el agente

1. **Percibe** `[Breeze, Glitter, Bump, Trapped]` en su casilla.
2. **Actualiza su modelo** (`conocimiento.py`):
   - toda casilla visitada es segura;
   - si en una casilla no hay brisa, sus vecinas también son seguras.
3. Si hay destello, hace **Grab**.
4. **Elige una meta**: la casilla segura sin visitar más cercana. Si ya tiene todos los objetos o no quedan casillas seguras por visitar, la meta es volver a (1,1).
5. **Planifica** la ruta con BFS, DFS o A\* sobre las casillas seguras (`problema.py` y `busqueda.py`).
6. **Ejecuta** la ruta y, al volver a (1,1), hace **Climb**.

El agente es conservador: nunca entra a una casilla desconocida, así que **nunca cae en un hoyo**.

## Estructura

```
explorador/
  mundo.py         Tablero real (oculto al agente) y generación reproducible por semilla
  conocimiento.py  Modelo interno: casillas visitadas, seguras, con brisa y trampas conocidas
  problema.py      Problema de búsqueda de ruta: estado (x, y, dirección), acciones, meta, costo
  heuristica.py    h = distancia Manhattan + giros mínimos (admisible) y h = 0 (línea base)
  busqueda.py      BFS, DFS y A* (búsqueda en grafos) con métricas
  agente.py        Ciclo percibir -> actualizar -> elegir meta -> planificar -> ejecutar
benchmark.py       Compara los planificadores sobre los mismos tableros
demo.py            Demostración en consola
tests/             Pruebas: seguridad del agente, validez de rutas, optimalidad de A*, heurística
```

## Problema de búsqueda (cada vez que el agente planifica)

| Elemento | Definición |
|---|---|
| Estado | `(x, y, d)`: casilla y dirección (E, N, O, S) |
| Estado inicial | Posición y dirección actuales del agente |
| Acciones | `Forward` (solo hacia casillas seguras), `TurnLeft`, `TurnRight` |
| Meta | Llegar a la casilla objetivo |
| Costo | 1 por acción, +50 si entra a una trampa ya conocida |

## Resultados

Promedio por episodio en 30 tableros de 12 × 12; las cifras completas están en `resultados/benchmark.md`.

| Planificador | Nodos expandidos | Memoria pico | Acciones | Puntaje |
|---|---|---|---|---|
| BFS | 153.1 | 58.1 | 55.8 | 760.9 |
| DFS | 337.5 | 104.7 | 282.8 | 302.2 |
| A\* sin heurística | 210.3 | 64.2 | 56.4 | 768.6 |
| **A\* con heurística** | **71.8** | **32.9** | 56.4 | **768.6** |

## Referencias

- Russell, S. J., & Norvig, P. (2016). *Artificial intelligence: A modern approach* (3rd ed.). Pearson.
- Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. *IEEE Transactions on Systems Science and Cybernetics, 4*(2), 100–107.
- aimacode. (s. f.). *aima-python* [Código fuente]. GitHub. https://github.com/aimacode/aima-python
