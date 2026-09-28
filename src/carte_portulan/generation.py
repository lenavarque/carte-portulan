"""Assemblage de la carte : terres, côtes, lacs, noms des ports, réseaux de rhumbs et roses.

Le SVG produit n'a pas de viewBox : il sert de réserve de groupes, à afficher avec <use> (voir le README).
Groupes : « terres », « noms », « villes », « rhumbs », « roses-noeuds », « roses », « rose-centrale ». Les couleurs et
les épaisseurs viennent de variables CSS, héritées à travers <use> : la page qui affiche la carte les choisit. Noms et
châteaux sont rangés par paliers de zoom (voir etiquettes.py).
"""
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from html import escape

from .config import Config
from .etiquettes import BAS, HAUT, Etiquette, Rectangle, largeur, paliers
from .geometrie import Grille, chemin, dans_boite, etendue, etoile, morceaux, simplifier
from .natural_earth import Source
from .projection import UNITES
from .projection import projeter as _projeter
from .rose import rose_ornee


TAILLE_PETITS_NOMS = 0.86         # les autres ports, un peu plus petits que les grands


@dataclass
class Carte:
    svg: str                        # le document SVG
    noeuds: list[dict]              # roses du réseau : x, y (unités de la carte), s (réseau), centre (bool)
    nombre_noms: tuple[int, int]    # (grands ports, autres ports)
    nombre_villes: int = 0          # châteaux dessinés
    paliers: tuple[float, ...] = () # seuils des paliers des noms (--noms-p0, --noms-p1…)

    def index(self) -> dict:
        """Données annexes, à écrire en JSON à côté du SVG."""
        return {"k": UNITES, "paliers": list(self.paliers), "noeuds": self.noeuds}


