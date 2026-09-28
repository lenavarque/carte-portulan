"""Outils géométriques : simplification des lignes, découpage, index spatial, chemins SVG compacts."""
import math
from collections.abc import Callable, Iterable, Sequence

Point = tuple[float, float]


def simplifier(points: Sequence[Point], tolerance: float) -> list[Point]:
    """Simplification de Douglas-Peucker (version itérative) : garde les points qui s'écartent de plus de
    « tolerance » de la ligne simplifiée. Le premier et le dernier point sont toujours gardés."""
    if len(points) < 3:
        return list(points)
    garder = [False] * len(points)
    garder[0] = garder[-1] = True
    pile = [(0, len(points) - 1)]
    while pile:
        a, b = pile.pop()
        (x1, y1), (x2, y2) = points[a], points[b]
        dx, dy = x2 - x1, y2 - y1
        long2 = dx * dx + dy * dy
        pire, ipire = -1.0, -1
        for i in range(a + 1, b):
            x, y = points[i]
            if long2:
                t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / long2))
                d = (x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2
            else:
                d = (x - x1) ** 2 + (y - y1) ** 2
            if d > pire:
                pire, ipire = d, i
        if pire > tolerance * tolerance:
            garder[ipire] = True
            pile += [(a, ipire), (ipire, b)]
    return [p for p, g in zip(points, garder) if g]


def dans_boite(lon: float, lat: float, boite: Sequence[float]) -> bool:
    """La boîte est (longitude ouest, latitude sud, longitude est, latitude nord)."""
    return boite[0] <= lon <= boite[2] and boite[1] <= lat <= boite[3]


def morceaux(ligne: Sequence[Point], garder: Callable[[float, float], bool]) -> list[list[Point]]:
    """Coupe une ligne en morceaux dont les points vérifient garder(x, y). Chaque morceau reprend le point
    voisin de part et d'autre, pour que deux morceaux complémentaires se raccordent sans trou."""
    res: list[list[Point]] = []
    courant: list[Point] = []
    for i, p in enumerate(ligne):
        if garder(*p):
            if not courant and i > 0:
                courant.append(ligne[i - 1])
            courant.append(p)
        elif courant:
            courant.append(p)
            res.append(courant)
            courant = []
    if len(courant) > 1:
        res.append(courant)
    return res


def etendue(points: Sequence[Point]) -> float:
    """Largeur + hauteur de la boîte englobante : mesure rapide de la taille d'une ligne."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


def chemin(lignes: Iterable[Sequence[Point]], fermer: bool = False) -> str:
    """Chemin SVG compact : premier point en absolu, puis déplacements relatifs arrondis à l'unité."""
    sortie = []
    for pts in lignes:
        if len(pts) < 2:
            continue
        x0, y0 = round(pts[0][0]), round(pts[0][1])
        px, py = x0, y0
        relatifs = []
        for x, y in pts[1:]:
            x, y = round(x), round(y)
            if (x, y) != (px, py):
                relatifs.append(f"{x - px} {y - py}")
                px, py = x, y
        if not relatifs:
            continue
        sortie.append(f"M{x0} {y0}l" + " ".join(relatifs).replace(" -", "-") + ("z" if fermer else ""))
    return "".join(sortie)


class Grille:
    """Index spatial de segments : pour trouver vite le segment le plus proche d'un point."""

    def __init__(self, lignes: Iterable[Sequence[Point]], taille: float):
        self.taille = taille
        self.cases: dict[tuple[int, int], list[tuple[Point, Point]]] = {}
        for pts in lignes:
            for a, b in zip(pts, pts[1:]):
                for c in {self.case(*a), self.case(*b)}:
                    self.cases.setdefault(c, []).append((a, b))

    def case(self, x: float, y: float) -> tuple[int, int]:
        return int(x // self.taille), int(y // self.taille)

    def plus_proche(self, x: float, y: float, rayon: int = 1) -> tuple[float, Point | None, Point | None]:
        """(distance, point le plus proche, vecteur du segment) parmi les cases voisines, ou (∞, None, None)."""
        cx, cy = self.case(x, y)
        meilleur: tuple[float, Point | None, Point | None] = (math.inf, None, None)
        for i in range(cx - rayon, cx + rayon + 1):
            for j in range(cy - rayon, cy + rayon + 1):
                for (x1, y1), (x2, y2) in self.cases.get((i, j), ()):
                    dx, dy = x2 - x1, y2 - y1
                    l2 = dx * dx + dy * dy or 1e-9
                    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / l2))
                    px, py = x1 + t * dx, y1 + t * dy
                    d = math.hypot(x - px, y - py)
                    if d < meilleur[0]:
                        meilleur = (d, (px, py), (dx, dy))
        return meilleur


def etoile(branches: int, grand: float, petit: float, rotation: float = 0.0, decimales: int = 1) -> str:
    """Points d'une étoile à « branches » branches (attribut points d'un <polygon>), pointe vers le haut."""
    pts = []
    for i in range(branches * 2):
        a = math.radians(rotation + i * 180 / branches - 90)
        r = grand if i % 2 == 0 else petit
        pts.append(f"{r * math.cos(a):.{decimales}f},{r * math.sin(a):.{decimales}f}")
    return " ".join(pts)
