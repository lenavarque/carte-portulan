"""La grande rose des vents ornée, dessinée comme sur les portulans.

32 branches : 4 vents cardinaux (rouge), 4 vents intermédiaires (or), 8 demi-vents (encre pâle), 16 quarts de vent
(vert). Au nord, une fleur de lys (la tramontane) ; à l'est, une croix (le levant, vers Jérusalem) ; ailleurs, les
initiales des vents méditerranéens : Grec, Sirocco, Ostro, Libeccio, Ponant, Mistral.

La rose tient dans un cercle de rayon 100 (132 avec la fleur de lys et les lettres). Ses couleurs sont des variables
CSS, avec une valeur par défaut : --rose-1 (rouge), --rose-2 (or), --rose-3 (encre pâle), --rose-4 (vert),
leurs variantes « -sombre » pour la face ombrée des branches, --rose-trait (anneau) et --nuit (cœur).
"""
import math

VERT = ("var(--rose-4, #7fae89)", "var(--rose-4-sombre, #3f5f47)")
PALE = ("var(--rose-3, #cfcdc6)", "var(--rose-3-sombre, #6c6f75)")
OR = ("var(--rose-2, #d9aa45)", "var(--rose-2-sombre, #8a6a25)")
ROUGE = ("var(--rose-1, #d8573c)", "var(--rose-1-sombre, #8e3321)")
TRAIT = "var(--rose-trait, rgba(228,227,222,.4))"

LYS = ('<g transform="translate(0 -113) scale(.95)" style="fill:var(--rose-1, #d8573c)">'
       '<path d="M0-17C6-11 7-4 2.5 3H-2.5C-7-4-6-11 0-17Z"/>'
       '<path d="M-2.5 2C-6-3-9-5-12.5-4.5-15-4-16 0-13.5 1.5-12 .5-10.5 1-9.5 3-8.5 4.5-5.5 5-2.5 4Z"/>'
       '<path d="M2.5 2C6-3 9-5 12.5-4.5 15-4 16 0 13.5 1.5 12 .5 10.5 1 9.5 3 8.5 4.5 5.5 5 2.5 4Z"/>'
       '<rect x="-8" y="3" width="16" height="3.2" rx=".6"/>'
       '<path d="M-2.4 6.2H2.4L1.4 13H-1.4Z"/></g>')
CROIX = ('<g transform="translate(113 0)" style="fill:var(--rose-1, #d8573c)">'
         '<path d="M-2.2-10H2.2V-2.2H10V2.2H2.2V10H-2.2V2.2H-10V-2.2H-2.2Z"/></g>')
VENTS = (("G", 45), ("S", 135), ("O", 180), ("L", 225), ("P", 270), ("M", 315))


def _point(r: float, cap: float) -> tuple[float, float]:
    """Point à la distance r, au cap donné (0 = nord, sens horaire)."""
    t = math.radians(cap)
    return r * math.sin(t), -r * math.cos(t)


def _f(p: tuple[float, float]) -> str:
    return f"{p[0]:.2f},{p[1]:.2f}"


def _branche(cap: float, longueur: float, largeur: float, clair: str, sombre: str) -> str:
    """Une branche en deux triangles : face éclairée à gauche, face ombrée à droite."""
    pointe, gauche, droite = _point(longueur, cap), _point(largeur, cap - 90), _point(largeur, cap + 90)
    return (f'<polygon points="0,0 {_f(pointe)} {_f(gauche)}" style="fill:{clair}"/>'
            f'<polygon points="0,0 {_f(pointe)} {_f(droite)}" style="fill:{sombre}"/>')


def rose_ornee(identifiant: str | None = "rose-ornee") -> str:
    """La rose en fragment SVG <g>, centrée sur l'origine, à placer dans un <svg> ou des <defs>."""
    morceaux = [f'<circle r="96" style="fill:none;stroke:{TRAIT};stroke-width:1.2"/>'
                f'<circle r="89" style="fill:none;stroke:{TRAIT};stroke-width:.8"/>'
                f'<circle r="62" style="fill:none;stroke:{TRAIT};stroke-width:.6"/>']
    graduations = []
    for i in range(128):
        cap = i * 360 / 128
        r1 = 89 if i % 4 == 0 else (92 if i % 2 == 0 else 94)
        graduations.append(f"M{_f(_point(r1, cap))}L{_f(_point(96, cap))}")
    morceaux.append(f'<path d="{"".join(graduations)}" style="fill:none;stroke:{TRAIT};stroke-width:.6"/>')
    for i in range(16):                                   # des plus petites branches aux plus grandes
        morceaux.append(_branche(11.25 + i * 22.5, 56, 4.2, *VERT))
    for i in range(8):
        morceaux.append(_branche(22.5 + i * 45, 70, 6.5, *PALE))
    for i in range(4):
        morceaux.append(_branche(45 + i * 90, 80, 9.5, *OR))
    for i in range(4):
        morceaux.append(_branche(i * 90, 88, 12, *ROUGE))
    morceaux.append('<circle r="7" style="fill:var(--nuit, #111317);stroke:var(--rose-2, #d9aa45);stroke-width:1.4"/>'
                    '<circle r="2.2" style="fill:var(--rose-2, #d9aa45)"/>')
    lettres = []
    for lettre, cap in VENTS:
        x, y = _point(111, cap)
        lettres.append(f'<text x="{x:.1f}" y="{y + 5.5:.1f}" text-anchor="middle">{lettre}</text>')
    morceaux.append(LYS + CROIX + '<g style="font-family:Spectral,Georgia,serif;font-weight:600;font-size:16px;'
                    'fill:var(--rose-3, #cfcdc6)">' + "".join(lettres) + "</g>")
    attribut = f' id="{identifiant}"' if identifiant else ""
    return f"<g{attribut}>" + "".join(morceaux) + "</g>"


def rose_ornee_autonome(taille: int = 512) -> str:
    """La rose seule, en fichier SVG complet (couleurs par défaut)."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-132 -132 264 264" width="{taille}" height="{taille}">\n'
            f"<title>Rose des vents</title>\n{rose_ornee(None)}\n</svg>\n")
