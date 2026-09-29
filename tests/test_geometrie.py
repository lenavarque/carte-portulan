import unittest

from carte_portulan.geometrie import (Grille, chemin, couper_rectangle, dans_boite, etendue, etoile, morceaux,
                                      par_cases, sans_bords, simplifier, simplifier_par_zones, traverser)


class TestSimplifier(unittest.TestCase):
    def test_points_alignes(self):
        ligne = [(0, 0), (1, 0.001), (2, 0), (3, 0)]
        self.assertEqual(simplifier(ligne, 0.1), [(0, 0), (3, 0)])

    def test_garde_les_ecarts(self):
        ligne = [(0, 0), (1, 5), (2, 0)]
        self.assertEqual(simplifier(ligne, 1), ligne)

    def test_courte(self):
        self.assertEqual(simplifier([(0, 0), (1, 1)], 10), [(0, 0), (1, 1)])


def aire(poly):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2


class TestCases(unittest.TestCase):
    def test_couper_rectangle(self):
        carre = [(-5, -5), (5, -5), (5, 5), (-5, 5), (-5, -5)]
        self.assertEqual(aire(couper_rectangle(carre, 0, 0, 10, 10)), 25)
        self.assertEqual(couper_rectangle(carre, 20, 20, 30, 30), [])

    def test_polygone_decoupe_sans_perte(self):
        # un « U » concave, à cheval sur quatre cases de 10 : la somme des morceaux fait l'aire d'origine
        u = [(2, 2), (18, 2), (18, 18), (14, 18), (14, 6), (6, 6), (6, 18), (2, 18)]
        cases = par_cases([u], 10, "decouper")
        self.assertEqual(set(cases), {(0, 0), (1, 0), (0, 1), (1, 1)})
        self.assertAlmostEqual(sum(aire(p) for morceaux in cases.values() for p in morceaux), aire(u))

    def test_ligne_coupee_sans_doublon(self):
        ligne = [(1, 1), (5, 1), (12, 1), (15, 1), (25, 1)]
        cases = par_cases([ligne], 10, "couper")
        self.assertEqual(cases, {(0, 0): [[(1, 1), (5, 1), (12, 1)]], (1, 0): [[(12, 1), (15, 1), (25, 1)]]})
        # chaque segment d'origine est tracé une fois, et les morceaux se raccordent
        segments = [s for morceaux in cases.values() for m in morceaux for s in zip(m, m[1:])]
        self.assertEqual(sorted(segments), sorted(zip(ligne, ligne[1:])))

    def test_polygone_entier(self):
        lac = [(8, 1), (13, 1), (13, 3), (8, 3)]
        self.assertEqual(par_cases([lac], 10, "entier"), {(1, 0): [lac]})


class TestCotes(unittest.TestCase):
    def test_simplifier_par_zones(self):
        # une ligne presque droite : gardée fine dans la zone (tolérance 0,01), simplifiée hors d'elle (tolérance 1)
        ligne = [(0, 0), (1, 0.1), (2, 0), (3, 0.1), (4, 0), (5, 0.1), (6, 0)]
        zones = [True, True, True, False, False, False, False]
        self.assertEqual(simplifier_par_zones(ligne, zones, 0.01, 1), [(0, 0), (1, 0.1), (2, 0), (3, 0.1), (6, 0)])

    def test_traverser(self):
        # une diagonale à travers le carré [0, 10] × [0, 10] depuis son centre
        s1, s2 = traverser((5, 5), (1, 1), (0, 0, 10, 10))
        self.assertEqual((s1, s2), (-5, 5))
        self.assertEqual(traverser((5, 5), (1, 0), (0, 0, 10, 10)), (-5, 5))
        s1, s2 = traverser((5, 20), (1, 0), (0, 0, 10, 10))              # passe à côté
        self.assertLessEqual(s2, s1)

    def test_sans_bords(self):
        # un carré coupé par le bord y = 10 : le côté posé sur le bord n'est pas une côte
        carre = [(0, 0), (5, 0), (5, 10), (0, 10), (0, 0)]
        self.assertEqual(sans_bords(carre, lambda p: p[1] == 10), [[(0, 0), (5, 0), (5, 10)], [(0, 10), (0, 0)]])


class TestDecoupage(unittest.TestCase):
    def test_boite(self):
        self.assertTrue(dans_boite(0, 0, (-1, -1, 1, 1)))
        self.assertFalse(dans_boite(2, 0, (-1, -1, 1, 1)))

    def test_morceaux_se_raccordent(self):
        ligne = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        dedans = morceaux(ligne, lambda x, y: 1 <= x <= 2)
        dehors = morceaux(ligne, lambda x, y: not 1 <= x <= 2)
        self.assertEqual(dedans, [[(0, 0), (1, 0), (2, 0), (3, 0)]])
        self.assertEqual(dehors, [[(0, 0), (1, 0)], [(2, 0), (3, 0), (4, 0)]])

    def test_etendue(self):
        self.assertEqual(etendue([(0, 0), (3, 1), (1, 4)]), 7)


class TestChemin(unittest.TestCase):
    def test_relatif(self):
        self.assertEqual(chemin([[(0, 0), (10, 0), (10, -5)]]), "M0 0l10 0 0-5")

    def test_ferme_et_doublons(self):
        self.assertEqual(chemin([[(1.2, 1.4), (1.4, 1.2), (3, 3)]], fermer=True), "M1 1l2 2z")

    def test_ignore_les_points_isoles(self):
        self.assertEqual(chemin([[(0, 0)], [(0, 0), (0.2, 0.1)]]), "")


class TestGrille(unittest.TestCase):
    def test_plus_proche(self):
        grille = Grille([[(0, 0), (100, 0)]], 100)
        d, point, segment = grille.plus_proche(50, 30)
        self.assertAlmostEqual(d, 30)
        self.assertEqual(point, (50, 0))
        self.assertEqual(segment, (100, 0))

    def test_trop_loin(self):
        grille = Grille([[(0, 0), (10, 0)]], 100)
        self.assertIsNone(grille.plus_proche(1000, 1000)[1])


class TestEtoile(unittest.TestCase):
    def test_nombre_de_points(self):
        self.assertEqual(len(etoile(4, 10, 2).split()), 8)
        self.assertEqual(etoile(4, 10, 2).split()[0], "0.0,-10.0")   # la première pointe vise le nord


if __name__ == "__main__":
    unittest.main()
