# Assistant Mistral transversal

## État livré

Le script `dist/assistant-overlay.js` ajoute le même mini-chat aux trois vues
servies par le cockpit : Veille, Super IA et Quant Core. Il utilise le proxy
authentifié `/ia/api/chat`; la clé Mistral reste donc dans le coffre chiffré de
Super IA et n'est jamais envoyée au navigateur.

Le panneau reprend l'expérience du CLI Vibe : conversation persistante pendant
la session, contexte de la fenêtre et mode éditeur. Le mode éditeur livré dans
cette étape produit un plan de modification. Il ne prétend pas avoir écrit un
fichier et n'expose aucun shell.

## Pourquoi l'écriture directe est bloquée

Une page accessible sur le LAN qui lancerait `vibe --trust` dans `/home/azoth`
deviendrait une exécution de code distante. Une injection dans un article RSS,
une requête forgée ou une session de navigateur volée pourrait alors modifier
le poste et lire des secrets.

Le backend Super IA possède déjà la chaîne correcte : mission déclarée,
`allowedPaths`, worktree Git isolé, Gitleaks, Bubblewrap, budget, shell Vibe
désactivé et contrôle du périmètre modifié. Le futur bouton « Appliquer » doit
obligatoirement appeler cette chaîne.

## Flux éditeur cible

1. choisir un dépôt enregistré et des chemins autorisés ;
2. demander un plan Vibe en lecture seule ;
3. afficher fichiers, budget et diff prévu ;
4. confirmer explicitement la création du worktree ;
5. exécuter Vibe avec outils `read`, `grep`, `write_file` et `edit`, sans Bash ;
6. montrer le diff réel et les résultats Gitleaks/tests ;
7. laisser l'opérateur accepter, corriger ou abandonner le worktree.

L'overlay ne doit jamais pouvoir sélectionner `/home`, le coffre Obsidian, les
credentials, les fichiers `.env`, les sauvegardes ou les données runtime comme
workspace éditable.
