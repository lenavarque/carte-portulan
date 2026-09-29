"""Fabrique de petites couches Natural Earth factices (shapefile + dbf), pour tester sans les vraies données."""
import struct
from pathlib import Path


def ecrire_shp(chemin: Path, type_: int, formes: list) -> None:
    """type_ : 1 (points : (x, y)), 3 (lignes) ou 5 (polygones) : [[(x, y), …], …] par forme."""
    enregistrements = []
    for numero, forme in enumerate(formes, start=1):
        if type_ == 1:
            contenu = struct.pack("<idd", 1, *forme)
        else:
            points = [p for partie in forme for p in partie]
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            debuts, n = [], 0
            for partie in forme:
                debuts.append(n)
                n += len(partie)
            contenu = struct.pack("<i4d2i", type_, min(xs), min(ys), max(xs), max(ys), len(forme), len(points))
            contenu += struct.pack(f"<{len(debuts)}i", *debuts)
            contenu += b"".join(struct.pack("<2d", *p) for p in points)
        enregistrements.append(struct.pack(">2i", numero, len(contenu) // 2) + contenu)
    corps = b"".join(enregistrements)
    entete = struct.pack(">7i", 9994, 0, 0, 0, 0, 0, (100 + len(corps)) // 2)
    entete += struct.pack("<2i4d4d", 1000, type_, 0, 0, 0, 0, 0, 0, 0, 0)
    chemin.write_bytes(entete + corps)


def ecrire_dbf(chemin: Path, champs: list[tuple[str, int]], lignes: list[dict]) -> None:
    """champs : [(nom, largeur)], tous de type texte."""
    long_ligne = 1 + sum(largeur for _, largeur in champs)
    long_entete = 32 + 32 * len(champs) + 1
    entete = struct.pack("<B3BIHH20x", 3, 126, 9, 28, len(lignes), long_entete, long_ligne)
    for nom, largeur in champs:
        entete += struct.pack("<11sc4xBB14x", nom.encode("ascii"), b"C", largeur, 0)
    entete += b"\r"
    corps = b"".join(b" " + b"".join(str(ligne.get(nom, "")).encode("utf-8").ljust(largeur)[:largeur]
                                     for nom, largeur in champs) for ligne in lignes)
    chemin.write_bytes(entete + corps + b"\x1a")


def ecrire_couche(dossier: Path, nom: str, type_: int, formes: list, champs: list[tuple[str, int]], lignes: list[dict]) -> None:
    ecrire_shp(dossier / f"{nom}.shp", type_, formes)
    ecrire_dbf(dossier / f"{nom}.dbf", champs, lignes)
    (dossier / f"{nom}.cpg").write_text("UTF-8", encoding="ascii")


def monde_factice(dossier: Path) -> None:
    """Une île carrée en Méditerranée (5° E – 7° E, 40° N – 42° N), un lac, et deux villes au bord de l'eau."""
    ile = [[(5.0, 40.0), (5.0, 42.0), (7.0, 42.0), (7.0, 40.0), (5.0, 40.0)]]
    lac = [[(5.8, 40.8), (5.8, 41.2), (6.2, 41.2), (6.2, 40.8), (5.8, 40.8)]]
    ecrire_couche(dossier, "ne_10m_land", 5, [ile], [("featurecla", 20)], [{"featurecla": "Land"}])
    ecrire_couche(dossier, "ne_50m_lakes", 5, [lac], [("scalerank", 4)], [{"scalerank": "0"}])
    champs = [("SCALERANK", 4), ("NAME", 30), ("NAME_FR", 30), ("ADM0CAP", 4), ("LATITUDE", 12), ("LONGITUDE", 12),
              ("POP_MAX", 12)]
    villes = [
        {"SCALERANK": "1", "NAME": "Portus", "NAME_FR": "Port-Royal", "ADM0CAP": "0", "LATITUDE": "41.0",
         "LONGITUDE": "5.05", "POP_MAX": "100000"},
        {"SCALERANK": "5", "NAME": "Caleta & Mar", "NAME_FR": "", "ADM0CAP": "0", "LATITUDE": "41.95",
         "LONGITUDE": "6.0", "POP_MAX": "2000"},
        {"SCALERANK": "5", "NAME": "Loin", "NAME_FR": "Loin", "ADM0CAP": "0", "LATITUDE": "30.0",
         "LONGITUDE": "30.0", "POP_MAX": "1000"},
    ]
    ecrire_couche(dossier, "ne_10m_populated_places", 1,
                  [(float(v["LONGITUDE"]), float(v["LATITUDE"])) for v in villes], champs, villes)
