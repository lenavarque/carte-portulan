# Contribuer

Merci de votre intérêt ! Les remarques, les corrections et les idées sont bienvenues.

## Signaler un problème ou proposer une idée

Ouvrez une [issue](https://github.com/lenavarque/carte-portulan/issues) en décrivant :

- ce que vous avez fait (commande, réglages, version de Python et de Natural Earth) ;
- ce qui s'est passé, et ce que vous attendiez ;
- si possible, une capture de la carte.

Pour une erreur géographique (un port mal placé, un nom erroné), indiquez la ville et la zone concernées : les noms
viennent de Natural Earth, mais leur choix et leur placement viennent de ce programme.

## Proposer une modification

1. Créez une branche à partir de `main`.
2. Faites votre modification, avec un test si elle change le comportement.
3. Vérifiez que les tests passent :

   ```bash
   python -m unittest discover -s tests -v
   ```

4. Notez le changement dans la section « Non publié » de [CHANGELOG.md](CHANGELOG.md).
5. Ouvrez une *pull request* qui explique le pourquoi du changement.

## Conventions

- **Aucune dépendance** : le programme n'utilise que la bibliothèque standard de Python (3.10 et plus récent).
- Le code, les commentaires et la documentation sont **en français**, noms de variables compris.
- Style : [PEP 8](https://peps.python.org/pep-0008/), lignes de 120 caractères au plus, annotations de type sur les
  fonctions publiques, une docstring pour chaque module et chaque fonction qui n'est pas évidente.
- Les distances des réglages sont en degrés ; à l'intérieur, la carte compte en centièmes de degré
  (`projection.UNITES`).
- Toute nouvelle couleur passe par une variable CSS, documentée dans le README.

## Code de conduite

Ce projet suit un [code de conduite](CODE_OF_CONDUCT.md) : en y participant, vous vous engagez à le respecter.
