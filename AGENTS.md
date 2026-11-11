# Consignes du dépôt MU-TH-UR

- Ne jamais pousser directement sur `main`; préparer une branche et une revue.
- Les clés, fichiers `.env`, données de coffre, modèles, journaux, bases et sauvegardes restent hors Git.
- Conserver Super IA et Freqtrade en sous-modules épinglés; ne pas recopier leur source ici.
- Garder la console Quant disponible sans moteur Freqtrade. Le moteur reste dans le profil explicite `trading-engine` et en dry-run.
- Le déploiement standard n’active aucune clé exchange, aucun compte et aucun ordre réel.
- Vérifier `git status`, Gitleaks, YAML/Compose et les chemins de volumes avant toute publication.
- Ne jamais publier les fichiers de runtime ou des chemins locaux contenant un nom de compte.
