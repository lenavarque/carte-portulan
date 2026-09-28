"""Réglages de la carte. Les positions et les distances sont en degrés ; tout se change par un fichier JSON
(voir charger_config() et le README)."""
import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path


@dataclass
class Config:
    # Étendue et détail
    lat_min: float = -72.0                                   # la carte s'arrête à ces latitudes
    lat_max: float = 80.0
    boite_detail: tuple[float, float, float, float] = (-16.0, 25.0, 50.0, 62.0)
    """Zone aux côtes détaillées (ouest, sud, est, nord) : Méditerranée et Europe par défaut."""
    tolerance_detail: float = 0.009                          # simplification des côtes, en degrés
    tolerance_monde: float = 0.026
    taille_min_terre: float = 0.12                           # îles plus petites ignorées (largeur + hauteur, degrés)
    taille_min_cote: float = 0.10
    rang_max_lacs: float = 1                                 # « scalerank » des lacs gardés (0 = les plus grands)

    # Noms des ports
    champ_nom: str = "NAME_FR"                               # champ de Natural Earth pour le nom (sinon NAME)
    rang_max_ports_detail: int = 7                           # « SCALERANK » des villes gardées dans la zone détaillée…
    rang_max_ports_monde: int = 3                            # … et ailleurs (les capitales le sont toujours)
    rang_max_grands_ports: int = 2                           # écrits en rouge (avec les capitales)
    distance_cote_detail: float = 0.20                       # distance maximale à la côte, en degrés
    distance_cote_monde: float = 0.35
    ecart_grands_ports: float = 0.75                         # écart minimal entre deux noms le long de la côte
    ecart_petits_ports: float = 0.26
    decalage_nom: float = 0.06                               # le nom commence un peu à l'intérieur des terres

    # Réseaux de rhumbs : (longitude, latitude, rayon du cercle des 16 roses), en degrés
    systemes: list[tuple[float, float, float]] = field(default_factory=lambda: [
        (17, 38, 15), (-21, 40, 15), (56, 38, 15), (98, 42, 17), (136, 28, 17), (-78, 22, 18),
        (-26, -18, 17), (62, -12, 17), (-135, -32, 18), (158, -28, 17), (-150, 30, 18)])
    portee: float = 2.6                                      # longueur des lignes de part et d'autre, en rayons

    # Grandes roses ornées : (longitude, latitude, taille : rayon en degrés)
    grandes_roses: list[tuple[float, float, float]] = field(default_factory=lambda: [
        (-38, 31, 4.2), (74, -14, 4.8), (-160, 12, 5.0), (-44, -36, 4.2), (170, -40, 4.6), (-12, 5, 3.6)])

    # Couches Natural Earth utilisées
    couche_terres: str = "ne_50m_land"
    couche_cotes_detail: str = "ne_10m_coastline"
    couche_cotes_monde: str = "ne_50m_coastline"
    couche_lacs: str = "ne_50m_lakes"
    couche_villes: str = "ne_10m_populated_places"

    def en_dict(self) -> dict:
        return asdict(self)


def charger_config(chemin: str | Path | None) -> Config:
    """Réglages par défaut, remplacés par ceux du fichier JSON (clés de Config ; les autres sont refusées)."""
    if chemin is None:
        return Config()
    donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
    connus = {f.name for f in fields(Config)}
    inconnus = set(donnees) - connus
    if inconnus:
        raise ValueError(f"Réglages inconnus dans {chemin} : {', '.join(sorted(inconnus))}")
    for cle in ("boite_detail",):
        if cle in donnees:
            donnees[cle] = tuple(donnees[cle])
    for cle in ("systemes", "grandes_roses"):
        if cle in donnees:
            donnees[cle] = [tuple(v) for v in donnees[cle]]
    return Config(**donnees)
