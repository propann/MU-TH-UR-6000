# Historique des versions

## 3.0 — 09/11/2026 — Veille Azoth

- Renommage en **Veille Azoth**.
- **101 sources** testées, en deux familles d'onglets : **PRO** (alertes, cyber et piratage, systèmes, réseau, homelab, cloud, chiffrement) et **PERSO** (firmwares, maker, musique, photo, rétro et jeux, drones et radio, IA, crypto et trading, matos).
- Suivi d'Omarchy, Arch Linux News, Hyprland, Pop!_OS COSMIC et Fortinet PSIRT.
- **« Pour toi »** : badge et onglet pour les sujets personnels cités par des sources généralistes.
- **Dernières versions** : version actuelle de chaque firmware ou logiciel suivi (flux GitHub et Codeberg ; les « nightly » sont ignorées).
- Alertes plus justes : mots reconnus en entier, mots surveillés liés à un vrai sujet de sécurité, « manual intervention » pour Arch.
- Reddit interrogé l'un après l'autre et une fois par heure (anti-blocage).
- **Windows en un clic** : icône sur le Bureau et dans le menu Démarrer (`Installer-Raccourcis.bat`), lancement sans console, bouton ⏻ pour arrêter, journal dans `data/veille.log`.
- **Raspberry Pi** (préparé) : options `--host` et `--password`, service systemd durci, script `pi/install-pi.sh`.
- Documentation : `docs/Veille_Technologique_TSSR_Azoth` (méthode de veille TSSR et description de l'outil, en Word et PDF).

## 2.0 — 09/11/2026 — Veille TSSR

- Serveur local Python (`veille.py`) : collecte réelle des flux RSS et Atom, cache, API JSON, protection contre les requêtes d'autres sites.
- Interface MU-TH-UR / HAL 9000 / Matrix : alertes prioritaires, favoris, lus et nouveaux, recherche, raccourcis clavier, synthèse Markdown, export OPML.
- Cours BTC, XMR et DOGE (CoinGecko).

## 1.0 — 09/11/2026 — maquette

- Maquette statique initiale (liens écrits en dur), réalisée avec Codex.
