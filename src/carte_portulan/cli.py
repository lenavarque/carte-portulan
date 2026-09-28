"""Ligne de commande : carte-portulan (ou python -m carte_portulan)."""
import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .apercu import page_apercu
from .config import charger_config
from .generation import generer
from .natural_earth import CoucheIntrouvable, Source
from .rose import rose_ornee_autonome

EMPLACEMENTS = ("natural_earth_vector.zip", "donnees/natural_earth_vector.zip", "donnees")


def trouver_natural_earth(demande: str | None) -> Path:
    """Chemin donné, sinon variable d'environnement NATURAL_EARTH, sinon emplacements habituels."""
    for candidat in (demande, os.environ.get("NATURAL_EARTH"), *EMPLACEMENTS):
        if candidat and Path(candidat).exists():
            return Path(candidat)
    raise SystemExit("Natural Earth introuvable. Téléchargez l'archive (voir le README) puis indiquez-la avec "
                     "--natural-earth CHEMIN ou la variable NATURAL_EARTH.")


def vue(texte: str) -> tuple[float, float, float]:
    try:
        lon, lat, largeur = (float(v) for v in texte.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("attendu : LONGITUDE,LATITUDE,LARGEUR (en degrés), par exemple 16,38,44")
    return lon, lat, largeur


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="carte-portulan",
        description="Dessine une carte du monde à la manière des portulans (SVG), d'après Natural Earth.")
    parser.add_argument("--natural-earth", metavar="CHEMIN",
                        help="archive natural_earth_vector.zip, ou dossier contenant les couches")
    parser.add_argument("--config", metavar="FICHIER", help="réglages en JSON (voir le README)")
    parser.add_argument("--sortie", metavar="DOSSIER", default="sortie", help="dossier de sortie (défaut : sortie)")
    parser.add_argument("--apercu", metavar="LON,LAT,LARGEUR", type=vue, default=(16, 38, 44),
                        help="vue de la page d'aperçu, en degrés (défaut : 16,38,44, la Méditerranée)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(arguments)

    config = charger_config(args.config)
    source = Source(trouver_natural_earth(args.natural_earth))
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    try:
        carte = generer(source, config, journal=lambda m: print(m, flush=True))
    except CoucheIntrouvable as erreur:
        print(erreur, file=sys.stderr)
        return 1
    (sortie / "portulan.svg").write_text(carte.svg, encoding="utf-8")
    (sortie / "portulan.json").write_text(json.dumps(carte.index(), separators=(",", ":")), encoding="utf-8")
    (sortie / "rose-ornee.svg").write_text(rose_ornee_autonome(), encoding="utf-8")
    (sortie / "apercu.html").write_text(page_apercu(carte.svg, *args.apercu, paliers=carte.paliers), encoding="utf-8")
    taille = (sortie / "portulan.svg").stat().st_size // 1024
    print(f"{sortie / 'portulan.svg'} : {taille} Ko, {carte.nombre_noms[0]} grands ports et "
          f"{carte.nombre_noms[1]} autres, {len(carte.noeuds)} roses du réseau.")
    print(f"Aperçu : {sortie / 'apercu.html'}")
    return 0
