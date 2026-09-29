# Journal des versions

Les changements notables de ce projet sont notés ici. Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et les numéros de version suivent le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté

- Rose centrale (groupe `rose-centrale`, réglage `rose_centrale`) : une grande rose au centre du réseau de rhumbs
  de la Méditerranée, d'où partent les lignes.
- Villes dessinées (groupe `villes`, réglages `chateaux` et `taille_chateau`) : un petit château devant le nom
  des grands ports de la zone détaillée, à la taille des noms. Couleurs : `--ville-trait`, `--ville-fond` et
  `--ville-toit`.
- Noms sans chevauchement (module `etiquettes`, réglage `paliers_noms`) : chaque nom reçoit un palier de zoom, le
  premier où il a sa place ; la page montre ou cache chaque palier avec `--noms-p0`, `--noms-p1`… Les seuils sont
  écrits dans `portulan.json`.
- Démonstration en ligne sur GitHub Pages : la carte en plein écran, à déplacer et zoomer, avec des vues prêtes,
  des couches à masquer et la vue gardée dans l'adresse. Générée et publiée par un workflow à chaque envoi.
- Étendue de la carte dans `portulan.json` (`bornes` : x ouest, y nord, x est, y sud), pour qu'une page n'en
  montre jamais les bords.
- Variable CSS `--vents` : `none` cache les noms des vents des grandes roses, que le navigateur remet en page à
  chaque zoom (utile pendant une animation).
- Variable CSS `--petits-noms` : `none` retire les petits noms, sans les mettre en page (plus léger que
  `--noms-2: 0` sur un téléphone).

### Modifié

- Les rhumbs sont moins nombreux et tracés comme à la main (réglages `variation_longueur`, `irregularite`,
  `lignes_manquantes` et `graine`) : angle un peu inégal, longueur et intensité variables, quelques lignes absentes.
  Les roses du cercle tracent 16 directions au lieu de 32 ; dix réseaux, plus grands, au lieu de onze. Chaque droite
  n'est tracée qu'une fois : une corde est commune à deux roses, un diamètre aux deux roses opposées et à la rose
  centrale, et deux droites presque confondues de réseaux voisins n'en font qu'une (réglage `ecart_rhumbs`).
- Plus de noms de ports (`rang_max_ports_detail` passe à 9), les petits un peu plus petits.
- Les lignes de rhumb sont des droites qui traversent toute la carte, comme sur les portulans (réglage `portee` :
  `None` par défaut ; un nombre les arrête à tant de rayons). Trois réseaux par défaut au lieu de dix : celui de la
  Méditerranée et les deux grands cercles du planisphère de Cantino (1502), centrés sur les îles du Cap-Vert et sur
  l'Inde, qui se touchent en Afrique ; une rose marque tout point commun à deux cercles.
- Les côtes sont le contour des terres elles-mêmes (couche `ne_10m_land`, détaillée dans la zone de détail, simplifiée
  ailleurs) : le trait et le remplissage se superposent exactement. Les couches `ne_50m_land`, `ne_10m_coastline` et
  `ne_50m_coastline` ne servent plus ; les réglages `couche_cotes_detail`, `couche_cotes_monde` et `taille_min_cote`
  disparaissent (nouveau : `taille_min_terre_detail`). Là où la carte coupe une terre (72° S, ±180°), aucun trait.
- Terres, côtes et lacs sont découpés en cases de 10° (réglage `case_terres`), un tracé par case : le navigateur ne
  dessine plus que les cases à l'écran. Une vue régionale se redessine environ dix fois plus vite.
- Les paliers des noms se montrent et se cachent par `display` (`--noms-p0`… valent `inline` ou `none`, au lieu de
  `visible` ou `hidden`) : un palier caché n'est plus mis en page. La variable est posée sur chaque nom et chaque
  château, et non plus sur un groupe par palier.
- La grande rose est gravée à l'encre : deux couleurs, branches hachurées, anneau gradué, noms des vents en
  toutes lettres. Nouvelles variables CSS `--rose-encre` et `--rose-papier` ; `--rose-3` et `--rose-4` ne servent
  plus, `--rose-2` ne sert plus qu'aux petites roses du réseau.

### Corrigé

- Les attributs complétés par des octets nuls (couche des pays en 1/10 000 000) sont lus sans ces octets.

## [0.1.0] - 2026-09-28

### Ajouté

- Première version : carte du monde à la manière des portulans, en SVG, d'après Natural Earth.
- Terres, côtes (détaillées dans une zone au choix), grands lacs.
- Noms des ports perpendiculaires à la côte, en deux niveaux d'importance.
- Réseaux de lignes de rhumb (32 vents autour de 16 roses sur un cercle), en trois encres.
- Petites roses aux nœuds du réseau et grandes roses ornées.
- Couleurs et épaisseurs en variables CSS.
- Ligne de commande `carte-portulan`, réglages en JSON, page d'aperçu autonome, exemple de page avec parallaxe.
- Lecture de Natural Earth sans dépendance : archive complète, couches zippées ou décompressées.
