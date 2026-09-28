import unittest

from carte_portulan.geometrie import Grille, chemin, dans_boite, etendue, etoile, morceaux, simplifier


class TestSimplifier(unittest.TestCase):
    def test_points_alignes(self):
        ligne = [(0, 0), (1, 0.001), (2, 0), (3, 0)]
        self.assertEqual(simplifier(ligne, 0.1), [(0, 0), (3, 0)])

    def test_garde_les_ecarts(self):
        ligne = [(0, 0), (1, 5), (2, 0)]
        self.assertEqual(simplifier(ligne, 1), ligne)

    def test_courte(self):
        self.assertEqual(simplifier([(0, 0), (1, 1)], 10), [(0, 0), (1, 1)])


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
