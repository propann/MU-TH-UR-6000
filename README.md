# MU-TH-UR 6000

**Le cockpit personnel qui réunit actualités techniques, IA, mémoire Obsidian et Quant Core.**

MU-TH-UR rassemble dans une seule interface les outils qui tournent sur la machine : flux techniques filtrables, modèles Ollama, modèles Mistral, notes Obsidian et console graphique du bot. Le cockpit sert de porte d’entrée au réseau local. Les composants gardent leurs données et leurs fonctions dans leurs propres espaces.

> Projet personnel en développement. Le trading réel n’est pas activé par défaut. Aucun ordre réel ne doit être passé avant validation explicite de la configuration et des protections.

## Le cockpit

| Module | Fonction |
|---|---|
| **Actualités** | Flux RSS/Atom, alertes, versions, favoris, filtres, export OPML et synthèse Markdown. |
| **IA** | Chat avec les modèles locaux Ollama ou les modèles Mistral accessibles par la clé configurée. Les réponses s’affichent progressivement. |
| **Mémoire** | Recherche dans le coffre Obsidian et rédaction de brouillons dans l’Inbox dédiée. Le coffre reste monté depuis la machine et n’est pas copié dans le dépôt. |
| **Quant Core** | Console graphique pour consulter et préparer le bot Freqtrade. L’interface reste disponible quand le moteur est arrêté. Le moteur se lance séparément, en dry-run par défaut. |

Les sous-chemins `/ia/` et `/quant/` sont relayés par MU-TH-UR après le contrôle d’accès du cockpit. Ollama, Super IA, Freqtrade et le coffre Obsidian restent des composants distincts afin de conserver leurs mises à jour et leurs sauvegardes propres.

## Architecture

Voir [l'architecture détaillée](docs/ARCHITECTURE.md), la [politique de sécurité](docs/SECURITY.md) et le [guide opérateur](docs/DEPLOY.md).

```text
Navigateur du réseau local
          │
          ▼
MU-TH-UR 6000 — porte d’entrée authentifiée
  ├── Actualités — flux publics et préférences locales
  ├── /ia/     ── Super IA ── Ollama local / Mistral API
  │                           └── Obsidian : coffre en lecture, Inbox en écriture
  └── /quant/  ── Console Quant Core ── Freqtrade (moteur optionnel)
```

## Déploiement

Le point d’entrée prévu est une seule commande après récupération du projet :

```bash
bash scripts/deployer.sh
```

Le déploiement prépare les composants, crée les fichiers de configuration privés s’ils manquent, démarre le cockpit et les interfaces, puis affiche l’adresse locale. Il ne télécharge aucun modèle, ne demande pas de clé API dans un terminal et ne démarre pas le moteur de trading réel.

**Prérequis machine :** Docker avec Compose, Ollama et les modèles déjà choisis, Node.js 22+, ainsi que le montage Obsidian si la mémoire documentaire est souhaitée. Une clé Mistral se configure ensuite depuis l’interface et reste chiffrée localement.

La commande unique sera vérifiée sur une installation fraîche avant sa première publication. Les secrets restent dans des fichiers locaux ignorés par Git, les modèles dans le stockage Ollama, les données du bot dans ses volumes privés, et le coffre Obsidian dans son montage local.

## Sécurité et données

- Le cockpit est destiné au réseau local et exige un mot de passe à l’entrée.
- Les services internes ne sont pas publiés directement sur le réseau.
- Les clés API ne sont jamais écrites dans le dépôt. La clé Mistral est enregistrée dans le coffre chiffré de Super IA.
- Les clés d’exchange, de messagerie et les mots de passe restent dans des fichiers locaux protégés ou dans les coffres de chaque composant.
- Le coffre Obsidian et l’Inbox ne sont ni copiés ni indexés par Git.
- Les états, historiques, journaux, modèles, bases de données et sauvegardes sont exclus du suivi Git.
- Le moteur Freqtrade reste en **dry-run**. Son démarrage est séparé de celui de la console.

Avant chaque publication : contrôle des fichiers suivis, recherche de secrets avec Gitleaks, inspection des changements, puis vérification du commit et de l’arborescence cible.

## Personnaliser les flux

Les flux de base couvrent la cybersécurité, l’infrastructure, l’IA, le matériel et les marchés. La configuration locale peut être enrichie depuis l’interface. Les choix personnels de flux et de sujets restent dans l’état local et ne sont pas intégrés au dépôt.

## État du projet

Le dépôt est en cours de reconstruction autour du cockpit complet. La page d’accueil et les modules de flux constituent la base existante. La commande unique, l’isolation des secrets et le démarrage séparé du moteur sont préparés sur une branche afin d’être examinés avant toute migration sur `main`.

Les changements sont préparés sur une branche et proposés en revue ; aucune fusion automatique vers `main` n’est effectuée.
