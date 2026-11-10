"""
benchmark.py — Compara BFS, DFS y A* como planificadores del agente explorador.

Para cada tamaño de tablero se generan 30 tableros con semillas 0..29. Los
cuatro planificadores se ejecutan sobre LOS MISMOS tableros y el mismo estado
inicial (agente en (1,1) mirando al este, sin conocer el mapa). Se reporta el
promedio por episodio.

Uso:
    python benchmark.py
    python benchmark.py --tableros 50

Salidas en resultados/: benchmark.csv, benchmark.md y ejemplo.txt
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from explorador import PLANIFICADORES, AgenteExplorador, generar_mundo

# (N, k objetos, m trampas)
TAMANOS = [(6, 3, 2), (8, 4, 3), (10, 5, 4), (12, 6, 5)]


def ejecutar(num_tableros: int = 30):
    filas = []
    for n, k, m in TAMANOS:
        mundos = [generar_mundo(n, k, m, semilla=s) for s in range(num_tableros)]
        for alg in PLANIFICADORES:
            eps = [AgenteExplorador(alg).ejecutar(w) for w in mundos]
            assert not any(e.murio for e in eps), "el agente nunca debe caer en un hoyo"
            prom = lambda f: statistics.mean(f(e) for e in eps)
            filas.append({
                "N": n, "k": k, "m": m, "tableros": num_tableros, "algoritmo": alg,
                "busquedas": round(prom(lambda e: e.busquedas), 1),
                "expandidos": round(prom(lambda e: e.nodos_expandidos), 1),
                "memoria_pico": round(prom(lambda e: e.memoria_pico), 1),
                "tiempo_ms": round(prom(lambda e: e.tiempo_busqueda_ms), 2),
                "acciones": round(prom(lambda e: len(e.acciones)), 1),
                "trampas": round(prom(lambda e: e.trampas_activadas), 2),
                "objetos": round(prom(lambda e: e.objetos), 2),
                "puntaje": round(prom(lambda e: e.puntaje), 1),
                "visitadas": round(prom(lambda e: e.casillas_visitadas), 1),
            })
    return filas


def ejemplo(n=10, k=5, m=4, semilla=5) -> str:
    """Muestra en texto un episodio concreto para cada planificador."""
    w = generar_mundo(n, k, m, semilla=semilla)
    salida = [f"Tablero {n}x{n}, semilla {semilla}\n{w.dibujar()}\n"]
    for alg in PLANIFICADORES:
        e = AgenteExplorador(alg).ejecutar(w)
        salida.append(f"--- {alg}: objetos={e.objetos}/{k} acciones={len(e.acciones)} "
                      f"trampas={e.trampas_activadas} puntaje={e.puntaje} "
                      f"expandidos={e.nodos_expandidos}\n{w.dibujar(e.recorrido)}\n")
    return "\n".join(salida)


def guardar(filas, carpeta: Path):
    carpeta.mkdir(exist_ok=True)
    with open(carpeta / "benchmark.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    cols = ["N", "algoritmo", "expandidos", "memoria_pico", "tiempo_ms",
            "acciones", "trampas", "objetos", "puntaje"]
    lineas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lineas += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in filas]
    (carpeta / "benchmark.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    (carpeta / "ejemplo.txt").write_text(ejemplo(), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tableros", type=int, default=30, help="tableros por tamaño")
    args = ap.parse_args()
    filas = ejecutar(args.tableros)
    carpeta = Path(__file__).parent / "resultados"
    guardar(filas, carpeta)
    print((carpeta / "benchmark.md").read_text())


if __name__ == "__main__":
    main()