class _Dessin:
    def __init__(self, source: Source, config: Config):
        self.source, self.c = source, config

    def u(self, degres: float) -> float:
        """Degrés → unités de la carte."""
        return degres * UNITES

    def projeter(self, lon: float, lat: float) -> tuple[float, float]:
        return _projeter(lon, lat, self.c.lat_min, self.c.lat_max)

    # ─── Terres, côtes, lacs ───

    def terres(self) -> str:
        anneaux = []
        for geo, _ in self.source.lire(self.c.couche_terres, set()):
            for anneau in geo or []:
                pts = simplifier([self.projeter(*p) for p in anneau], self.u(self.c.tolerance_monde))
                if len(pts) >= 4 and etendue(pts) > self.u(self.c.taille_min_terre):
                    anneaux.append(pts)
        return chemin(anneaux, fermer=True)

    def cotes(self) -> tuple[str, list]:
        """Côtes détaillées dans la boîte de détail, moyennes ailleurs. Renvoie (chemin, lignes projetées)."""
        boite = self.c.boite_detail
        lignes = []
        for geo, _ in self.source.lire(self.c.couche_cotes_detail, set()):
            for ligne in geo or []:
                for m in morceaux(ligne, lambda lon, lat: dans_boite(lon, lat, boite)):
                    pts = simplifier([self.projeter(*p) for p in m], self.u(self.c.tolerance_detail))
                    if len(pts) > 2 or math.dist(pts[0], pts[-1]) > self.u(0.04):
                        lignes.append(pts)
        for geo, _ in self.source.lire(self.c.couche_cotes_monde, set()):
            for ligne in geo or []:
                for m in morceaux(ligne, lambda lon, lat: not dans_boite(lon, lat, boite)):
                    pts = simplifier([self.projeter(*p) for p in m], self.u(self.c.tolerance_monde))
                    if etendue(pts) > self.u(self.c.taille_min_cote):
                        lignes.append(pts)
        return chemin(lignes), lignes

    def lacs(self) -> str:
        anneaux = []
        for geo, att in self.source.lire(self.c.couche_lacs, {"scalerank"}):
            if geo and float(att.get("scalerank") or 9) <= self.c.rang_max_lacs:
                for anneau in geo:
                    anneaux.append(simplifier([self.projeter(*p) for p in anneau], self.u(self.c.tolerance_monde)))
        return chemin(anneaux, fermer=True)

    # ─── Noms des ports : perpendiculaires à la côte, écrits vers l'intérieur des terres ───

    def noms(self, lignes_cotes: list) -> tuple[dict, dict]:
        """Noms et châteaux, rangés par (importance, palier). Les noms sont placés sans chevauchement (etiquettes.py)."""
        c = self.c
        grille = Grille(lignes_cotes, self.u(1))
        champs = {"SCALERANK", "NAME", c.champ_nom, "ADM0CAP", "LATITUDE", "LONGITUDE", "POP_MAX"}
        candidats = []
        for _, a in self.source.lire(c.couche_villes, champs):
            lon, lat = float(a["LONGITUDE"]), float(a["LATITUDE"])
            rang = int(float(a["SCALERANK"] or 10))
            capitale = a["ADM0CAP"].startswith("1")
            detail = dans_boite(lon, lat, c.boite_detail)
            if not (rang <= (c.rang_max_ports_detail if detail else c.rang_max_ports_monde) or capitale):
                continue
            if not (c.lat_min < lat < c.lat_max):
                continue
            x, y = self.projeter(lon, lat)
            d, point, seg = grille.plus_proche(x, y)
            if point is None or d > self.u(c.distance_cote_detail if detail else c.distance_cote_monde):
                continue
            rang_nom = 1 if (rang <= c.rang_max_grands_ports or capitale) else 2
            nom = a.get(c.champ_nom) or a["NAME"]
            candidats.append((rang_nom, rang, -float(a["POP_MAX"] or 0), nom, (x, y), point, seg, d, detail))
        candidats.sort()
        # le château (h em de haut, proportions du dessin) entre la côte et le nom, qui commence après lui
        h = c.taille_chateau
        l_chateau = h * 20 / 33
        places, retenus = [], []
        for rang_nom, _, _, nom, ville, cote, seg, d, detail in candidats:
            ecart = self.u(c.ecart_grands_ports if rang_nom == 1 else c.ecart_petits_ports)
            if any(math.dist(cote, p) < max(ecart, e) for p, e in places):
                continue
            places.append((cote, ecart))
            if d > self.u(0.015):                             # de la côte vers la ville
                vx, vy = ville[0] - cote[0], ville[1] - cote[1]
            else:                                            # ville sur la côte : perpendiculaire au segment
                vx, vy = -seg[1], seg[0]
            n = math.hypot(vx, vy) or 1
            vx, vy = vx / n, vy / n
            decalage = self.u(c.decalage_nom)
            x, y = cote[0] + vx * decalage, cote[1] + vy * decalage
            angle = math.degrees(math.atan2(vy, vx))
            inverse = math.cos(math.radians(angle)) < 0       # toujours lisible de gauche à droite
            rotation = angle + 180 if inverse else angle
            chateau = c.chateaux and rang_nom == 1 and detail
            # demi-étendue du château dans la direction du nom : plus grande quand la côte est en biais
            demi = l_chateau / 2 * abs(vx) + h / 2 * abs(vy)
            centre_chateau = demi + 0.15
            avant = centre_chateau + demi + 0.3 if chateau else 0.0
            w = largeur(nom)
            ux, uy = math.cos(math.radians(rotation)), math.sin(math.radians(rotation))
            x0, x1 = (-avant - w, -avant) if inverse else (avant, avant + w)
            formes = [Rectangle(x, y, ux, uy, x0, x1, HAUT, BAS)]
            if chateau:
                cx, cy = vx * centre_chateau, vy * centre_chateau
                formes.append(Rectangle(x, y, 1, 0, cx - l_chateau / 2, cx + l_chateau / 2, cy - h / 2, cy + h / 2))
            retenus.append((rang_nom, nom, x, y, rotation, inverse, avant, chateau, vx, vy, centre_chateau,
                            Etiquette(rang_nom, formes, 1.0 if rang_nom == 1 else TAILLE_PETITS_NOMS)))
        palier = paliers([r[-1] for r in retenus], c.paliers_noms)
        noms, chateaux = defaultdict(list), defaultdict(list)
        for (rang_nom, nom, x, y, rotation, inverse, avant, chateau, vx, vy, centre_chateau, _), k in zip(retenus, palier):
            if k is None:                                    # pas de place, même de très près
                continue
            texte = escape(nom, quote=False)
            decale = f' x="{-avant if inverse else avant:.2f}em"' if avant else ""
            fin_nom = ' text-anchor="end"' if inverse else ""
            noms[rang_nom, k].append(f'<text transform="translate({x:.0f} {y:.0f}) rotate({rotation:.0f})"{decale}{fin_nom}>'
                                     f'{texte}</text>')
            if chateau:
                # le dessin fait 22 × 35 unités avec la marge du trait (33 de haut sans elle)
                hc, lc = h * 35 / 33, h * 22 / 33
                chateaux[k].append(f'<use href="#chateau" transform="translate({x:.0f} {y:.0f})" '
                                   f'x="{vx * centre_chateau - lc / 2:.2f}em" y="{vy * centre_chateau - hc / 2:.2f}em" '
                                   f'width="{lc:.2f}em" height="{hc:.2f}em"/>')
        return noms, chateaux

    # ─── Réseaux de rhumbs : une rose centrale et 16 roses sur un cercle ───

    def rhumbs(self) -> tuple[dict, list[dict]]:
        """Lignes par (sorte de vent, origine, intensité). Comme sur les portulans, les droites des roses du cercle
        passent par d'autres roses : une corde est commune à deux roses, un diamètre aux deux roses opposées et à la
        rose centrale. Chaque droite n'est tracée qu'une fois (sinon, avec un tracé irrégulier, elle se dédouble) :
        les 16 droites de la rose centrale (32 vents, dont 8 diamètres), puis pour les roses du cercle, les cordes
        entre roses de même parité (16 directions) et les tangentes. Comme à la main : angle un peu inégal, longueur
        et intensité variables, quelques droites absentes."""
        c = self.c
        hasard = random.Random(c.graine)
        types: dict[tuple[str, str, int], list[str]] = defaultdict(list)
        tracees: dict[int, list[tuple[float, float, float]]] = defaultdict(list)   # par direction : décalage, étendue
        noeuds = []
        for s, (lon, lat, r) in enumerate(c.systemes):
            cx, cy = self.projeter(lon, lat)
            rayon = self.u(r)
            roses = [(cx + rayon * math.sin(math.radians(i * 22.5)), cy - rayon * math.cos(math.radians(i * 22.5)))
                     for i in range(16)]
            noeuds.append({"x": round(cx), "y": round(cy), "s": s, "centre": True})
            noeuds += [{"x": round(x), "y": round(y), "s": s, "centre": False} for x, y in roses[1::2]]
            # (point de passage, cap en degrés, origine) ; cap 0 = nord, sens des aiguilles d'une montre
            droites = [((cx, cy), k * 11.25, "centre") for k in range(16)]
            for i in range(16):
                for j in range(i, 16):
                    if (i + j) % 2 or j == i + 8:            # autre parité : hors des 16 directions ; diamètre : déjà là
                        continue
                    if hasard.random() < c.lignes_manquantes:
                        continue
                    if j == i:                               # tangente
                        droites.append((roses[i], i * 22.5 + 90, "cercle"))
                    else:                                    # corde, passant par son milieu
                        (xi, yi), (xj, yj) = roses[i], roses[j]
                        cap = math.degrees(math.atan2(xj - xi, -(yj - yi)))
                        droites.append((((xi + xj) / 2, (yi + yj) / 2), cap, "cercle"))
            for (px, py), cap, origine in droites:
                k = round(cap / 11.25) % 16
                a = math.radians(k * 11.25 + hasard.uniform(-c.irregularite, c.irregularite))
                ux, uy = math.sin(a), -math.cos(a)
                # longueur de part et d'autre, comptée depuis le point de la droite le plus proche du centre du réseau
                t = (cx - px) * ux + (cy - py) * uy
                l1 = rayon * c.portee * (1 + hasard.uniform(-c.variation_longueur, c.variation_longueur))
                l2 = rayon * c.portee * (1 + hasard.uniform(-c.variation_longueur, c.variation_longueur))
                genre = "vents" if k % 4 == 0 else ("demi" if k % 2 == 0 else "quarts")
                intensite = hasard.choices((0, 1, 2), weights=(3, 5, 2))[0]
                (x1, y1), (x2, y2) = (px + ux * (t - l1), py + uy * (t - l1)), (px + ux * (t + l2), py + uy * (t + l2))
                # une droite presque confondue avec une autre déjà tracée (d'un réseau voisin) doublerait le trait
                a0 = math.radians(k * 11.25)
                decalage = px * math.cos(a0) + py * math.sin(a0)
                debut, fin = sorted((x1 * math.sin(a0) - y1 * math.cos(a0), x2 * math.sin(a0) - y2 * math.cos(a0)))
                if any(abs(decalage - d) < self.u(c.ecart_rhumbs) and min(fin, f) > max(debut, g) for d, g, f in tracees[k]):
                    continue
                tracees[k].append((decalage, debut, fin))
                types[(genre, origine, intensite)].append(f"M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}")
        return {k: "".join(v) for k, v in types.items()}, noeuds


