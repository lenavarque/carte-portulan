"""Lecture des couches Natural Earth (shapefile + dbf), sans dépendance.

Une Source peut être :
- l'archive complète « natural_earth_vector.zip » (ou toute archive zip contenant les couches) ;
- un dossier contenant les couches, décompressées (.shp et .dbf) ou dans leur zip d'origine (ne_50m_land.zip…).
Les couches sont cherchées par leur nom (« ne_50m_land »), où qu'elles soient rangées.

Seuls les types Point, PolyLine et Polygon sont gérés : ils suffisent pour les côtes, les terres, les lacs et les villes.
"""
import struct
import zipfile
from collections.abc import Iterable
from pathlib import Path

Geometrie = tuple[float, float] | list[list[tuple[float, float]]] | None


class CoucheIntrouvable(FileNotFoundError):
    """La couche demandée n'est ni dans l'archive, ni dans le dossier."""


def lire_formes(octets: bytes) -> list[Geometrie]:
    """Géométries d'un fichier .shp : (x, y) pour un point, [[(x, y), …], …] (une liste par partie) pour une ligne
    ou un polygone, None pour une forme vide."""
    formes: list[Geometrie] = []
    pos = 100                                            # en-tête du fichier
    while pos + 8 <= len(octets):
        _, longueur = struct.unpack(">ii", octets[pos:pos + 8])
        debut = pos + 8
        pos = debut + longueur * 2                       # longueur en mots de 16 bits
        type_ = struct.unpack("<i", octets[debut:debut + 4])[0]
        if type_ == 0:
            formes.append(None)
        elif type_ == 1:
            formes.append(struct.unpack("<dd", octets[debut + 4:debut + 20]))
        elif type_ in (3, 5):
            nparts, npoints = struct.unpack("<ii", octets[debut + 36:debut + 44])
            parts = list(struct.unpack(f"<{nparts}i", octets[debut + 44:debut + 44 + 4 * nparts])) + [npoints]
            base = debut + 44 + 4 * nparts
            pts = struct.unpack(f"<{2 * npoints}d", octets[base:base + 16 * npoints])
            formes.append([[(pts[2 * i], pts[2 * i + 1]) for i in range(parts[k], parts[k + 1])] for k in range(nparts)])
        else:
            raise ValueError(f"type de forme non géré : {type_}")
    return formes


def lire_attributs(octets: bytes, champs: Iterable[str] | None = None,
                   encodage: str = "utf-8") -> tuple[list[dict[str, str]], list[str]]:
    """Attributs d'un fichier .dbf : (lignes, noms des champs). « champs » limite les champs lus (tous si None)."""
    voulus = None if champs is None else set(champs)
    n, entete, long_ligne = struct.unpack("<IHH", octets[4:12])
    descripteurs, pos = [], 32
    while octets[pos] != 0x0D:
        nom = octets[pos:pos + 11].split(b"\0")[0].decode("ascii")
        descripteurs.append((nom, octets[pos + 16]))
        pos += 32
    lignes = []
    for i in range(n):
        ligne, p = {}, entete + i * long_ligne + 1        # 1 : indicateur de suppression
        for nom, taille in descripteurs:
            if voulus is None or nom in voulus:
                ligne[nom] = octets[p:p + taille].decode(encodage, "replace").strip()
            p += taille
        lignes.append(ligne)
    return lignes, [d[0] for d in descripteurs]


class Source:
    """Les couches Natural Earth, dans une archive zip ou un dossier."""

    def __init__(self, chemin: str | Path):
        self.chemin = Path(chemin)
        if not self.chemin.exists():
            raise FileNotFoundError(f"Natural Earth introuvable : {self.chemin}")

    def __repr__(self) -> str:
        return f"Source({str(self.chemin)!r})"

    def _fichiers(self, couche: str) -> dict[str, bytes]:
        """Contenu des fichiers .shp, .dbf (et .cpg s'il existe) de la couche."""
        voulus = {f"{couche}.{ext}".lower() for ext in ("shp", "dbf", "cpg")}
        if self.chemin.is_file():
            with zipfile.ZipFile(self.chemin) as z:
                return self._dans_zip(z, voulus)
        trouves = {}
        for f in self.chemin.rglob("*"):
            if f.name.lower() in voulus:
                trouves[f.suffix[1:].lower()] = f.read_bytes()
        if "shp" not in trouves:
            for archive in self.chemin.rglob(f"{couche}.zip"):
                with zipfile.ZipFile(archive) as z:
                    trouves = self._dans_zip(z, voulus)
                break
        return trouves

    @staticmethod
    def _dans_zip(z: zipfile.ZipFile, voulus: set[str]) -> dict[str, bytes]:
        return {Path(n).suffix[1:].lower(): z.read(n) for n in z.namelist() if Path(n).name.lower() in voulus}

    def lire(self, couche: str, champs: Iterable[str] | None = None) -> list[tuple[Geometrie, dict[str, str]]]:
        """[(géométrie, attributs)] de la couche « couche » (par exemple « ne_50m_land »)."""
        fichiers = self._fichiers(couche)
        if "shp" not in fichiers or "dbf" not in fichiers:
            raise CoucheIntrouvable(f"Couche « {couche} » introuvable dans {self.chemin}")
        encodage = fichiers.get("cpg", b"utf-8").decode("ascii", "replace").strip() or "utf-8"
        if encodage.upper() in ("UTF-8", "UTF8", "65001"):
            encodage = "utf-8"
        formes = lire_formes(fichiers["shp"])
        attributs, _ = lire_attributs(fichiers["dbf"], champs, encodage)
        return list(zip(formes, attributs))
