# Architecture cible

## Interface

Une seule entrée authentifiée dessert six espaces :

| Espace | Fonction | Service source |
|---|---|---|
| Accueil | santé, alertes, raccourcis, ressources | nouveau bureau Azoth |
| Recherche | retrouver une note, un projet, une conversation ou un rapport | index global |
| Cerveau | recherche et citations dans Obsidian | index local + coffre monté |
| IA | conversations, modèles et agents | Ollama + SuperIA |
| Veille | RSS, alertes, tri, favoris et synthèses | Veille Azoth + coffre Drive |
| Trading | positions, profits, stratégies, logs et recherche | Quant Core |

La cabine Trading reste un module distinct dans le bureau. Son moteur Freqtrade
et son API ne sont jamais exposés directement au LAN ; seule la console serveur
communique avec eux sur le réseau privé des conteneurs.

Quant Core doit gérer plusieurs sessions de bot isolées. Une session possède
son propre état, sa stratégie, son profil de risque, son portefeuille simulé,
ses journaux et son cycle démarrage/arrêt. La première mise en service n'en
lance qu'une afin de valider les ressources et les garde-fous. L'interface sera
conçue dès le départ pour en afficher plusieurs sans dupliquer leurs secrets.

Le choix de l'exchange n'est pas arrêté. Binance sert uniquement de source de
données publiques dans la configuration dry-run initiale ; aucune dépendance
fonctionnelle du cockpit ne doit supposer que Binance sera l'exchange final.
Le futur connecteur d'exécution sera choisi et validé séparément.

Obsidian n'est pas utilisé comme tableau de bord d'exploitation. Il reste le
coffre durable et l'éditeur des connaissances. Le bureau Azoth affiche ses notes,
crée des brouillons dans `Inbox/`, puis ouvre Obsidian lorsqu'une édition riche
est demandée.

## Services

```text
navigateur LAN
    |
    v
bureau Azoth authentifié
    |-- Cerveau ----> index local ----> SuperIA-Vault
    |-- IA ---------> API locale -----> Ollama
    |-- Agents ------> SuperIA --------> dépôts Git
    |-- Veille ------> Veille Azoth ---> flux RSS + Drive/Veille
    `-- Trading -----> Quant Core -----> Freqtrade dry-run
                              |--------> Quant Rack
                              `--------> laboratoires à la demande
```

## Limites de ressources initiales

- un seul grand modèle IA chargé ;
- contexte IA initial de 8 192 tokens ;
- Freqtrade : 1 CPU et 1 Go RAM au repos ;
- console Trading : 0,5 CPU et 512 Mo RAM ;
- laboratoires stratégie et FreqAI arrêtés hors recherche ;
- l'indexation Drive est lancée après validation du socle trading ;
- les tâches lourdes de backtest et d'indexation ne tournent pas en même temps.

## Frontières de sécurité fonctionnelles

- secrets hors Git, Drive et Obsidian ;
- aucun port Freqtrade publié ;
- le modèle débridé ne reçoit ni outil système, ni clé, ni action de trading ;
- activation de stratégie bornée au dry-run pendant la construction ;
- aucune session ne peut quitter le dry-run par une action du cockpit ou de l'IA ;
- les sessions de bot restent isolées et identifiées explicitement ;
- le coffre Drive est d'abord monté en lecture seule ;
- toute réponse issue du cerveau doit citer le chemin ou la page source.
