import tempfile
import unittest
import zipfile
from pathlib import Path

from carte_portulan.natural_earth import CoucheIntrouvable, Source

from fabrique import ecrire_couche, monde_factice


class TestSource(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dossier = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_dossier(self):
        monde_factice(self.dossier)
        terres = Source(self.dossier).lire("ne_50m_land")
        self.assertEqual(len(terres), 1)
        geometrie, attributs = terres[0]
        self.assertEqual(geometrie[0][0], (5.0, 40.0))
        self.assertEqual(attributs["featurecla"], "Land")

    def test_points_et_champs(self):
        monde_factice(self.dossier)
        villes = Source(self.dossier).lire("ne_10m_populated_places", {"NAME"})
        self.assertEqual(villes[0][0], (5.05, 41.0))
        self.assertEqual(villes[0][1], {"NAME": "Portus"})

    def test_archive_complete(self):
        couches = self.dossier / "couches"
        couches.mkdir()
        monde_factice(couches)
        archive = self.dossier / "natural_earth_vector.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for f in couches.iterdir():
                z.write(f, f"50m_physical/{f.name}")
        self.assertEqual(len(Source(archive).lire("ne_50m_lakes")), 1)

    def test_zip_par_couche(self):
        couches = self.dossier / "couches"
        couches.mkdir()
        monde_factice(couches)
        telechargements = self.dossier / "telechargements"
        telechargements.mkdir()
        with zipfile.ZipFile(telechargements / "ne_50m_land.zip", "w") as z:
            for ext in ("shp", "dbf", "cpg"):
                z.write(couches / f"ne_50m_land.{ext}", f"ne_50m_land.{ext}")
        self.assertEqual(len(Source(telechargements).lire("ne_50m_land")), 1)

    def test_couche_vide(self):
        ecrire_couche(self.dossier, "vide", 3, [], [("a", 1)], [])
        self.assertEqual(Source(self.dossier).lire("vide"), [])

    def test_couche_absente(self):
        with self.assertRaises(CoucheIntrouvable):
            Source(self.dossier).lire("ne_50m_land")

    def test_chemin_absent(self):
        with self.assertRaises(FileNotFoundError):
            Source(self.dossier / "absent.zip")


if __name__ == "__main__":
    unittest.main()
