# Chat IA et cerveau Obsidian

> Incident du 12 novembre 2026 : les réponses instables provenaient du cumul
> d'une température `2.0` mémorisée dans le navigateur et du modèle expérimental
> Abliterated. Voir [INCIDENT-IA-2026-11-12.md](INCIDENT-IA-2026-11-12.md) pour
> le diagnostic, les barrières ajoutées et le test de référence.

## Objectif

La façade Super IA est un chat personnel léger. Elle donne accès aux modèles
Ollama locaux et, sur choix explicite, à l'API Mistral. Elle ne lance aucun
agent autonome et ne possède aucun accès aux commandes système ou au trading.

L'accès LAN passe uniquement par le cockpit :

- cockpit : `http://<adresse-lan>:8765` ;
- chat IA : `/ia/` ;
- ancienne matrice, conservée pour diagnostic : `/ia/matrix` ;
- service Super IA direct : `127.0.0.1:3210`, inaccessible depuis le LAN.

## Modèles et confidentialité

Ollama est le fournisseur par défaut. La liste de modèles est lue depuis
`http://127.0.0.1:11434/api/tags`. Le modèle, la température et la longueur
maximale sont choisis dans l'interface.

Mistral n'est appelé qu'après sélection manuelle et confirmation pour chaque
message. Sa clé est saisie dans la page IA, chiffrée en AES-256-GCM et stockée
hors Git dans `~/.superia/credentials/vault.enc`. La clé n'est jamais renvoyée
au navigateur après son enregistrement.

Le contexte Obsidian est disponible avec Ollama et Mistral via la case « Utiliser
Obsidian ». Avec Mistral, les extraits sélectionnés sont transmis à l'API distante.
Voir [la liaison Mistral et Obsidian](MISTRAL-OBSIDIAN.md) pour le périmètre exact.

## Coffre documentaire

Drive `SuperIA-Vault` est la source officielle. Le remote rclone attendu est
`gdrive:`. Le script `~/serveur-local/connecter-cerveau.sh` crée deux montages :

- `/home/azoth/GoogleDrive/SuperIA-Vault` : coffre complet éditable dans Obsidian ;
- `/home/azoth/GoogleDrive/SuperIA-Inbox` : montage indépendant et écrivable,
  ciblant le dossier Drive `Inbox` du coffre officiel.

Le statut du coffre ne parcourt pas Drive et répond immédiatement. La première
recherche construit l'index à la demande, parcourt au plus 2 000 notes Markdown
et conserve la liste des chemins en mémoire pendant 30 secondes. Les réponses locales doivent citer les
chemins `SOURCE` fournis. Le bouton `+ Obsidian` crée une nouvelle note dans
`Inbox/` avec frontmatter `status: brouillon`. Il utilise une création exclusive
et ne peut donc pas écraser une note existante.

## Démarrage

Le target `azoth.target` démarre Ollama, le coffre, Super IA, le cockpit et
Quant Core. Le service `azoth-vault.service` monte le coffre avant Super IA.

```bash
systemctl --user daemon-reload
systemctl --user enable --now azoth.target
```

Contrôles rapides :

```bash
mountpoint /home/azoth/GoogleDrive/SuperIA-Vault
mountpoint /home/azoth/GoogleDrive/SuperIA-Inbox
curl -fsS http://127.0.0.1:3210/healthz
curl -fsS http://127.0.0.1:3210/api/vault/status
```

Les ports attendus sont `8765` sur le LAN, puis `3000`, `3210` et `11434`
uniquement en boucle locale.

## Vérifications après modification

```bash
cd ~/serveur-local/worktrees/super-ia-lan-auth
npm run build
node --test tests/web.test.mjs

python3 -m py_compile ~/serveur-local/sources/veille-azoth/veille.py
bash -n ~/serveur-local/connecter-cerveau.sh
git diff --check
```

Le test ciblé de stabilité de température doit toujours passer. Dans un
environnement de maintenance isolé, les tests qui ouvrent un socket local ou
lancent un sous-processus peuvent échouer avec `EPERM` ; relancer alors la suite
sur l'hôte avant publication.

## Retour arrière

Pour couper uniquement l'écriture des brouillons :

```bash
fusermount3 -u /home/azoth/GoogleDrive/SuperIA-Inbox
systemctl --user restart superia-web.service
```

Le coffre principal reste éditable dans Obsidian. Pour arrêter tous les montages :

```bash
systemctl --user stop azoth-vault.service
```

Ne jamais supprimer le contenu d'un point de montage pour le démonter et ne
jamais utiliser une synchronisation bidirectionnelle automatique sur le coffre.
