"""Outils géométriques : simplification des lignes, découpage, rangement par cases, index spatial, chemins SVG
compacts."""
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


def simplifier_par_zones(points: Sequence[Point], zones: Sequence[bool], tol_vrai: float, tol_faux: float) -> list[Point]:
    """Simplifie une ligne morceau par morceau, avec la tolérance de la zone de chaque morceau (zones[i] : le point i
    est-il dans la zone « vraie » ?). Le point où la zone change termine un morceau et commence le suivant : les
    morceaux se raccordent exactement."""
    if not points:
        return []
    res = [points[0]]
    debut = 0
    for i in range(1, len(points) + 1):
        if i == len(points) or zones[i] != zones[debut]:
            fin = min(i, len(points) - 1)
            res += simplifier(points[debut:fin + 1], tol_vrai if zones[debut] else tol_faux)[1:]
            debut = fin
    return res


def sans_bords(anneau: Sequence[Point], sur_bord: Callable[[Point], bool]) -> list[list[Point]]:
    """Le contour d'un polygone en lignes, sans ses côtés posés sur le bord de la carte (les deux extrémités sur le
    bord) : là où la carte coupe une terre (Antarctique, ±180°), il n'y a pas de côte à tracer."""
    lignes: list[list[Point]] = []
    courant: list[Point] = [anneau[0]] if anneau else []
    for a, b in zip(anneau, anneau[1:]):
        if sur_bord(a) and sur_bord(b):
            if len(courant) > 1:
                lignes.append(courant)
            courant = [b]
        else:
            courant.append(b)
    if len(courant) > 1:
        lignes.append(courant)
    return lignes


def traverser(p: Point, u: Point, boite: Sequence[float]) -> tuple[float, float]:
    """(s1, s2) tels que la droite p + s·u traverse la boîte (x0, y0, x1, y1) de p + s1·u à p + s2·u
    (algorithme de Liang-Barsky) ; s2 <= s1 si elle la manque."""
    s1, s2 = -math.inf, math.inf
    for q, v, bas, haut in ((p[0], u[0], boite[0], boite[2]), (p[1], u[1], boite[1], boite[3])):
        if abs(v) < 1e-12:
            if not bas <= q <= haut:
                return 0.0, 0.0
            continue
        a, b = (bas - q) / v, (haut - q) / v
        s1, s2 = max(s1, min(a, b)), min(s2, max(a, b))
    return s1, s2


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


def couper_rectangle(anneau: Sequence[Point], x0: float, y0: float, x1: float, y1: float) -> list[Point]:
    """Partie d'un polygone fermé comprise dans le rectangle [x0, x1] × [y0, y1] (algorithme de Sutherland-Hodgman).
    D'un polygone concave, il peut rester des arêtes de largeur nulle le long du bord : sans effet sur un
    remplissage, mais à ne pas tracer."""
    poly = list(anneau[:-1] if len(anneau) > 1 and anneau[0] == anneau[-1] else anneau)

    def couper(poly, dedans, croisement):
        sortie = []
        for i, b in enumerate(poly):
            a = poly[i - 1]
            if dedans(b):
                if not dedans(a):
                    sortie.append(croisement(a, b))
                sortie.append(b)
            elif dedans(a):
                sortie.append(croisement(a, b))
        return sortie

    def en_x(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def en_y(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)

    for dedans, croisement in ((lambda p: p[0] >= x0, en_x(x0)), (lambda p: p[0] <= x1, en_x(x1)),
                               (lambda p: p[1] >= y0, en_y(y0)), (lambda p: p[1] <= y1, en_y(y1))):
        if not poly:
            break
        poly = couper(poly, dedans, croisement)
    return poly


def par_cases(lignes: Iterable[Sequence[Point]], taille: float, mode: str) -> dict[tuple[int, int], list[list[Point]]]:
    """Range des lignes par cases carrées de côté « taille ». Le navigateur ne redessine alors que les cases visibles,
    au lieu de parcourir toute la carte pour chaque morceau d'écran. Trois façons de faire :
    - « decouper » : des polygones, coupés au bord des cases (pour un remplissage sans contour) ;
    - « couper » : des lignes, coupées en morceaux ; le segment qui franchit un bord reste au morceau qu'il quitte,
      et le suivant repart de son extrémité : rien n'est tracé deux fois ;
    - « entier » : des polygones, chacun rangé entier dans la case du centre de sa boîte (petits, et tracés)."""
    def case(x: float, y: float) -> tuple[int, int]:
        return math.floor(x / taille), math.floor(y / taille)

    cases: dict[tuple[int, int], list[list[Point]]] = {}
    for pts in lignes:
        if len(pts) < 2:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        (cx0, cy0), (cx1, cy1) = case(min(xs), min(ys)), case(max(xs), max(ys))
        if mode == "entier" or (cx0, cy0) == (cx1, cy1):
            k = (cx0, cy0) if mode != "entier" else case((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            cases.setdefault(k, []).append(list(pts))
        elif mode == "decouper":
            for i in range(cx0, cx1 + 1):
                for j in range(cy0, cy1 + 1):
                    morceau = couper_rectangle(pts, i * taille, j * taille, (i + 1) * taille, (j + 1) * taille)
                    if len(morceau) >= 3:
                        cases.setdefault((i, j), []).append(morceau)
        else:
            courant, k = [pts[0]], case(*pts[0])
            for p in pts[1:]:
                courant.append(p)
                suivante = case(*p)
                if suivante != k:
                    cases.setdefault(k, []).append(courant)
                    courant, k = [p], suivante
            if len(courant) > 1:
                cases.setdefault(k, []).append(courant)
    return cases


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
