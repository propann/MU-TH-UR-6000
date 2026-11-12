# Plan de mise en route de Mother

Dernière revue documentaire : 12 novembre 2026. Ce plan sépare les faits
observés, les corrections nécessaires et les validations restant à faire. Une
case cochée demande une preuve reproductible, pas seulement un service `active`.

## État de départ

- [x] Le dépôt de livraison canonique est `propann/MU-TH-UR-6000`, branche
  `main`; le checkout local est `~/serveur-local/sources/veille-azoth`.
- [x] Ollama expose les deux modèles locaux attendus et le chat renvoie des
  réponses quand le flux fournit des événements `delta` puis `done`.
- [x] Avec le raisonnement activé, le diagnostic fourni par l'opérateur a
  obtenu une réponse et un appel `list_files` réussi pour les deux modèles.
- [ ] La variante `SUPERIA_TEST_THINK=0` n'est pas validée : le modèle
  Abliterated a rendu son raisonnement interne au lieu du texte demandé, et le
  diagnostic global a échoué. Garder le raisonnement activé par défaut jusqu'à
  une recette dédiée.
- [x] Le service systemd `azoth.target` regroupe le cockpit, Ollama, Super IA,
  le coffre et Quant Core dans sa configuration utilisateur observée.
- [ ] La machine était également configurée avec `superia-local.target` activé.
  Clarifier le point d'entrée documenté. Un `restart` d'un target systemd ne
  redémarre pas nécessairement ses unités déjà actives.
- [x] Obsidian est éditable par l'utilisateur; les brouillons IA sont créés
  exclusivement dans le montage `Inbox` avec création sans écrasement.
- [x] Le manifeste `config/rack.json` est chargé par `GET /api/rack`, affiché
  dans le cockpit et enrichi de sondes runtime pour les services supervisés;
  les autres modules restent « non sondés » et aucune capacité n'est routée.

## P0 — avant toute mise en service fiable

- [ ] **Fixer un seul point d'entrée opérateur.** Décider si `azoth.target` est
  la commande normale de démarrage complet. Documenter une commande de
  redémarrage qui redémarre réellement Ollama et Super IA, et vérifier les
  dépendances `Requires/Wants`, `After`, `WantedBy`, le lingering et le démarrage
  après fermeture de session puis après reboot.
- [ ] **Recette service après reboot.** Vérifier `systemctl --user is-active`
  des unités, `/api/version` Ollama, `/api/tags`, `/healthz` Super IA, la liste
  `/api/chat/models`, le proxy cockpit `/ia/` et l'état du montage Obsidian.
  Noter les horodatages et les versions effectives.
- [ ] **Valider les flux depuis le poste de production.** Les erreurs Reddit
  `429`, DPReview `403` et le délai Codeberg ont été observés le 12 novembre
  2026; retester après modification des délais et conserver les anciens articles
  en cas de panne. Les six entrées Reddit ont déjà un TTL d'une heure; le bouton
  de forçage a été aligné sur ce TTL pour éviter qu'il ne relance ces flux toutes
  les cinq minutes. Les résultats réseau dépendent de l'IP et de l'heure.
- [x] Le vérificateur actif accepte le fichier de mot de passe utilisateur, un
  chemin explicite via `VEILLE_PASSWORD_FILE`, ou le fichier système Pi
  `/etc/veille-azoth.env` lorsqu'il est lisible.
- [ ] **Sécuriser les outils de fichiers avant de les appeler un éditeur.** Le
  code actuellement présent dans le worktree Super IA base les chemins sur
  `process.cwd()` (le dépôt Super IA du service), autorise `write_file` avec
  remplacement (`flag: w`) et doit encore être revu pour le chemin final en cas
  de lien symbolique. L'unité systemd actuelle protège le home en lecture seule
  et n'autorise l'écriture que dans le coffre Super IA et Inbox : la capacité
  d'écriture dans le dépôt n'est pas validée et peut être refusée par systemd.
  Définir des workspaces enregistrés, résoudre les chemins
  canoniques, refuser tout lien sortant, bloquer secrets et données runtime,
  utiliser création atomique ou aperçu/diff confirmé pour les modifications.
- [ ] **Aligner la livraison du backend IA.** Le service tourne depuis
  `~/serveur-local/worktrees/super-ia-lan-auth`, qui contient des changements
  non commités distincts du HEAD de son dépôt. Décider quelles sources relèvent
  de MU-TH-UR et intégrer/versionner le backend dans la destination convenue
  avant de déclarer une release reproductible. Ne pas confondre le checkout
  exécuté, le HEAD publié et les fichiers non commités.
