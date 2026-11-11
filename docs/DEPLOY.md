# Déployer MU-TH-UR

Depuis la racine clonée avec ses sous-modules :

```bash
bash scripts/deployer.sh
```

Le script vérifie Git, Python, Docker et Compose, initialise les sous-modules, prépare `.env` en permissions `0600`, reprend le cache et les préférences de l'ancien portail, réutilise le coffre local Super IA, construit les interfaces, arrête les anciennes unités systemd et la pile Compose Quant sans supprimer leurs volumes, puis démarre Ollama, le montage Obsidian, le cockpit et la console Quant.

Il ne télécharge pas de poids Ollama et ne démarre pas le moteur Freqtrade. L’adresse d’accès locale est `http://127.0.0.1:8765`; depuis un autre appareil du même réseau, utiliser l’adresse LAN de la machine. Le pare-feu doit autoriser uniquement ce sous-réseau.

## Démarrage explicite du moteur

La console démarre sans le moteur. Après avoir vérifié la configuration et confirmé le mode dry-run :

```bash
docker compose --env-file .env -f components/freqtrade/docker-compose.coolify.yml \
  --profile trading-engine up -d
```

Arrêter le moteur :

```bash
docker compose --env-file .env -f components/freqtrade/docker-compose.coolify.yml \
  --profile trading-engine stop freqtrade-engine rack-agent
```

## Arrêter et relancer le cockpit

```bash
docker compose --env-file .env -f components/freqtrade/docker-compose.coolify.yml down
docker compose --env-file .env -f compose.yaml down
docker compose --env-file .env -f components/freqtrade/docker-compose.coolify.yml up -d trading-terminal
docker compose --env-file .env -f compose.yaml up -d
```

L’arrêt du cockpit ne supprime pas ses volumes. Ne pas ajouter `--volumes` si tu veux conserver l’état, la configuration, le coffre IA et les données du bot. L’engine et le rack ne sont pas démarrés par ces commandes.

## Mot de passe du portail

À la première installation, le mot de passe est généré dans `.env` et recopié dans `.muthur-first-password`. Les deux fichiers sont privés, ignorés par Git et créés en mode `0600`. Après l’avoir enregistré dans un gestionnaire de mots de passe, supprimer le fichier de première installation ; la valeur de `.env` reste la référence.
