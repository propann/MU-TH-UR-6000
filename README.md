# AZOTH ULTIME

> Cockpit personnel souverain pour l'IA locale, la connaissance, la veille et
> le trading simulé.

```text
╔══════════════════════════════════════════════════════════════╗
║  MU-TH-UR // UNE PORTE · DES SERVICES ISOLÉS · ZÉRO SECRET  ║
╚══════════════════════════════════════════════════════════════╝
```

Azoth Ultime rassemble les interfaces et procédures d'exploitation d'un poste
personnel. Le cockpit est la porte d'entrée, Obsidian est la mémoire durable et
les composants restent des dépôts Git indépendants, verrouillés par commit.

## Vue d'ensemble

| Module | Rôle | État |
|---|---|---|
| MU-TH-UR 6000 | cockpit et veille technologique | opérationnel |
| Super IA | chat Ollama/Mistral et citations Obsidian | opérationnel |
| Quant Core | Freqtrade et console de trading | `dry-run` uniquement |
| SuperIA-Vault | source documentaire officielle | lecture seule + `Inbox/` |

```text
Navigateur LAN
      │
      ▼
MU-TH-UR 6000 ── authentification unique
      ├── /ia/ ────── Super IA ────── Ollama local
      │                   └────────── Obsidian en lecture
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
- Freqtrade reste en `dry-run`, sans clé d'exchange ;
- l'IA n'active pas le trading et ne place aucun ordre ;
- le coffre complet est lu, seul `Inbox/` accepte de nouveaux brouillons ;
- le modèle expérimental Abliterated n'obtient ni outil, ni coffre, ni secret.

## Composants verrouillés

Les sources ne sont pas copiées dans ce dépôt. Les références publiées sont
tenues dans [`config/services.yaml`](config/services.yaml) et expliquées dans
[`services/README.md`](services/README.md).

| Composant | Dépôt | Branche de livraison |
|---|---|---|
| MU-TH-UR 6000 / Azoth Ultime | `propann/MU-TH-UR-6000` | `main` |
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

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
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
