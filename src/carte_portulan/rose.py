"""La grande rose des vents, gravée à l'encre comme sur les portulans.

32 branches en quatre tailles : 4 vents cardinaux, 4 vents intermédiaires, 8 demi-vents, 16 quarts de vent. Chaque
branche a une face claire (couleur du papier) et une face ombrée par des hachures, à l'encre pâle, ou au cinabre pour
les huit vents principaux. Autour, un anneau gradué et les noms des vents méditerranéens en toutes lettres
(Tramontana, Greco, Levante, Scirocco, Ostro, Libeccio, Ponente, Maestro) ; au-delà, une fleur de lys au nord et
une croix au levant.

La rose tient dans un cercle de rayon 100 (132 avec les noms, la fleur de lys et la croix). Ses couleurs sont des
variables CSS, avec une valeur par défaut : --rose-encre (traits et hachures), --rose-1 (cinabre), --rose-papier
(face claire des branches, par défaut --nuit).
"""
import math

ENCRE = "var(--rose-encre, #cfcdc6)"
ROUGE = "var(--rose-1, #d8573c)"
PAPIER = "var(--rose-papier, var(--nuit, #111317))"

# (cap du premier vent, pas, nombre, longueur, demi-largeur, couleur des hachures, écart des hachures)
BRANCHES = (
    (11.25, 22.5, 16, 50, 3.4, ENCRE, 1.7),       # quarts de vent
    (22.5, 45, 8, 66, 5.4, ENCRE, 1.4),           # demi-vents
    (45, 90, 4, 80, 8.0, ROUGE, 1.25),            # vents intermédiaires
    (0, 90, 4, 92, 10.5, ROUGE, 1.2),             # vents cardinaux
)
VENTS = ("Tramontana", "Greco", "Levante", "Scirocco", "Ostro", "Libeccio", "Ponente", "Maestro")

LYS = ('<g transform="translate(0 -121) scale(.72)" style="fill:{rouge};stroke:none">'
       '<path d="M0-17C6-11 7-4 2.5 3H-2.5C-7-4-6-11 0-17Z"/>'
       '<path d="M-2.5 2C-6-3-9-5-12.5-4.5-15-4-16 0-13.5 1.5-12 .5-10.5 1-9.5 3-8.5 4.5-5.5 5-2.5 4Z"/>'
       '<path d="M2.5 2C6-3 9-5 12.5-4.5 15-4 16 0 13.5 1.5 12 .5 10.5 1 9.5 3 8.5 4.5 5.5 5 2.5 4Z"/>'
       '<rect x="-8" y="3" width="16" height="3.2" rx=".6"/>'
       '<path d="M-2.4 6.2H2.4L1.4 13H-1.4Z"/></g>').format(rouge=ROUGE)
CROIX = ('<g transform="translate(122 0) scale(.72)" style="fill:{rouge};stroke:none">'
         '<path d="M-2.2-10H2.2V-2.2H10V2.2H2.2V10H-2.2V2.2H-10V-2.2H-2.2Z"/></g>').format(rouge=ROUGE)


def _point(r: float, cap: float) -> tuple[float, float]:
    """Point à la distance r, au cap donné (0 = nord, sens horaire)."""
    t = math.radians(cap)
    return r * math.sin(t), -r * math.cos(t)


def _f(x: float, y: float) -> str:
    return f"{x:.2f},{y:.2f}"


def _branche(cap: float, longueur: float, largeur: float, ecart: float) -> tuple[str, str]:
    """(contour de la branche, hachures de sa face ombrée), en commandes de chemin SVG."""
    ux, uy = _point(1, cap)                        # vers la pointe
    px, py = _point(1, cap + 90)                   # vers la face ombrée (à droite, dans le sens horaire)
    pointe = (ux * longueur, uy * longueur)
    gauche, droite = (-px * largeur, -py * largeur), (px * largeur, py * largeur)
    contour = f"M{_f(*gauche)}L{_f(*pointe)}L{_f(*droite)}Z M0,0L{_f(*pointe)}"
    hachures = []
    d = ecart * 0.6
    while d < largeur - 0.25:                      # traits parallèles à l'axe, du centre vers le bord de la face
        bout = longueur * (1 - d / largeur)
        x0, y0 = px * d, py * d
        hachures.append(f"M{_f(x0, y0)}L{_f(x0 + ux * bout, y0 + uy * bout)}")
        d += ecart
    return contour, "".join(hachures)


def rose_ornee(identifiant: str | None = "rose-ornee") -> str:
    """La rose en fragment SVG <g>, centrée sur l'origine, à placer dans un <svg> ou des <defs>."""
    trait = f"fill:none;stroke:{ENCRE};stroke-linejoin:round"
    graduations = []
    for i in range(128):
        cap = i * 360 / 128
        r1 = 94 if i % 4 == 0 else (96.5 if i % 2 == 0 else 98)
        graduations.append(f"M{_f(*_point(r1, cap))}L{_f(*_point(100, cap))}")
    morceaux = [f'<circle r="100" style="{trait};stroke-width:.8"/>',
                f'<circle r="94" style="{trait};stroke-width:.5"/>',
                f'<path d="{"".join(graduations)}" style="{trait};stroke-width:.4"/>',
                f'<circle r="66" style="{trait};stroke-width:.4;stroke-dasharray:1.5 2"/>']
    for depart, pas, nombre, longueur, largeur, couleur, ecart in BRANCHES:
        contours, hachures = [], []
        for i in range(nombre):
            c, h = _branche(depart + i * pas, longueur, largeur, ecart)
            contours.append(c)
            hachures.append(h)
        # face claire (couleur du papier, cache les lignes de rhumb dessous), hachures, puis contour
        morceaux.append(f'<path d="{"".join(c.split(" M0")[0] for c in contours)}" style="fill:{PAPIER};stroke:none"/>')
        morceaux.append(f'<path d="{"".join(hachures)}" style="fill:none;stroke:{couleur};stroke-width:.45"/>')
        morceaux.append(f'<path d="{" ".join(contours)}" style="{trait};stroke-width:.55"/>')
    morceaux.append(f'<circle r="20" style="{trait};stroke-width:.4"/>'
                    f'<circle r="5" style="fill:{PAPIER};stroke:{ROUGE};stroke-width:.8"/>'
                    f'<circle r="1.8" style="fill:{ROUGE}"/>')
    noms = []
    for i, nom in enumerate(VENTS):
        cap = i * 45
        x, y = _point(107, cap)
        rotation = cap if math.cos(math.radians(cap)) >= -0.01 else cap + 180   # jamais à l'envers
        noms.append(f'<text transform="translate({x:.2f} {y:.2f}) rotate({rotation:g})" text-anchor="middle" '
                    f'dy="2.6">{nom}</text>')
    morceaux.append(f'<g style="font-family:Spectral,Georgia,serif;font-style:italic;font-size:7.5px;'
                    f'letter-spacing:.08em;fill:{ENCRE}">' + "".join(noms) + "</g>")
    morceaux.append(LYS + CROIX)
    attribut = f' id="{identifiant}"' if identifiant else ""
    return f"<g{attribut}>" + "".join(morceaux) + "</g>"


def rose_ornee_autonome(taille: int = 512) -> str:
    """La rose seule, en fichier SVG complet (couleurs par défaut)."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-132 -132 264 264" width="{taille}" height="{taille}">\n'
            f"<title>Rose des vents</title>\n{rose_ornee(None)}\n</svg>\n")
