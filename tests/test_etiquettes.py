import unittest

from carte_portulan.etiquettes import BAS, HAUT, Etiquette, Rectangle, largeur, paliers


def nom(x, y, texte="Portus", rang=1, angle=(1, 0)):
    """Étiquette d'un nom écrit depuis (x, y) dans la direction « angle »."""
    return Etiquette(rang, [Rectangle(x, y, *angle, 0, largeur(texte), HAUT, BAS)])


class TestEtiquettes(unittest.TestCase):
    def test_largeur(self):
        self.assertAlmostEqual(largeur("Ab"), 0.73 + 0.51)
        self.assertAlmostEqual(largeur("É"), largeur("E"))          # accent : largeur de la lettre de base
        self.assertGreater(largeur("Москва"), 0)                   # autre alphabet : largeur moyenne

    def test_chevauchement(self):
        a, b = nom(0, 0), nom(0, 200)                              # deux noms l'un au-dessus de l'autre
        self.assertTrue(a.chevauche(b, 300))
        self.assertFalse(a.chevauche(b, 50))
        self.assertFalse(nom(0, 0).chevauche(nom(5000, 0), 300))

    def test_paliers(self):
        seuils = (300, 100, 30)
        etiquettes = [nom(0, 0, "Grand"), nom(0, 150, "Petit", rang=2), nom(0, 60, "Minuscule", rang=2),
                      nom(4000, 0, "Loin", rang=2)]
        p = paliers(etiquettes, seuils)
        self.assertEqual(p[0], 0)                                  # le grand port d'abord
        self.assertEqual(p[3], 0)                                  # seul dans son coin
        self.assertEqual(p[1], 1)                                  # n'a de place qu'en zoomant
        self.assertEqual(p[2], 2)
        # à chaque palier, les noms visibles ne se chevauchent pas
        for i, a in enumerate(etiquettes):
            for j, b in enumerate(etiquettes[:i]):
                if p[i] is not None and p[j] is not None:
                    self.assertFalse(a.chevauche(b, seuils[max(p[i], p[j])]), (i, j))

    def test_petit_nom_ne_chasse_pas_un_grand(self):
        # un petit port prioritaire par l'ordre de la liste ne prend pas la place d'un grand
        p = paliers([nom(0, 60, "Petit", rang=2), nom(0, 0, "Grand")], (300, 30))
        self.assertEqual(p[1], 0)
        self.assertEqual(p[0], 1)

    def test_sans_place(self):
        p = paliers([nom(0, 0, "Un"), nom(0, 0, "Deux")], (300, 30))   # au même endroit : jamais de place
        self.assertEqual(p, [0, None])


if __name__ == "__main__":
    unittest.main()
