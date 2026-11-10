"""
demo.py — Muestra un episodio del agente explorador (sin mapa) con cada planificador.

Uso:
    python demo.py                                  # tablero 10x10, semilla 5
    python demo.py --n 8 --k 4 --m 3 --semilla 3
    python demo.py --algoritmo "A* con heurística" --acciones
"""

import argparse

from explorador import PLANIFICADORES, AgenteExplorador, generar_mundo


def main():
    ap = argparse.ArgumentParser(description="Demostración del agente explorador")
    ap.add_argument("--n", type=int, default=10, help="tamaño de la rejilla N")
    ap.add_argument("--k", type=int, default=5, help="número de objetos")
    ap.add_argument("--m", type=int, default=4, help="número de trampas")
    ap.add_argument("--semilla", type=int, default=5)
    ap.add_argument("--algoritmo", choices=[*PLANIFICADORES, "todos"], default="todos")
    ap.add_argument("--acciones", action="store_true", help="imprime la secuencia de acciones")
    args = ap.parse_args()

    mundo = generar_mundo(args.n, args.k, args.m, semilla=args.semilla)
    print(f"Tablero {args.n}x{args.n} | objetos={args.k} trampas={args.m} hoyos={len(mundo.hoyos)}")
    print("El agente NO ve este mapa: solo recibe percepciones locales.")
    print("A=inicio  P=hoyo  T=trampa  G=objeto  ~=brisa  *=casilla visitada\n")
    print(mundo.dibujar(), "\n")

    elegidos = PLANIFICADORES if args.algoritmo == "todos" else [args.algoritmo]
    for nombre in elegidos:
        ep = AgenteExplorador(nombre).ejecutar(mundo)
        print(f"--- Planificador {nombre}: objetos={ep.objetos}/{args.k}  "
              f"acciones={len(ep.acciones)}  trampas={ep.trampas_activadas}  "
              f"puntaje={ep.puntaje}  búsquedas={ep.busquedas}  "
              f"nodos expandidos={ep.nodos_expandidos}")
        print(mundo.dibujar(ep.recorrido))
        if args.acciones:
            print(" -> ".join(ep.acciones))
        print()


if __name__ == "__main__":
    main()
