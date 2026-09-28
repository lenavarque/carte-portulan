"""Projection de Mercator, en centièmes de degré.

Sur une carte de Mercator, une route à cap constant (loxodromie, ou ligne de rhumb) est une droite, comme sur les
portulans. Les coordonnées de la carte sont :

    x = longitude × 100
    y = −Mercator(latitude) × 100   (l'axe des y est tourné vers le bas, comme en SVG)

où Mercator(latitude) est exprimé en « degrés équivalents » : un degré de longitude à l'équateur vaut 100 unités.
"""
import math

UNITES = 100                     # unités de la carte par degré de longitude
LAT_MIN, LAT_MAX = -72.0, 80.0   # au-delà, Mercator s'étire à l'infini : on arrête la carte


def mercator(lat: float, lat_min: float = LAT_MIN, lat_max: float = LAT_MAX) -> float:
    """Ordonnée de Mercator (en degrés équivalents, vers le bas) d'une latitude, bornée à [lat_min, lat_max]."""
    lat = max(lat_min, min(lat_max, lat))
    return -math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 180 / math.pi


def projeter(lon: float, lat: float, lat_min: float = LAT_MIN, lat_max: float = LAT_MAX) -> tuple[float, float]:
    """(longitude, latitude) en degrés → (x, y) en unités de la carte."""
    return lon * UNITES, mercator(lat, lat_min, lat_max) * UNITES


def vue(lon: float, lat: float, largeur: float, rapport: float) -> tuple[float, float, float, float]:
    """viewBox SVG (x, y, largeur, hauteur) centrée sur (lon, lat), large de « largeur » degrés,
    pour une fenêtre dont hauteur / largeur = rapport."""
    x, y = projeter(lon, lat)
    w = largeur * UNITES
    h = w * rapport
    return x - w / 2, y - h / 2, w, h
