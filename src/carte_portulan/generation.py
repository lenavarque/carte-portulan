"""Assemblage de la carte : terres, côtes, lacs, noms des ports, réseaux de rhumbs et roses.

Le SVG produit n'a pas de viewBox : il sert de réserve de groupes, à afficher avec <use> (voir le README).
Groupes : « terres », « noms », « rhumbs », « roses-noeuds », « roses », « rose-centrale ». Les couleurs et les épaisseurs viennent
de variables CSS, héritées à travers <use> : la page qui affiche la carte les choisit.
"""
import math
from dataclasses import dataclass
from html import escape

from .config import Config
from .geometrie import Grille, chemin, dans_boite, etendue, etoile, morceaux, simplifier
from .natural_earth import Source
from .projection import UNITES
from .projection import projeter as _projeter
from .rose import rose_ornee


@dataclass
class Carte:
    svg: str                        # le document SVG
    noeuds: list[dict]              # roses du réseau : x, y (unités de la carte), s (réseau), centre (bool)
    nombre_noms: tuple[int, int]    # (grands ports, autres ports)

    def index(self) -> dict:
        """Données annexes, à écrire en JSON à côté du SVG."""
        return {"k": UNITES, "noeuds": self.noeuds}


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

    def noms(self, lignes_cotes: list) -> dict[int, list[str]]:
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
            candidats.append((rang_nom, rang, -float(a["POP_MAX"] or 0), nom, (x, y), point, seg, d))
        candidats.sort()
        places, sortie = [], {1: [], 2: []}
        for rang_nom, _, _, nom, ville, cote, seg, d in candidats:
            ecart = self.u(c.ecart_grands_ports if rang_nom == 1 else c.ecart_petits_ports)
            if any(math.dist(cote, p) < max(ecart, e) for p, e in places):
                continue
            if d > self.u(0.015):                             # de la côte vers la ville
                vx, vy = ville[0] - cote[0], ville[1] - cote[1]
            else:                                            # ville sur la côte : perpendiculaire au segment
                vx, vy = -seg[1], seg[0]
            n = math.hypot(vx, vy) or 1
            vx, vy = vx / n, vy / n
            angle = math.degrees(math.atan2(vy, vx))
            decalage = self.u(c.decalage_nom)
            x, y = cote[0] + vx * decalage, cote[1] + vy * decalage
            places.append((cote, ecart))
            texte = escape(nom, quote=False)
            if math.cos(math.radians(angle)) < 0:            # toujours lisible de gauche à droite
                sortie[rang_nom].append(f'<text transform="translate({x:.0f} {y:.0f}) rotate({angle + 180:.0f})" '
                                        f'text-anchor="end">{texte}</text>')
            else:
                sortie[rang_nom].append(f'<text transform="translate({x:.0f} {y:.0f}) rotate({angle:.0f})">{texte}</text>')
        return sortie

    # ─── Réseaux de rhumbs : une rose centrale et 16 roses sur un cercle, 32 vents chacune ───

    def rhumbs(self) -> tuple[dict, list[dict]]:
        types = {(g, o): [] for g in ("vents", "demi", "quarts") for o in ("centre", "cercle")}
        noeuds = []
        for s, (lon, lat, r) in enumerate(self.c.systemes):
            cx, cy = self.projeter(lon, lat)
            rayon = self.u(r)
            points = [(cx, cy, "centre")] + [(cx + rayon * math.sin(math.radians(i * 22.5)),
                                              cy - rayon * math.cos(math.radians(i * 22.5)), "cercle")
                                             for i in range(16)]
            for i, (x, y, genre) in enumerate(points):
                if genre == "centre" or i % 2 == 1:           # une rose sur deux porte une petite rose dessinée
                    noeuds.append({"x": round(x), "y": round(y), "s": s, "centre": genre == "centre"})
                for k in range(16):                            # 16 droites = 32 directions
                    a = math.radians(k * 11.25)
                    dx, dy = math.sin(a) * rayon * self.c.portee, -math.cos(a) * rayon * self.c.portee
                    genre_ligne = "vents" if k % 4 == 0 else ("demi" if k % 2 == 0 else "quarts")
                    types[(genre_ligne, genre)].append(f"M{x - dx:.0f} {y - dy:.0f}L{x + dx:.0f} {y + dy:.0f}")
        return {k: "".join(v) for k, v in types.items()}, noeuds


def _petite_rose() -> str:
    return (f'<g id="petite-rose"><circle r="34" style="fill:none;stroke:var(--rose-trait);stroke-width:3"/>'
            f'<polygon points="{etoile(4, 30, 7, 45)}" style="fill:var(--rose-2)"/>'
            f'<polygon points="{etoile(4, 50, 9)}" style="fill:var(--rose-1)"/></g>')


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
    noms = dessin.noms(lignes)
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
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<!-- Carte à la manière des portulans, d'après Natural Earth (domaine public). Projection de Mercator, centièmes de degré. -->
<defs>
{_petite_rose()}
{rose_ornee()}
</defs>
<g id="terres">
<path d="{d_terres}" style="fill:var(--terre-fond);stroke:none"/>
<path d="{d_lacs}" style="fill:var(--lac-fond);stroke:var(--terre-trait);stroke-width:calc(var(--trait,8px) * .8);stroke-linejoin:round"/>
<path d="{d_cotes}" style="stroke:var(--terre-trait);stroke-width:var(--trait,8px);{trait}"/>
</g>
<g id="noms" style="{texte}">
<g style="fill:var(--nom-1);opacity:var(--noms-1,1)">{"".join(noms[1])}</g>
<g style="fill:var(--nom-2);opacity:var(--noms-2,1)">{"".join(noms[2])}</g>
</g>
<g id="rhumbs" style="stroke-width:var(--trait,8px);{trait}">
<g><path d="{r[('vents', 'centre')]}" style="stroke:var(--rhumb-vent)"/><path d="{r[('demi', 'centre')]}" style="stroke:var(--rhumb-demi)"/><path d="{r[('quarts', 'centre')]}" style="stroke:var(--rhumb-quart)"/></g>
<g style="opacity:var(--rhumbs-cercles,1)"><path d="{r[('vents', 'cercle')]}" style="stroke:var(--rhumb-vent)"/><path d="{r[('demi', 'cercle')]}" style="stroke:var(--rhumb-demi)"/><path d="{r[('quarts', 'cercle')]}" style="stroke:var(--rhumb-quart)"/></g>
</g>
<g id="roses-noeuds">{roses_noeuds}</g>
<g id="roses" style="opacity:var(--grandes-roses,1)">{grandes}</g>
<g id="rose-centrale" style="opacity:var(--rose-centrale,1)">{centrale}</g>
</svg>
"""
    return Carte(svg=svg, noeuds=noeuds, nombre_noms=(len(noms[1]), len(noms[2])))
