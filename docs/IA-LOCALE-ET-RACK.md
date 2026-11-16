# IA locale et rack MU-TH-UR

Le point d'entrée `superia-local.target` regroupe les trois unités nécessaires
au chat local raccordé au rack : `ollama.service`, `superia-web.service` et
`veille-azoth.service`. Le drop-in `veille-azoth.service.d/superia-local.conf`
fait suivre les redémarrages et arrêts du target à la veille. Les unités
existantes gardent leurs propres fichiers et paramètres; aucun secret n'est
recopié dans cette configuration.

## Installation utilisateur

Depuis la racine de ce dépôt :

```bash
install -D -m 0644 config/systemd/superia-local.target \
  "$HOME/.config/systemd/user/superia-local.target"
install -D -m 0644 config/systemd/veille-azoth.service.d/superia-local.conf \
  "$HOME/.config/systemd/user/veille-azoth.service.d/superia-local.conf"
systemctl --user daemon-reload
systemctl --user enable --now superia-local.target
```

Après une mise à jour du code :

```bash
systemctl --user restart superia-local.target
systemctl --user status superia-local.target ollama.service superia-web.service veille-azoth.service --no-pager
```

Le target démarre le pont de rack hébergé par la veille sur le port local
`8765`. Le chat Super IA l'appelle uniquement pour les capacités explicitement
autorisées en lecture seule. Le target n'installe pas Ollama, Super IA, leurs
modèles ou leurs unités de service.

## Vérification IA et outils

Depuis le dépôt Super IA :

```bash
npm run build
npm run diagnose:chat
```

Le diagnostic vérifie chaque modèle détecté : texte conforme au marqueur,
appel à l'outil local `list_files` et appels rack `mother_list_models`,
`mother_search_articles` et `mother_trading_status`. Il échoue si la sortie
n'est que du raisonnement/brouillon, si un outil ne s'exécute pas ou si le pont
rack n'est pas joignable. Pour comparer le mode rapide :

```bash
SUPERIA_TEST_THINK=0 npm run diagnose:chat
```

Le chat utilise un contexte local de 8 192 tokens, un budget de sortie initial
de 2 048 et le profil Qwen3 0,6 avec raisonnement / 0,7 sans. Une seule IA doit
rester chargée à la fois sur la machine observée; vérifier `/api/ps` avant de
modifier ces limites. Les résultats de test fonctionnel ne remplacent pas une
évaluation de qualité sur les tâches réelles.

Les appels rack restent read-only : inventaire Ollama, recherche dans les
articles déjà en cache, état de santé Quant Core. Aucun appel ne lit de compte
de trading, ne passe d'ordre, ne rafraîchit de flux, n'écrit dans Obsidian ou
n'exécute de commande système.

Depuis le 16 novembre 2026, le chat local dispose en plus d'un catalogue d'outils
documenté dans Super IA (`docs/WEB.md`, section « Outils du chat local ») :
recherche dans le workspace et le coffre (`search_files`, `vault_search`),
`workspace_stats`, `get_datetime`, `calc` (bac à sable), `system_info` (lecture
seule), `web_search`/`web_fetch` (Internet en lecture seule, anti-SSRF) et
`inbox_save` (seule écriture : brouillon inédit dans `Inbox/`, jamais
d'écrasement). Aucun outil shell n'est exposé aux modèles.
