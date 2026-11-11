# Architecture du cockpit

MU-TH-UR est le point d’entrée. Il réunit les interfaces et laisse les services spécialisés responsables de leurs données.

| Service | Accès hôte | Rôle | Démarrage par défaut |
|---|---:|---|---|
| MU-TH-UR | `8765` | Porte d’entrée, flux et relais HTTP authentifié | Oui |
| Super IA | `3210` sur loopback | Chat, modèles, configuration des fournisseurs et accès Obsidian | Oui |
| Quant Core UI | `3000` sur loopback | Préparer et superviser le bot | Oui |
| Freqtrade engine | aucun port hôte | Moteur de trading, réseau Compose interne | Non, profil `trading-engine` |
| Rack Agent | aucun port hôte | Opérations contrôlées du bot | Non, profil `trading-engine` |
| Ollama | `11434` sur loopback | Modèles locaux existants | Service hôte, aucun modèle téléchargé par le déploiement |

```text
Navigateur ── mot de passe ── MU-TH-UR:8765
                                  ├── /ia/ ── Super IA:3210 ── Ollama:11434
                                  │                       └── coffre Obsidian monté
                                  └── /quant/ ── Quant UI:3000 ── Freqtrade (optionnel)
```

MU-TH-UR et Super IA utilisent le réseau hôte Linux pour accéder aux services déjà installés. Ils n’écoutent que sur les ports prévus ; seul MU-TH-UR est destiné au réseau local. Quant UI est publié sur `127.0.0.1`; Freqtrade et Rack Agent ne publient aucun port hôte.

Les composants Super IA et Freqtrade sont des sous-modules publics, épinglés à des commits. Le dépôt principal garde l’orchestration, l’interface d’accueil et la documentation.
