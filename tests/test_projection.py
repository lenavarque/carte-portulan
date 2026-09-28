import math
import unittest

from carte_portulan.projection import LAT_MAX, UNITES, mercator, projeter, vue


class TestProjection(unittest.TestCase):
    def test_equateur(self):
        self.assertAlmostEqual(mercator(0), 0)
        x, y = projeter(0, 0)
        self.assertEqual(x, 0)
        self.assertAlmostEqual(y, 0)

    def test_sens(self):
        # le nord est en haut : y diminue quand la latitude augmente
        self.assertLess(projeter(0, 45)[1], projeter(0, 10)[1])
        self.assertAlmostEqual(mercator(30), -mercator(-30))

    def test_longitude(self):
        self.assertEqual(projeter(12.5, 0)[0], 12.5 * UNITES)

    def test_bornes(self):
        self.assertEqual(mercator(89.9), mercator(LAT_MAX))
        self.assertTrue(math.isfinite(mercator(90)))

    def test_vue(self):
        x, y, w, h = vue(10, 0, 20, 0.5)
        self.assertEqual((x + w / 2, w, h), (10 * UNITES, 20 * UNITES, 10 * UNITES))
        self.assertAlmostEqual(y + h / 2, 0)


if __name__ == "__main__":
    unittest.main()