def _petite_rose() -> str:
    return (f'<g id="petite-rose"><circle r="34" style="fill:none;stroke:var(--rose-trait);stroke-width:3"/>'
            f'<polygon points="{etoile(4, 30, 7, 45)}" style="fill:var(--rose-2)"/>'
            f'<polygon points="{etoile(4, 50, 9)}" style="fill:var(--rose-1)"/></g>')


def _chateau() -> str:
    """Petit château de port, à la manière des vignettes de villes des portulans : muraille crénelée, tour, toit et
    fanion. Chaque <use> le pose entre la côte et le nom, en em : il suit la taille des noms (--taille-noms)."""
    trait = "stroke:var(--ville-trait,#cfcdc6)"
    fond = "fill:var(--ville-fond,#111317)"
    toit = "fill:var(--ville-toit,#d8573c)"
    return ('<symbol id="chateau" viewBox="-11 -34 22 35">'
            f'<path d="M-10 0V-11H-8V-13.5H-6V-11H-4V-13.5H-2V-11H2V-13.5H4V-11H6V-13.5H8V-11H10V0Z" style="{fond};{trait}"/>'
            f'<path d="M-4 -11V-20H4V-11" style="{fond};{trait}"/>'
            f'<path d="M-5 -20L0 -27L5 -20Z" style="{toit};{trait}"/>'
            f'<path d="M-2 0V-4.5A2 2 0 0 1 2 -4.5V0" style="fill:none;{trait}"/>'
            f'<path d="M0 -27V-33" style="fill:none;{trait}"/>'
            f'<path d="M0 -33L6.5 -31.5L0 -30Z" style="{toit};stroke:none"/></symbol>')


