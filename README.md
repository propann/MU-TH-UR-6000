# MU-TH-UR 6000 — Mother

> Cockpit personnel souverain pour l'IA locale, la connaissance, la veille et
> le trading simulé.

```text
╔══════════════════════════════════════════════════════════════╗
║  MOTHER // UNE PORTE · DES SERVICES ISOLÉS · ZÉRO SECRET    ║
╚══════════════════════════════════════════════════════════════╝
```

MU-TH-UR 6000, surnommé Mother comme l'ordinateur du Nostromo dans *Alien*,
rassemble les interfaces et procédures d'exploitation du poste. Le cockpit est
la porte d'entrée et Obsidian la mémoire durable. MU-TH-UR est le dépôt de
référence; des composants restent actuellement dans leurs propres dépôts et
leur intégration ou migration est suivie dans le plan de mise en route.

## Vue d'ensemble

| Module | Rôle | État |
|---|---|---|
| MU-TH-UR 6000 | cockpit et veille technologique | installé, recette à terminer |
| Super IA | chat Ollama/Mistral et contexte Obsidian | intégré, durcissement à terminer |
| Quant Core | Freqtrade et console de trading | `dry-run`, recette séparée |
| SuperIA-Vault | source documentaire officielle | éditable par l'utilisateur; brouillons IA dans `Inbox/` |

```text
Navigateur LAN
      │
      ▼
MU-TH-UR 6000 ── authentification unique
      ├── /ia/ ────── Super IA ────── Ollama local
      │                   └────────── Obsidian à la demande
      ├── /quant/ ── Quant Core ───── Freqtrade dry-run
      └── / ───────── Veille ───────── flux RSS
```

## Captures

Les captures destinées à la vitrine sont gérées dans
[`docs/captures/`](docs/captures/README.md). Elles doivent être relues avant
publication afin d'écarter adresse privée, nom de note, clé, solde ou donnée de
trading personnelle.

| Interface | Chemin public | Capture attendue |
|---|---|---|
| Cockpit | `/` | `docs/captures/cockpit.png` |
| IA locale | `/ia/` | `docs/captures/ia-locale.png` |
| Trading simulé | `/quant/` | `docs/captures/quant-core.png` |

## Sécurité par défaut

- aucun `.env`, jeton, mot de passe ou identifiant Drive dans Git ;
- Ollama, Super IA et Quant Core liés à `127.0.0.1` ;
- seul le cockpit authentifié est destiné au LAN ;
- l'installation Pi utilise Basic Auth sur HTTP sans TLS : rester sur un réseau
  de confiance ou passer par un VPN; ne pas publier le port sur Internet ;
- Freqtrade reste en `dry-run`, sans clé d'exchange ;
- l'IA n'active pas le trading et ne place aucun ordre ;
- les modèles locaux partagent le même catalogue d'outils, dont le périmètre doit être durci ;
- l'utilisateur édite librement Obsidian; l'IA ne crée que des brouillons dans `Inbox/` ;
- le contexte Obsidian vers Mistral doit devenir un opt-in réel; l'interface
  actuelle coche l'option par défaut, correction requise avant mise en route.

## Composants verrouillés

MU-TH-UR est le dépôt de référence du projet. Certains composants restent
actuellement dans leurs propres dépôts; leur intégration ou migration est
suivie dans le [plan de mise en route](docs/PLAN-MISE-EN-ROUTE.md). Les
références connues figurent dans [`config/services.yaml`](config/services.yaml).

| Composant | Dépôt | Branche de livraison |
|---|---|---|
| MU-TH-UR 6000 / Mother | `propann/MU-TH-UR-6000` | `main` |
| Super IA | `propann/super-ia` | `fix/lan-token-login` |
| Quant Core | `propann/freqtrade` | `rebuild/engine-optional` |

## Démarrage et contrôle

```bash
systemctl --user start azoth.target
bash scripts/verifier-azoth-actif.sh
bash scripts/tester-ia-locale.sh
```

Les tâches de préparation sont idempotentes et documentées dans `scripts/`.
Ne jamais démarrer tous les laboratoires pour un simple contrôle documentaire.

Tests unitaires du registre RACK (bibliothèque standard Python) :

```bash
python3 -m unittest discover -s tests -v
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Rack logiciel Mother](docs/RACK-LOGICIEL.md)
- [Plan de mise en route](docs/PLAN-MISE-EN-ROUTE.md)
- [Trame graphique MU-TH-UR](docs/DESIGN-SYSTEM.md)
- [Audit de la Veille et étude Mistral](docs/AUDIT-VEILLE-MISTRAL.md)
- [Assistant Mistral transversal](docs/ASSISTANT-OVERLAY.md)
- [Liaison Mistral et Obsidian](docs/MISTRAL-OBSIDIAN.md)
- [État du déploiement](docs/DEPLOIEMENT.md)
- [IA et Obsidian](docs/IA-OBSIDIAN.md)
- [Incident IA du 12 novembre](docs/INCIDENT-IA-2026-11-12.md)
- [Interface unifiée](docs/INTERFACE.md)
- [Réseau local](docs/RESEAU-LOCAL.md)
- [Audit Git et poste de développement](docs/AUDIT-GIT-ET-DEV.md)

## Règle d'or

Le dépôt contient la structure reproductible et les décisions. Les données
runtime, journaux, modèles, coffres, sauvegardes et identifiants restent hors
Git.
