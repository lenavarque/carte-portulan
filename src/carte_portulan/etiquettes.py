"""Placement des noms sans chevauchement, par paliers de zoom.

Les noms gardent la même taille à l'écran (--taille-noms, en unités de la carte) : de loin, ils couvrent une plus
grande partie de la carte qu'en gros plan. Chaque nom reçoit donc un palier : il n'est montré que si la taille des
noms ne dépasse pas le seuil de ce palier (la page règle --noms-p0, --noms-p1… selon la vue). À chaque palier, aucun
nom visible n'en chevauche un autre. En zoomant, chaque étiquette rétrécit vers son point d'ancrage (qu'elle
contient) : deux étiquettes qui ne se chevauchent pas ne se chevaucheront donc pas davantage de plus près.
"""
import math
import unicodedata
from dataclasses import dataclass, field

# Largeur des caractères de Spectral italique, en em, espacement des lettres (.02 em) compris (mesurée dans un
# navigateur). Les autres : selon leur forme de base (sans accent), sinon une valeur moyenne.
LARGEURS = {
    " ": 0.25, "'": 0.27, "’": 0.27, "-": 0.37, "/": 0.30, ".": 0.26, "(": 0.33, ")": 0.33,
    "A": 0.73, "B": 0.65, "C": 0.69, "D": 0.75, "E": 0.64, "F": 0.62, "G": 0.76, "H": 0.79, "I": 0.39, "J": 0.39,
    "K": 0.72, "L": 0.62, "M": 0.94, "N": 0.80, "O": 0.80, "P": 0.64, "Q": 0.80, "R": 0.64, "S": 0.51, "T": 0.67,
    "U": 0.80, "V": 0.72, "W": 0.97, "X": 0.72, "Y": 0.69, "Z": 0.63,
    "a": 0.52, "b": 0.51, "c": 0.45, "d": 0.54, "e": 0.46, "f": 0.34, "g": 0.46, "h": 0.54, "i": 0.31, "j": 0.31,
    "k": 0.49, "l": 0.28, "m": 0.79, "n": 0.55, "o": 0.52, "p": 0.53, "q": 0.49, "r": 0.37, "s": 0.37, "t": 0.33,
    "u": 0.54, "v": 0.44, "w": 0.68, "x": 0.46, "y": 0.47, "z": 0.41,
}
HAUT, BAS = -0.85, 0.3        # hauteur des lettres au-dessus et au-dessous de la ligne de base, en em
MARGE = 0.15                  # espace minimal entre deux étiquettes, en em


def largeur(texte: str) -> float:
    """Largeur approchée d'un nom, en em."""
    total = 0.0
    for c in texte:
        if c not in LARGEURS:
            base = unicodedata.normalize("NFD", c)[0]
            c = base if base in LARGEURS else ("A" if base.isupper() else "a")
        total += LARGEURS[c]
    return total


@dataclass
class Rectangle:
    """Rectangle orienté : ancre (unités de la carte), direction de son axe x, étendue en em de part et d'autre."""
    ox: float
    oy: float
    ux: float
    uy: float
    x0: float
    x1: float
    y0: float
    y1: float

    def coins(self, taille: float) -> list[tuple[float, float]]:
        vx, vy = -self.uy, self.ux
        m = MARGE / 2
        return [(self.ox + taille * (x * self.ux + y * vx), self.oy + taille * (x * self.uy + y * vy))
                for x, y in ((self.x0 - m, self.y0 - m), (self.x1 + m, self.y0 - m),
                             (self.x1 + m, self.y1 + m), (self.x0 - m, self.y1 + m))]

    def portee(self) -> float:
        """Distance maximale d'un point du rectangle à l'ancre, en em."""
        return max(math.hypot(x, y) for x in (self.x0, self.x1) for y in (self.y0, self.y1)) + MARGE


def _separes(a: list, b: list) -> bool:
    """Deux quadrilatères convexes sont disjoints s'il existe un axe (normale d'un côté) qui les sépare."""
    for poly in (a, b):
        for i in range(4):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % 4]
            nx, ny = y1 - y2, x2 - x1
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return True
    return False


@dataclass
class Etiquette:
    """Un nom (et son château éventuel), dans l'ordre de priorité où on les place."""
    rang: int                                   # 1 : grands ports, 2 : les autres
    formes: list[Rectangle] = field(default_factory=list)
    echelle: float = 1.0                        # taille relative (les petits noms sont un peu plus petits)

    def __post_init__(self):
        self.ox, self.oy = self.formes[0].ox, self.formes[0].oy
        self.rayon = max(r.portee() for r in self.formes) * self.echelle

    def chevauche(self, autre: "Etiquette", taille: float) -> bool:
        if math.hypot(self.ox - autre.ox, self.oy - autre.oy) > taille * (self.rayon + autre.rayon):
            return False
        return any(not _separes(a.coins(taille * self.echelle), b.coins(taille * autre.echelle))
                   for a in self.formes for b in autre.formes)


def paliers(etiquettes: list[Etiquette], seuils: tuple[float, ...]) -> list[int | None]:
    """Palier de chaque étiquette (indice dans « seuils », du plus grand au plus petit), ou None si elle ne trouve
    de place à aucun palier. Les grands ports d'abord, à tous les paliers, puis les autres : un petit nom ne prend
    jamais la place d'un grand."""
    palier: list[int | None] = [None] * len(etiquettes)
    places: list[int] = []
    for rang in (1, 2):
        for k, taille in enumerate(seuils):
            for i, e in enumerate(etiquettes):
                if e.rang != rang or palier[i] is not None:
                    continue
                # deux étiquettes sont visibles ensemble à partir du plus petit de leurs deux seuils
                if all(not e.chevauche(etiquettes[j], seuils[max(k, palier[j])]) for j in places):
                    palier[i] = k
                    places.append(i)
    return palier