def generer(source: Source, config: Config | None = None, journal=None) -> Carte:
    """Dessine la carte. « journal », s'il est donné, reçoit un message à chaque étape."""
    config = config or Config()
    dire = journal or (lambda _: None)
    dessin = _Dessin(source, config)
    dire("Terres…")
    d_terres = dessin.terres()
    dire("Côtes…")
    d_cotes, lignes = dessin.cotes()
    d_lacs = dessin.lacs()
    dire("Noms des ports…")
    noms, chateaux = dessin.noms(lignes)
    dire("Rhumbs et roses…")
    r, noeuds = dessin.rhumbs()
    roses_noeuds = "".join(
        f'<use href="#petite-rose" transform="translate({p["x"]} {p["y"]}) scale({1.5 if p["centre"] else 0.8})"'
        + ("" if p["centre"] else ' style="opacity:var(--rhumbs-cercles,1)"') + "/>" for p in noeuds)
    def rose(lon, lat, taille):
        x, y = dessin.projeter(lon, lat)
        return f'<use href="#rose-ornee" transform="translate({x:.0f} {y:.0f}) scale({taille * UNITES / 100:.2f})"/>'

    grandes = "".join(rose(*r) for r in config.grandes_roses)
    centrale = rose(*config.rose_centrale) if config.rose_centrale else ""
    # Épaisseur des traits en unités de la carte : --trait vaut un pixel à l'écran (à recalculer quand la vue change).
    # « vector-effect: non-scaling-stroke » ferait de même, mais ralentit beaucoup le navigateur.
    trait = "fill:none;stroke-linejoin:round"
    texte = "font-family:Spectral,Georgia,serif;font-style:italic;font-size:var(--taille-noms,40px);letter-spacing:.02em"
    # intensités des lignes (opacité, épaisseur) : l'encre d'un tracé à la main n'est pas uniforme
    intensites = ((0.5, 1), (0.8, 1), (1, 1.35))
    encres = {"vents": "var(--rhumb-vent)", "demi": "var(--rhumb-demi)", "quarts": "var(--rhumb-quart)"}

    def lignes_de(origine):
        return "".join(
            f'<path d="{r[(g, origine, i)]}" style="stroke:{encres[g]};opacity:{o};'
            f'stroke-width:calc(var(--trait,8px) * {e})"/>'
            for g in encres for i, (o, e) in enumerate(intensites) if r.get((g, origine, i)))

    def par_palier(elements: dict, cle) -> str:
        """Un groupe par palier : la page montre ou cache chacun avec --noms-p0, --noms-p1…"""
        return "".join(f'<g style="visibility:var(--noms-p{k},visible)">{"".join(elements[cle(k)])}</g>'
                       for k in range(len(config.paliers_noms)) if elements.get(cle(k)))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<!-- Carte à la manière des portulans, d'après Natural Earth (domaine public). Projection de Mercator, centièmes de degré. -->
