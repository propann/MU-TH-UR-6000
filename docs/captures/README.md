# Captures d'écran

Les captures sont générées depuis la session graphique de l'hôte avec :

```bash
bash scripts/capturer-interfaces.sh
```

Fichiers attendus : `cockpit.png`, `ia-locale.png` et `quant-core.png`.

Avant toute indexation Git, ouvrir chaque image et vérifier qu'elle ne montre
aucune clé, aucun jeton, aucune adresse privée, aucun chemin de note personnel,
aucun solde et aucune donnée de trading réelle. Les PNG sont ignorés par défaut ;
après revue, les ajouter explicitement avec `git add -f docs/captures/*.png`.

Une capture de page de connexion ne doit jamais contenir un mot de passe
prérempli. Utiliser uniquement des données de démonstration ou un état vide.
