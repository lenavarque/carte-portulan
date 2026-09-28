"""Page HTML autonome qui montre une vue de la carte, avec un thème sombre par défaut.

La carte y est incluse telle quelle : la page s'ouvre directement (double-clic), sans serveur. Elle sert d'exemple
des variables CSS à définir pour afficher la carte.
"""
from html import escape

from .projection import UNITES, vue

# Thème sombre de référence : toutes les variables CSS lues par la carte
THEME = """
  --terre-fond: rgba(228, 227, 222, 0.055);
  --terre-trait: rgba(228, 227, 222, 0.34);
  --lac-fond: #111317;
  --nom-1: rgba(216, 87, 60, 0.62);
  --nom-2: rgba(228, 227, 222, 0.3);
  --rhumb-vent: rgba(228, 227, 222, 0.075);
  --rhumb-demi: rgba(111, 159, 122, 0.15);
  --rhumb-quart: rgba(216, 87, 60, 0.13);
  --rose-1: rgba(216, 87, 60, 0.3);
  --rose-2: rgba(217, 170, 69, 0.22);
  --rose-trait: rgba(228, 227, 222, 0.12);
  --grandes-roses: 0.15;
"""


def reglages_vue(largeur_degres: float, largeur_px: float) -> dict[str, str]:
    """Variables qui dépendent de l'échelle : épaisseur d'un pixel, taille des noms, ce qu'on montre ou cache."""
    w = largeur_degres * UNITES
    return {
        "--trait": f"{w / largeur_px:.3f}px",
        "--taille-noms": f"{10.5 * w / largeur_px:.2f}px",
        "--noms-1": "0" if largeur_degres > 150 else "1",
        "--noms-2": "0" if largeur_degres > 40 else "1",
        "--rhumbs-cercles": "0" if largeur_degres > 160 else "1",
    }


def page_apercu(svg: str, lon: float, lat: float, largeur: float, largeur_px: int = 1200, hauteur_px: int = 800) -> str:
    x, y, w, h = vue(lon, lat, largeur, hauteur_px / largeur_px)
    variables = ";".join(f"{k}:{v}" for k, v in reglages_vue(largeur, largeur_px).items())
    titre = escape(f"Carte portulan : {lon}°, {lat}°, {largeur}° de large")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{titre}</title>
<style>
:root {{{THEME}}}
html, body {{ margin: 0; background: #111317; }}
.reserve {{ position: absolute; width: 0; height: 0; overflow: hidden; }}
.carte {{ display: block; width: {largeur_px}px; height: {hauteur_px}px; margin: 24px auto; }}
</style>
</head>
<body>
<div class="reserve">{svg}</div>
<svg class="carte" style="{variables}" viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}" preserveAspectRatio="xMidYMid slice">
  <use href="#rhumbs"/><use href="#roses-noeuds"/><use href="#terres"/><use href="#noms"/><use href="#roses"/>
</svg>
</body>
</html>
"""