<defs>
{_petite_rose()}
{_chateau()}
{rose_ornee()}
</defs>
<g id="terres">
<path d="{d_terres}" style="fill:var(--terre-fond);stroke:none"/>
<path d="{d_lacs}" style="fill:var(--lac-fond);stroke:var(--terre-trait);stroke-width:calc(var(--trait,8px) * .8);stroke-linejoin:round"/>
<path d="{d_cotes}" style="stroke:var(--terre-trait);stroke-width:var(--trait,8px);{trait}"/>
</g>
<g id="noms" style="{texte}">
<g style="fill:var(--nom-1);opacity:var(--noms-1,1)">{par_palier(noms, lambda k: (1, k))}</g>
<g style="fill:var(--nom-2);opacity:var(--noms-2,1);font-size:calc(var(--taille-noms,40px) * {TAILLE_PETITS_NOMS})">{par_palier(noms, lambda k: (2, k))}</g>
</g>
<g id="villes" style="font-size:var(--taille-noms,40px);stroke-width:2;stroke-linejoin:round;opacity:var(--villes,1)">{par_palier(chateaux, lambda k: k)}</g>
<g id="rhumbs" style="{trait}">
<g>{lignes_de("centre")}</g>
<g style="opacity:var(--rhumbs-cercles,1)">{lignes_de("cercle")}</g>
</g>
<g id="roses-noeuds">{roses_noeuds}</g>
<g id="roses" style="opacity:var(--grandes-roses,1)">{grandes}</g>
<g id="rose-centrale" style="opacity:var(--rose-centrale,1)">{centrale}</g>
</svg>
"""
    compte = lambda rang: sum(len(v) for (r, _), v in noms.items() if r == rang)
    return Carte(svg=svg, noeuds=noeuds, nombre_noms=(compte(1), compte(2)),
                 nombre_villes=sum(len(v) for v in chateaux.values()), paliers=tuple(config.paliers_noms))
