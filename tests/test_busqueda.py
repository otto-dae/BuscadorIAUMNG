"""
Pruebas automáticas (solo biblioteca estándar):

    python -m unittest discover -s tests -v

Verifican que:
  - el agente nunca entra a un hoyo y siempre sale por (1,1);
  - el agente solo pisa casillas que su modelo ya había demostrado seguras;
  - las rutas de los tres algoritmos son válidas y A* encuentra la más barata;
  - la heurística es admisible y consistente.
"""

import itertools
import unittest

from explorador import (PLANIFICADORES, AgenteExplorador, Pose, ProblemaRuta, astar, bfs,
                        dfs, generar_mundo, h_cero, h_manhattan_giros)
from explorador.problema import FORWARD


def rejilla(n, hoyos=()):
    return frozenset((x, y) for x in range(1, n + 1) for y in range(1, n + 1)) - set(hoyos)


def problemas_aleatorios(cantidad=40):
    """Problemas de ruta sobre zonas seguras de mundos aleatorios."""
    for semilla in range(cantidad):
        w = generar_mundo(7, 3, 3, semilla=semilla)
        seguras = frozenset(w.alcanzables())
        destinos = sorted(seguras)
        destino = destinos[(semilla * 7) % len(destinos)]
        yield ProblemaRuta(Pose(1, 1, semilla % 4), destino, seguras, frozenset(w.trampas & seguras))


class TestAgente(unittest.TestCase):

    def test_nunca_cae_y_siempre_sale(self):
        for semilla, alg in itertools.product(range(25), PLANIFICADORES):
            w = generar_mundo(8, 4, 3, semilla=semilla)
            ep = AgenteExplorador(alg).ejecutar(w)
            with self.subTest(semilla=semilla, alg=alg):
                self.assertFalse(ep.murio)
                self.assertTrue(ep.salio)
                self.assertEqual(ep.acciones[-1], "Climb")

    def test_solo_pisa_casillas_seguras(self):
        """Ninguna casilla del recorrido contiene un hoyo."""
        for semilla in range(25):
            w = generar_mundo(10, 5, 4, semilla=semilla)
            ep = AgenteExplorador("A* con heurística").ejecutar(w)
            with self.subTest(semilla=semilla):
                self.assertFalse(set(ep.recorrido) & w.hoyos)

    def test_mismo_conocimiento_mismos_objetos(self):
        """Todos los planificadores exploran la misma zona segura y recogen lo mismo."""
        for semilla in range(15):
            w = generar_mundo(10, 5, 4, semilla=semilla)
            objetos = {AgenteExplorador(a).ejecutar(w).objetos for a in PLANIFICADORES}
            with self.subTest(semilla=semilla):
                self.assertEqual(len(objetos), 1)


class TestRutas(unittest.TestCase):

    def test_rutas_validas(self):
        for p in problemas_aleatorios():
            for res in (bfs(p), dfs(p), astar(p, lambda s: h_manhattan_giros(s, p.destino))):
                with self.subTest(destino=p.destino, alg=res.algoritmo):
                    s, costo = p.initial, 0
                    for a in res.acciones:
                        self.assertIn(a, p.actions(s))
                        s2 = p.result(s, a)
                        costo += p.step_cost(s, a, s2)
                        if a == FORWARD:
                            self.assertIn(s2.casilla, p.seguras)
                        s = s2
                    self.assertTrue(p.goal_test(s))
                    self.assertEqual(costo, res.costo)

    def test_astar_es_optimo(self):
        for p in problemas_aleatorios():
            with self.subTest(destino=p.destino):
                con_h = astar(p, lambda s: h_manhattan_giros(s, p.destino))
                sin_h = astar(p, lambda s: h_cero(s, p.destino))
                self.assertEqual(con_h.costo, sin_h.costo)
                self.assertLessEqual(con_h.nodos_expandidos, sin_h.nodos_expandidos)
                self.assertLessEqual(con_h.costo, bfs(p).costo)
                self.assertLessEqual(con_h.costo, dfs(p).costo)


class TestHeuristica(unittest.TestCase):

    def test_admisible(self):
        """h(s) <= costo real mínimo, para todas las poses y destinos de una rejilla con hoyos."""
        seguras = rejilla(5, hoyos=[(3, 3), (2, 4), (4, 2)])
        for destino in seguras:
            for c, d in itertools.product(seguras, range(4)):
                s = Pose(c[0], c[1], d)
                optimo = astar(ProblemaRuta(s, destino, seguras), lambda s: 0).costo
                with self.subTest(s=s, destino=destino):
                    self.assertLessEqual(h_manhattan_giros(s, destino), optimo)

    def test_consistente(self):
        """h(s) <= c(s, a, s') + h(s') para toda transición."""
        seguras = rejilla(6, hoyos=[(3, 3), (4, 4), (2, 5)])
        for destino in seguras:
            p = ProblemaRuta(Pose(1, 1, 0), destino, seguras)
            for c, d in itertools.product(seguras, range(4)):
                s = Pose(c[0], c[1], d)
                for a in p.actions(s):
                    s2 = p.result(s, a)
                    with self.subTest(s=s, a=a, destino=destino):
                        self.assertLessEqual(h_manhattan_giros(s, destino),
                                             p.step_cost(s, a, s2) + h_manhattan_giros(s2, destino))


if __name__ == "__main__":
    unittest.main()
