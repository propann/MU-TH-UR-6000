# Interface cible MU-TH-UR 6000

Ce document décrit la cible produit, pas l'interface actuellement livrée.
L'état implémenté est décrit dans le README et le
[plan de mise en route](PLAN-MISE-EN-ROUTE.md).

## Expérience recherchée

Après connexion, une seule fenêtre donne accès à l'ensemble du système. Une
barre latérale stable contient :

```text
Accueil
Recherche
Cerveau
IA
Veille
Trading
Projets
Automatisations
Machine
Réglages
```

La barre supérieure contient une recherche globale et l'état synthétique : IA,
coffre, trading, réseau et sauvegarde.

## Accueil

- reprendre la dernière activité ;
- conversations et notes récentes ;
- état de l'IA locale ;
- état du bot et mode `dry-run` clairement visible ;
- éléments de veille à valider ;
- tâches Git et traitements documentaires ;
- alertes machine utiles.

## Recherche globale

Une requête unique cherche dans :

- les notes Markdown et pièces jointes indexées ;
- les projets Git et leur documentation ;
- les rapports de trading et de backtest ;
- la veille ;
- les conversations enregistrées ;
- les événements et journaux résumés.

Chaque résultat indique son origine, sa date et son niveau de confidentialité.
Un résultat documentaire ouvre la note ou la source exacte. Un résultat de
service ouvre le bon écran du bureau.

## Cerveau

- navigation dans `SuperIA-Vault` ;
- recherche hybride avec citations ;
- aperçu Markdown, PDF et documents convertis ;
- bouton « Ouvrir dans Obsidian » ;
- création uniquement dans `Inbox/` au départ ;
- état de synchronisation et conflits visibles.

## IA

- modèle actif et consommation CPU/GPU/RAM ;
- conversations locales ;
- choix entre modèle principal et laboratoire débridé ;
- sources utilisées affichées à côté de la réponse ;
- enregistrement volontaire d'un échange dans le coffre ;
- outils autorisés affichés avant chaque action.

## Trading

La console Quant Core devient la cabine dédiée :

- mode réel ou dry-run toujours visible ;
- positions, capital, profits et risques ;
- stratégie et profil Quant Rack actifs ;
- logs et santé du moteur ;
- laboratoire de backtest et résultats hors échantillon ;
- rapport exportable dans le coffre ;
- aucun ordre forcé par l'IA.

## Veille

- sources présentes dans le dossier Drive `Veille/` ;
- doublons regroupés ;
- résumé local et liens originaux ;
- validation humaine avant archivage ;
- publication des éléments retenus dans `Veille/` ;
- possibilité de transformer un élément en tâche de projet.

## Projets et traitements

- dépôts, branches, changements et tests ;
- missions SuperIA et agents disponibles ;
- état de la synchronisation et de l'indexation documentaire ;
- liens directs vers les notes projet ;
- traces d'action et reçus consultables.

## Machine

- CPU, RAM, GPU, stockage, températures et réseau ;
- services actifs et en échec ;
- sauvegardes et dernière restauration testée ;
- mises à jour disponibles ;
- consommation des laboratoires lourds.

## Règles de données

| Donnée | Emplacement durable |
|---|---|
| Notes, décisions, rapports lisibles | Obsidian / Drive |
| Sources PDF, DOCX, images | Drive avec référence depuis le coffre |
| Embeddings et index | stockage local reconstruisible |
| État des services | volumes locaux |
| Secrets et clés | coffre serveur local, jamais Obsidian |
| Modèles IA | stockage local |
| Données Freqtrade | volume privé Quant Core |
| Sauvegardes | stockage séparé à définir |

## Première version utile

La première version ne cherche pas à tout réécrire. Elle fournit le menu commun,
la recherche, les états de santé et des ouvertures vers les interfaces existantes.
La cabine Quant Core reste intacte. Les intégrations deviennent natives une fois
les services validés sur cette machine.
