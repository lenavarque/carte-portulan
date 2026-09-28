"""Carte portulan : une carte du monde à la manière des portulans, dessinée en SVG d'après Natural Earth.

Utilisation depuis Python :

    from carte_portulan import Config, Source, generer
    carte = generer(Source("natural_earth_vector.zip"), Config())
    open("portulan.svg", "w", encoding="utf-8").write(carte.svg)
"""
from .config import Config, charger_config
from .generation import Carte, generer
from .natural_earth import Source
from .rose import rose_ornee, rose_ornee_autonome

__version__ = "0.1.0"
__all__ = ["Carte", "Config", "Source", "charger_config", "generer", "rose_ornee", "rose_ornee_autonome", "__version__"]
