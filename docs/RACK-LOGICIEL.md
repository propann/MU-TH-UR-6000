# Rack logiciel MU-TH-UR 6000

Le rack est le plan de raccordement des logiciels de Mother. Il décrit ce
qu'un module fournit, les permissions nécessaires et le chemin d'une demande.
Le manifeste [`config/rack.json`](../config/rack.json) est chargé par l'API
`GET /api/rack` et affiché dans le cockpit. Il reste un registre de capacités et
d'états : il ne route pas encore les appels des modèles.

## Identité et objectifs

Le système s'appelle **MU-TH-UR 6000**. Son nom d'usage est **Mother**, en
référence à l'ordinateur du Nostromo dans *Alien*. Le dépôt de référence est
[`propann/MU-TH-UR-6000`](https://github.com/propann/MU-TH-UR-6000).

Le rack doit éviter les intégrations dupliquées : un logiciel fournit des
capacités stables, et le cockpit, le chat ou une automatisation les consomment
par un adaptateur commun. Une capacité décrit une action, un module son
implémentation, une ressource son périmètre et un profil un assemblage autorisé.

## Inventaire constaté

| Module | Capacités constatées/documentées | Limites |
|---|---|---|
| Ollama | lister et interroger les modèles locaux | un grand modèle chargé à la fois |
| Mistral | chat distant optionnel | fournisseur choisi manuellement; jauge locale de tokens non imposée par le serveur; contexte Obsidian à rendre opt-in réel |
| Outils workspace Super IA | `list_files`, `read_file`, `write_file` annoncés aux deux modèles locaux | périmètre = checkout Super IA; systemd monte le home en lecture seule et n'autorise l'écriture que dans le coffre Super IA et Inbox; l'écriture du workspace n'est donc pas validée |
| Obsidian | édition normale par l'utilisateur, recherche/récupération de contexte, création Inbox | brouillon exclusif dans `Inbox/`; le contexte Mistral dépend du code chargé et de l'état réel de la case |
| Veille | actualiser les flux et rechercher des articles | traduction IA à étudier, pas encore une capacité intégrée |
| Git | inspecter le dépôt | gestion de worktrees à raccorder au registre |
| Freqtrade | état consultable par le cockpit | `dry-run`; soumission d'ordre absente des outils IA |
| Az-N8N | référence d'anciens workflows | désactivé |
| MCP | étude d'architecture | aucun serveur/client MCP opérationnel déclaré |

Les noms de capacités détaillés figurent dans le manifeste. Les outils système
installés sur l'hôte ne deviennent pas automatiquement des outils IA. Un outil
doit être exposé par un adaptateur, limité à des ressources précises et testé.

## Trame cible

```text
Interface / chat / automatisation
              |
              v
     Registre Mother + permissions
              |
        Routeur de capacités
       /       |        \
   Ollama   Obsidian    Veille ...
              |
       résultat normalisé
```

Chaque appel devrait déclarer l'identifiant de capacité, le module, la portée,
les paramètres validés, le résultat, les erreurs et la durée. L'interface peut
ainsi montrer quel outil a été appelé et ce qu'il a réellement fait. Les
permissions sont évaluées côté serveur; le modèle ne choisit pas ses propres
droits.

## Profils de permissions

- **Lecture locale** : recherche et lecture limitées aux espaces enregistrés.
- **Brouillon documentaire** : création exclusive sous `Inbox/`, sans
  remplacement ni suppression de notes existantes.
- **Édition de workspace** : outils `list_files`, `read_file` et `write_file`
  partagés entre les modèles locaux; actuellement limités par le code au
  checkout Super IA, avec écriture non validée sous les règles systemd.
- **Fournisseur distant** : aucun contexte local sans activation explicite;
  politique cible. Le code de l'interface est actuellement pré-coché et les
  worktrees du backend divergent; les extraits peuvent être transmis au
  fournisseur selon le build chargé. Ne pas traiter ce comportement comme
  conforme avant la tâche P0 de confidentialité.
- **Trading** : état consultable; aucune clé ni capacité d'exécution d'ordre
  dans le chat.

« Tous les modèles locaux à la même enseigne » signifie le même catalogue
d'outils. Aujourd'hui, `write_file` ouvre en mode remplacement (`flag: w`), les
outils se basent sur `process.cwd()` et la validation du lien symbolique final
doit être revue. Les règles bloquent notamment les chemins cachés, `dist`,
`node_modules`, `backups` et certains noms de fichiers sensibles. En outre,
l'unité systemd active configure `ProtectHome=read-only` et n'autorise en
écriture que `~/.superia` et le montage `Inbox`; une écriture dans le checkout
peut donc échouer au niveau du système. Avant d'étendre l'accès, il faut une
liste de workspaces autorisés, des chemins canoniques, une protection contre
les liens symboliques et un aperçu/accord avant toute écriture.

## MCP et Obsidian

Un serveur MCP Obsidian est techniquement envisageable, mais un serveur seul ne
connecterait pas le chat : Mother doit aussi avoir un client MCP. Étapes
proposées :

1. extraire les fonctions de recherche, lecture de contexte et création Inbox
   derrière un service Obsidian commun;
2. borner les chemins au coffre monté et valider chaque entrée;
3. exposer ces fonctions par un serveur MCP local, en stdio ou sur transport
   local authentifié selon le consommateur;
4. intégrer un client dans le routeur Mother et afficher les appels/résultats;
5. vérifier les conflits Drive et conserver l'écriture exclusive dans Inbox.

Ne pas exposer de shell général, de suppression de note ni de remplacement de
fichier. Les spécifications du SDK officiel décrivent les transports et les
outils : [MCP TypeScript SDK](https://ts.sdk.modelcontextprotocol.io/v2/) et
[transport stdio](https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio).

## Ordre de construction

1. garder ce manifeste aligné sur les routes réellement disponibles;
2. définir une interface commune `list / call / result` et ses erreurs;
3. implémenter le registre et la vérification de permissions côté serveur;
4. raccorder les capacités existantes via des adaptateurs minces;
5. ajouter les journaux d'appel sans contenu sensible;
6. intégrer Obsidian via MCP après validation des montages et des conflits;
7. étudier la traduction d'articles et le routage d'outils de veille.

La prochaine tranche est de sécuriser les outils existants avant d'ajouter un
registre runtime : workspace explicitement sélectionné, lecture par défaut,
écriture atomique vers un nouveau fichier ou diff confirmé, puis preuve de
confinement. Le plan complet figure dans
[`PLAN-MISE-EN-ROUTE.md`](PLAN-MISE-EN-ROUTE.md). Le manifeste ne passera au
statut runtime qu'après l'intégration et sa recette.
