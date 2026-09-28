# Journal des versions

Les changements notables de ce projet sont notés ici. Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et les numéros de version suivent le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté

- Rose centrale (groupe `rose-centrale`, réglage `rose_centrale`) : une grande rose au centre du réseau de rhumbs
  de la Méditerranée, d'où partent les lignes.
- Démonstration en ligne sur GitHub Pages : la carte en plein écran, à déplacer et zoomer, avec des vues prêtes,
  des couches à masquer et la vue gardée dans l'adresse. Générée et publiée par un workflow à chaque envoi.

### Modifié

- La grande rose est gravée à l'encre : deux couleurs, branches hachurées, anneau gradué, noms des vents en
  toutes lettres. Nouvelles variables CSS `--rose-encre` et `--rose-papier` ; `--rose-3` et `--rose-4` ne servent
  plus, `--rose-2` ne sert plus qu'aux petites roses du réseau.

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
