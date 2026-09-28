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

    def test_reseaux(self):
        systemes = len(Config().systemes)
        self.assertEqual(len(self.carte.noeuds), systemes * 9)  # rose centrale + une sur deux du cercle
        self.assertEqual(sum(n["centre"] for n in self.carte.noeuds), systemes)
        self.assertEqual(self.carte.index()["k"], 100)

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
