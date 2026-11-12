# État du déploiement

Dernière mise à jour : 12 novembre 2026.

## Opérationnel

- socle de développement validé sans point en attente ;
- Ollama `0.40.16` actif sur `127.0.0.1:11434` avec `qwen3:8b` ;
- Veille Azoth restaurée depuis Drive avec ses sources et son état utilisateur ;
- cockpit disponible sur `http://<adresse-lan>:8765` avec authentification ;
- service utilisateur `veille-azoth.service` activé au démarrage ;
- quatre modules visibles : Veille, Trading, IA locale et Cœur Obsidian.

## Quant Core

La configuration locale est préparée dans le dépôt `freqtrade` :

- secrets aléatoires dans `.env`, fichier ignoré par Git et limité au propriétaire ;
- aucune clé d'exchange ;
- choix de l'exchange reporté ; Binance fournit seulement les données publiques
  provisoires du dry-run et pourra être remplacé ;
- Telegram désactivé ;
- portefeuille simulé de 1 000 USDT ;
- mode spot et `dry_run: true` ;
- entrées forcées désactivées ;
- moteur Freqtrade accessible uniquement sur le réseau Docker ;
- console publiée uniquement sur `127.0.0.1:3000`.

Les profils `research`, `observe`, `operator` et `ai-execution` restent arrêtés
pendant la mise en service initiale.

### Validation du 11 novembre 2026

- images moteur, rack-agent et console construites sans erreur ;
- trois conteneurs actifs et console déclarée saine ;
- préflight : zéro échec, trois avertissements attendus ;
- moteur Freqtrade `2026.7` en état `RUNNING` ;
- journal explicite : `Dry run is enabled. All trades are simulated.` ;
- stratégie initiale : `QuantCoreBaseline`, période 15 minutes ;
- protections actives : délai, stoploss, drawdown maximal et faible profit ;
- console intégrée sous `/quant/` derrière le cockpit authentifié ;
- ports internes `8080` et `9191` toujours non publiés.

La console a ensuite été vérifiée `healthy` et sa route `/quant/api/health` a
répondu `200 OK`. Le cockpit la sonde via `QUANT_CORE_URL` ; cette
valeur devra être mise à jour après tout changement d'adresse du serveur.

### Sessions de bot

La cible prévoit plusieurs sessions indépendantes. La première instance sert de
référence et doit être validée avant duplication. Chaque session future aura :

- un identifiant et un nom explicites ;
- une stratégie et un profil Quant Rack propres ;
- un portefeuille dry-run, une base et des journaux séparés ;
- des limites CPU/RAM et un état de santé individuels ;
- aucun accès direct aux secrets d'une autre session.

Le cockpit agrégera leurs états sans leur donner le droit d'activer le trading
réel. La sélection et l'authentification de l'exchange resteront une opération
distincte, effectuée plus tard par l'opérateur.

## Modèles IA

Deux profils sont disponibles localement :

- principal stable : `qwen3:8b` ;
- laboratoire débridé :
  `hf.co/richardyoung/Qwen3-8B-Abliterated-GGUF:Q4_K_M`.

Les deux modèles ont été téléchargés et vérifiés par Ollama. Le modèle stable
est le choix par défaut. Le candidat Qwen 3.5 9B reste une évolution future et
n'est pas présenté comme installé.

Un seul grand modèle peut être chargé à la fois. Le laboratoire débridé ne
reçoit aucun outil, secret, accès au coffre, accès système ou accès trading.
Le modèle principal n'obtiendra un accès documentaire en lecture qu'après la
validation des citations et du montage Drive.

## Cœur documentaire

Voir aussi [IA-OBSIDIAN.md](IA-OBSIDIAN.md) pour l'architecture du chat, le
montage restreint d'`Inbox`, les vérifications et le retour arrière.

Le dossier Drive `SuperIA-Vault` reste la source officielle. Le chemin local
prévu est `/home/azoth/GoogleDrive/SuperIA-Vault`, monté en lecture seule avec
`serveur-local/connecter-cerveau.sh` après configuration interactive de rclone.

Drive contient deux dossiers homonymes. Le coffre actif retenu le 11 novembre
2026 est celui qui contient `.obsidian`, `Accueil SuperIA.md`,
`Reprise SuperIA et état du système.md` et les notes les plus récentes. L'autre
dossier reste intact et ne doit jamais être fusionné automatiquement.

Le coffre complet est monté en lecture seule. Un second montage indépendant,
`/home/azoth/GoogleDrive/SuperIA-Inbox`, cible uniquement le dossier Drive
`Inbox` en écriture : l'IA peut y créer des brouillons sans modifier ni écraser
les notes existantes. Le coffre ne doit contenir aucun secret ni donnée
d'exécution.

La façade Super IA est volontairement réduite à un chat. Ollama peut rechercher
les notes Markdown du miroir local et doit citer leur chemin. Le contexte
Obsidian est désactivé dès que Mistral est sélectionné : aucune note n'est
transmise à une API distante automatiquement. La clé Mistral se configure dans
la fenêtre du chat et reste chiffrée dans le coffre privé de Super IA.

## État des validations

- Quant Core construit et validé en `dry-run` ;
- moteur non publié et console reliée au cockpit sous `/quant/` ;
- chat local Ollama fonctionnel, sans outil système ni droit trading ;
- température limitée côté serveur après l'incident du 12 novembre ;
- recherche Obsidian locale avec citations et écriture limitée à `Inbox/` ;
- montage Drive et conservation du démarrage après redémarrage à surveiller.

## Retour arrière

- Veille : `systemctl --user disable --now veille-azoth.service` ;
- Quant Core : arrêter la pile sans supprimer ses volumes ;
- coffre : démonter le montage rclone sans modifier Drive ;
- ne jamais utiliser `docker compose down -v`, qui supprimerait les volumes.

## Démarrage automatique

Le target utilisateur `azoth.target` regroupe les services disponibles :

- `ollama.service` ;
- `veille-azoth.service` ;
- `azoth-quant.service`, qui attend Docker puis applique le Compose dry-run.
- `superia-web.service`, interface IA multi-fournisseurs sur le port `3210`.

## Porte d'entrée unique

Le cockpit `http://<adresse-lan>:8765` est la seule porte destinée au LAN.
Quant Core est publié sous `/quant/` et Super IA sous `/ia/` par la passerelle
authentifiée du cockpit. Leurs ports `3000` et `3210` restent liés à
`127.0.0.1` : ils ne constituent donc plus des portes accessibles depuis le LAN.

## Fournisseur Mistral

Super IA contient déjà le fournisseur Mistral officiel :

- endpoint `https://api.mistral.ai/v1` ;
- secret attendu `MISTRAL_API_KEY` ;
- modèle initial `mistral-large-latest` ;
- stockage chiffré AES-256-GCM dans `~/.superia/credentials/` ;
- interface protégée par token et session HttpOnly.

La clé doit être saisie depuis l'interface Super IA, jamais dans Git, une note,
un prompt ou la conversation d'assistance. L'intégration peut être configurée
sans lancer de requête payante. Tout appel distant futur exigera un budget et
devra signaler que les données quittent la machine.

Le maintien des services utilisateur au démarrage, avant toute connexion
graphique, exige le lingering systemd pour le compte `azoth`. Le coffre Drive
n'est pas inclus tant que rclone n'est pas autorisé et testé.

Commandes opérateur :

```bash
systemctl --user start azoth.target
bash ~/Projets/Azoth-Ultime/scripts/verifier-azoth-actif.sh
```