- [ ] **Consolider le projet dans ce dépôt.** Le dépôt MU-TH-UR est la destination
  canonique demandée. Préparer la migration du code Super IA et des composants
  retenus avec historique, licences, documentation et scripts de déploiement;
  retirer ensuite les références de livraison aux anciens dépôts seulement
  quand le build depuis MU-TH-UR remplace réellement leurs services.
- [ ] **Vérifier la confidentialité Obsidian.** Dans l'interface actuelle, la
  case `Utiliser Obsidian` est initialement cochée dans le code observé; elle
  doit être décochée par défaut et rester un opt-in clair, en particulier avec
  Mistral. Vérifier séparément le backend réellement chargé : le HEAD Super IA
  accepte les extraits pour le fournisseur choisi, tandis que le worktree
  exécuté contient une modification locale qui limite ces extraits à Ollama.
  Choisir explicitement la politique et la tester sans envoyer de note privée.
- [ ] **Recette qualité par modèle et paramètres.** Pour chaque modèle, exécuter
  instruction, calcul, contexte synthétique et appel outil avec raisonnement
  activé. Tester le mode sans raisonnement séparément, vérifier l'absence de
  fuite de `thinking`, le texte final, les erreurs, les appels et leur résultat.
  Garder le diagnostic hors du coffre personnel.
- [ ] **Tester les fonctions Obsidian.** Édition manuelle, recherche et citation,
  création Inbox, conflit de nom, panne rclone, redémarrage et démontage propre.
  Ne jamais synchroniser deux écritures concurrentes sans résoudre le conflit.

## P1 — rack exploitable

- [ ] Valider le schéma et les identifiants de capacités du manifeste avec les
  API/routes réellement disponibles.
- [ ] Implémenter un registre chargé par Mother avec métadonnées uniformes :
  module, capacité, ressource autorisée, schéma d'entrée, permission, résultat
  et erreur normalisés.
- [ ] Ajouter un adaptateur Obsidian limité à rechercher/lire du contexte et
  créer un brouillon Inbox; afficher sources et reçus d'outil.
- [ ] Décider si MCP est nécessaire après extraction de ces fonctions dans un
  service partagé. Si oui, intégrer serveur **et** client; MCP seul ne raccorde
  pas le chat.
- [ ] Raccorder la traduction d'articles comme capacité distincte : choix du
  fournisseur, coût, opt-in distant, sortie enregistrée en brouillon, citation
  du lien d'origine et approbation humaine avant publication.
- [ ] Ajouter des journaux d'outils sans contenu de note, secrets, prompts
  complets ou données personnelles.

## P1 — sécurité, réseau et reprise

- [ ] Auditer les ports : seules les routes prévues du cockpit sont accessibles
  depuis le LAN; Ollama, Super IA et Quant Core restent liés à localhost.
- [ ] Vérifier l'authentification du cockpit et du proxy depuis un autre appareil
  du réseau, sans exposer les ports internes.
- [ ] Confirmer l'état du pare-feu, de la réservation DHCP et du câble Ethernet
  avant de remplacer le Wi-Fi.
- [ ] Faire l'inventaire des secrets hors Git et exécuter le scan de secrets avant
  publication; contrôler aussi captures, journaux et exemples de configuration.
- [ ] Documenter les sauvegardes des configurations et bases, puis faire une
  restauration réelle vers un emplacement temporaire.
- [ ] Quant : rester en `dry-run`; faire valider santé et isolation après reboot.
  Aucune clé exchange ni capacité d'ordre IA ne doit apparaître dans le rack.

## P2 — présentation et publication

- [ ] Capturer cockpit, IA et Quant Core après recette; masquer nom d'utilisateur,
  adresses privées, notes, tokens, soldes et données personnelles.
- [ ] Comparer les docs au commit et aux routes réellement déployés; déplacer les
  visions futures dans des sections « cible » et les faits non vérifiés dans
  « à confirmer ».
- [ ] Vérifier le diff, les liens et le YAML; lancer les validations propres à
  chaque composant depuis son dépôt/worktree de livraison.
- [ ] Faire une revue humaine des changements sensibles, puis commit/push
  uniquement vers `propann/MU-TH-UR-6000` après contrôle du diff et des secrets.

## Critère de mise en route

La mise en route est validée lorsque le démarrage complet après reboot est
reproductible, les contrôles IA passent pour les deux modèles dans le mode
retenu, Obsidian reste éditable avec conflits maîtrisés, les outils de fichiers
sont confinés et leur portée est visible, l'accès LAN est authentifié, les
sauvegardes ont été restaurées en essai et aucun secret n'est dans Git. Le rack
peut rester un manifeste statique tant que son état est clairement affiché.
