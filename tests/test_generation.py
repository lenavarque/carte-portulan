import contextlib
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from carte_portulan import Config, Source, charger_config, generer, rose_ornee, rose_ornee_autonome
from carte_portulan.cli import main

from fabrique import monde_factice

SVG = "{http://www.w3.org/2000/svg}"


class TestGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dossier = Path(cls._tmp.name)
        monde_factice(cls.dossier)
        cls.carte = generer(Source(cls.dossier), Config())
        cls.racine = ET.fromstring(cls.carte.svg)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def groupe(self, identifiant):
        return self.racine.find(f".//*[@id='{identifiant}']")

    def test_groupes(self):
        for identifiant in ("terres", "noms", "villes", "rhumbs", "roses-noeuds", "roses", "rose-centrale", "petite-rose", "rose-ornee",
                           "chateau"):
            self.assertIsNotNone(self.groupe(identifiant), identifiant)

    def test_rose_centrale(self):
        self.assertEqual(len(self.groupe("rose-centrale")), 1)
        sans = ET.fromstring(generer(Source(self.dossier), Config(rose_centrale=None)).svg)
        self.assertEqual(len(sans.find(".//*[@id='rose-centrale']")), 0)

    def test_noms_des_ports(self):
        textes = [t.text for t in self.groupe("noms").iter(f"{SVG}text")]
        self.assertIn("Port-Royal", textes)                  # nom français quand il existe
        self.assertIn("Caleta & Mar", textes)                # sinon le nom d'origine, correctement échappé
        self.assertNotIn("Loin", textes)                     # trop loin de toute côte
        self.assertEqual(self.carte.nombre_noms, (1, 1))

    def test_villes(self):
        self.assertEqual(self.carte.nombre_villes, 1)             # le grand port de la zone détaillée
        self.assertEqual(len(self.groupe("villes")), 1)
        sans = generer(Source(self.dossier), Config(chateaux=False))
        self.assertEqual(sans.nombre_villes, 0)

    def test_meme_carte_a_chaque_fois(self):
        self.assertEqual(generer(Source(self.dossier), Config()).svg, self.carte.svg)
        autre = generer(Source(self.dossier), Config(graine=7)).svg
        self.assertNotEqual(autre, self.carte.svg)                # la graine change le tracé des rhumbs

    def test_terres(self):
        chemins = [p.get("d") for p in self.groupe("terres").iter(f"{SVG}path")]
        self.assertTrue(all(chemins))
        # un tracé par case (terres, lacs, côtes), ou un seul de chaque sans découpage
        self.assertEqual(len(self.groupe("terres")), 3)
        sans = ET.fromstring(generer(Source(self.dossier), Config(case_terres=0)).svg).find(".//*[@id='terres']")
        self.assertEqual(len(list(sans.iter(f"{SVG}path"))), 3)

    def test_cotes_sur_les_terres(self):
        # le trait des côtes suit exactement le bord du remplissage : mêmes points
        import re
        remplissage, _, trait = list(self.groupe("terres"))
        def points(groupe):
            res = set()
            for p in groupe.iter(f"{SVG}path"):
                for sous in re.findall(r"M[^M]+", p.get("d")):
                    nombres = list(map(int, re.findall(r"-?\d+", sous)))
                    x, y = nombres[0], nombres[1]
                    res.add((x, y))
                    for dx, dy in zip(nombres[2::2], nombres[3::2]):
                        x, y = x + dx, y + dy
                        res.add((x, y))
            return res
        self.assertTrue(points(trait))
        self.assertEqual(points(trait), points(remplissage))

    def test_paliers_et_vents(self):
        # la page montre ou cache chaque nom par « display » (un nom caché n'est pas mis en page) : son palier, et
        # --petits-noms pour les autres ports ; de même les châteaux et les noms des vents
        styles = {t.text: t.get("style") for t in self.groupe("noms").iter(f"{SVG}text")}
        self.assertRegex(styles["Port-Royal"], r"^display:var\(--noms-p\d,inline\)$")
        self.assertRegex(styles["Caleta & Mar"], r"^display:var\(--petits-noms,var\(--noms-p\d,inline\)\)$")
        self.assertTrue(all(u.get("style", "").startswith("display:var(--noms-p") for u in self.groupe("villes")))
        vents = [t.get("style") for t in ET.fromstring(rose_ornee_autonome()).iter(f"{SVG}text")]
        self.assertEqual(set(vents), {"display:var(--vents,inline)"})

    def test_bornes(self):
        ouest, nord, est, sud = self.carte.index()["bornes"]
        self.assertEqual((ouest, est), (-18000, 18000))
        self.assertLess(nord, 0)                                  # y vers le bas : le nord est négatif
        self.assertGreater(sud, 0)

    def test_rhumbs_sans_doublon(self):
        """Chaque droite n'est tracée qu'une fois : aucune paire presque confondue (même direction, même place)."""
        import math
        import re
        segments = [tuple(map(float, m)) for p in self.groupe("rhumbs").iter(f"{SVG}path")
                    for m in re.findall(r"M(-?\d+) (-?\d+)L(-?\d+) (-?\d+)", p.get("d"))]
        self.assertGreater(len(segments), 100)

        def confondues(a, b):
            ax, ay, bx, by = a
            cx, cy, dx, dy = b
            l = math.hypot(bx - ax, by - ay)
            ux, uy = (bx - ax) / l, (by - ay) / l
            ecart = max(abs((cx - ax) * uy - (cy - ay) * ux), abs((dx - ax) * uy - (dy - ay) * ux))
            t = sorted(((cx - ax) * ux + (cy - ay) * uy, (dx - ax) * ux + (dy - ay) * uy))
            return ecart < 20 and min(l, t[1]) - max(0, t[0]) > 300

        doublons = [(a, b) for i, a in enumerate(segments) for b in segments[:i] if confondues(a, b)]
        self.assertEqual(doublons, [])

    def test_une_droite_par_corde(self):
        # un seul réseau, toutes les droites : 16 pour la rose centrale, 48 cordes et 16 tangentes pour le cercle
        carte = generer(Source(self.dossier), Config(systemes=[(0, 0, 20)], lignes_manquantes=0))
        rhumbs = ET.fromstring(carte.svg).find(".//*[@id='rhumbs']")
        self.assertEqual(sum(p.get("d").count("M") for p in rhumbs.iter(f"{SVG}path")), 16 + 48 + 16)

    def test_reseaux(self):
        systemes = len(Config().systemes)
        # rose centrale + une sur deux du cercle, et une rose là où les deux cercles de Cantino se touchent
        self.assertEqual(len(self.carte.noeuds), systemes * 9 + 1)
        self.assertEqual(sum(n["centre"] for n in self.carte.noeuds), systemes + 1)
        self.assertEqual(self.carte.index()["k"], 100)

    def test_droites_d_un_bord_a_l_autre(self):
        import re
        ouest, nord, est, sud = self.carte.index()["bornes"]
        bord = lambda x, y: min(abs(x - ouest), abs(x - est), abs(y - nord), abs(y - sud)) <= 1
        segments = [tuple(map(float, m)) for p in self.groupe("rhumbs").iter(f"{SVG}path")
                    for m in re.findall(r"M(-?\d+) (-?\d+)L(-?\d+) (-?\d+)", p.get("d"))]
        self.assertTrue(segments)
        self.assertTrue(all(bord(x1, y1) and bord(x2, y2) for x1, y1, x2, y2 in segments))
        # avec une portée, des segments, qui s'arrêtent avant les bords
        courts = ET.fromstring(generer(Source(self.dossier), Config(portee=1.0)).svg).find(".//*[@id='rhumbs']")
        coupes = [tuple(map(float, m)) for p in courts.iter(f"{SVG}path")
                  for m in re.findall(r"M(-?\d+) (-?\d+)L(-?\d+) (-?\d+)", p.get("d"))]
        self.assertFalse(all(bord(x1, y1) and bord(x2, y2) for x1, y1, x2, y2 in coupes))

    def test_rose(self):
        self.assertTrue(rose_ornee().startswith('<g id="rose-ornee">'))
        self.assertTrue(rose_ornee(None).startswith("<g>"))
        textes = [t.text for t in ET.fromstring(rose_ornee_autonome()).iter(f"{SVG}text")]
        self.assertEqual(textes[0], "Tramontana")
        self.assertEqual(len(textes), 8)


