# Audit Git et poste de développement

Audit initial du 11 novembre 2026 : 27 dépôts GitHub accessibles. Pour
l'instant, les sources applicatives prévues ne sont pas encore clonées ici.

## Dépôts prioritaires

| Domaine | Dépôts | Usage |
|---|---|---|
| Trading | `propann/freqtrade` | Quant Core, backtests, dry-run |
| IA | `propann/super-ia`, `propann/MU-TH-UR-6000` | agents, mémoire, cockpit IA |
| Archive seulement | `propann/Az-N8N` | ancien starter n8n, hors déploiement |
| Meshtastic/LoRa | `propann/LoRaZ-Family-Ops`, `propann/Adopte-un-Mesh` | nœuds, messages, cartographie |
| ESP32 | `propann/azothesp32cam`, `propann/Engineering-Studio` | firmware et atelier électronique |
| Raspberry Pi | `propann/azoth-pi-photo` | nœud photo réseau |
| Gros projets | `propann/Az-1`, `propann/L-AZ-2`, `propann/TerraCraft` | auditer avant clonage complet |

Les gros dépôts ne doivent pas être récupérés automatiquement avant examen des
fichiers volumineux et de leur utilité réelle.

## Outils présents

Git, Docker, Python 3, SSH, rsync, rclone, Ollama et NVIDIA.

## Outils manquants constatés

- Node.js/npm et VS Code ou VSCodium ;
- `pipx` et `uv` ;
- PlatformIO, Arduino CLI et outils série ;
- Meshtastic CLI et Mosquitto/MQTT ;
- ADB pour Android ;
- Compose, Git LFS, pre-commit, ShellCheck, jq/yq ;
- btop, nvtop, smartmontools et lm-sensors.

Le poste final réunira cinq profils : socle développement, IA, embarqué ESP32,
Meshtastic/LoRa et exploitation des services du LAN. Chaque installation devra
être reproductible et ne jamais contenir de secret dans Git.

## Audit des sources récupérées

Les trois sources sont rattachées et propres aux commits suivants :

- `freqtrade` : `3f5db229980ddcf28b7742d182e5000fc97e2a59` ;
- `super-ia` : `8f8407bee5bdcb188586ace05bcfc16574c8db8c` ;
- `Az-N8N` : `8c742a18d23e2715a28cf854cd5b0fc27474b992`.

`Az-N8N` est conservé uniquement comme archive locale. Son audit n'a trouvé
aucun workflow de veille à reprendre ; il ne fait plus partie du déploiement.

Aucun secret réel évident n'est suivi dans ces dépôts. Les correspondances
trouvées sont des `.env.example`, des générateurs, des tests et le code de
gestion des secrets. Aucun `.env` opérationnel ne doit être créé avant la
validation de chaque service.

### Contraintes constatées

- Super IA exige Node.js 22.5 ou supérieur ; Node.js est actuellement absent.
- Quant Core utilise Bun pour son développement local et Docker Compose pour la
  pile complète.
- Docker et Compose sont installés, mais la session `azoth` n'a pas encore accès
  au socket Docker ; groupe et reconnexion de session sont à corriger.
- La mémoire disponible suffit pour les contrôles, mais le lancement simultané
  d'Ollama, Freqtrade, de l'indexation Drive et des outils de développement devra être
  limité et surveillé sur les 16 Gio de RAM.
- Le disque dispose d'environ 794 Gio libres : aucune pression immédiate.

### Ports locaux prévus

| Service | Port | Exposition initiale |
|---|---:|---|
| Quant Core | 3000 | `127.0.0.1` |
| Super IA | 3210 | `127.0.0.1` |
| Ollama | 11434 | `127.0.0.1` |

Ces services restent privés. Le futur cockpit ou reverse proxy sera le seul
point d'entrée autorisé depuis le LAN.

## Ordre de mise en service

1. installer Node.js 22 LTS, Corepack/Bun et les outils Python isolés ;
2. corriger puis tester l'accès Docker sans `sudo` ;
3. exécuter les tests de Super IA, sans lancer son daemon ;
4. valider Quant Core et ne démarrer Freqtrade qu'en dry-run ;
5. mesurer RAM, GPU, ports et santé après chaque service ;
6. connecter en lecture seule le dossier Drive `Veille/` à l'index local ;
7. ajouter ensuite Meshtastic, PlatformIO et MQTT.

L'installation est orchestrée par `scripts/installer-socle-dev.sh`. Elle ne
démarre ni Super IA, ni Freqtrade et ne configure aucun compte. Une
reconnexion de session est nécessaire après l'ajout aux groupes `docker` et
`dialout`, puis `scripts/valider-socle-dev.sh` contrôle le résultat.