class TestConfig(unittest.TestCase):
    def test_fichier(self):
        with tempfile.TemporaryDirectory() as tmp:
            chemin = Path(tmp) / "reglages.json"
            chemin.write_text(json.dumps({"systemes": [[0, 0, 10]], "portee": 1.5}), encoding="utf-8")
            config = charger_config(chemin)
            self.assertEqual(config.systemes, [(0, 0, 10)])
            self.assertEqual(config.portee, 1.5)

    def test_cle_inconnue(self):
        with tempfile.TemporaryDirectory() as tmp:
            chemin = Path(tmp) / "reglages.json"
            chemin.write_text('{"inconnue": 1}', encoding="utf-8")
            with self.assertRaises(ValueError):
                charger_config(chemin)


class TestLigneDeCommande(unittest.TestCase):
    def test_sorties(self):
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp)
            (dossier / "ne").mkdir()
            monde_factice(dossier / "ne")
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--natural-earth", str(dossier / "ne"), "--sortie", str(dossier / "sortie"),
                             "--apercu", "6,41,10"])
            self.assertEqual(code, 0)
            for nom in ("portulan.svg", "portulan.json", "rose-ornee.svg", "apercu.html"):
                self.assertTrue((dossier / "sortie" / nom).exists(), nom)


if __name__ == "__main__":
    unittest.main()
