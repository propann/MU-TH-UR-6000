# Qualité des réponses locales

## Constats

L'audit du chat montre l'absence de consigne système générale, un historique
conservé lors du changement de modèle, et aucune indication lorsque la limite
de génération interrompt une réponse. Ces défauts peuvent contribuer aux réponses
incohérentes, sans prouver que le modèle lui-même est défectueux.

Le chat injecte désormais une consigne factuelle en français, réinitialise la
conversation lors du choix d'un autre modèle et affiche la troncature signalée
par Ollama. Les noms de modèles ne déterminent plus leur ordre, leur étiquette
ou leur restauration dans le sélecteur. Le test opérateur accepte tous les noms.

## Vérification sur l'hôte

Le lecteur NDJSON a été corrigé : il conserve l'événement final sans saut de
ligne, reconstitue l'UTF-8 fragmenté, remonte les erreurs du fournisseur et refuse
une fin de flux sans événement `done`. Le chat signale le raisonnement en cours
sans le confondre avec la réponse finale. Les tests reproduisent ces cas avec
des flux synthétiques ; ils ne mesurent pas la qualité des modèles installés.

`python3 scripts/diagnostiquer-modeles.py` sonde tous les modèles installés, ou
uniquement les noms fournis en arguments. Trois questions publiques vérifient
instruction, calcul et utilisation d'un contexte fourni. Le script affiche la
réponse, la durée, le nombre de tokens et la cause de fin. La présence d'une
réponse attendue est un indicateur simple, pas une évaluation sémantique complète.
Les résultats restent dans le terminal ; aucun contenu du coffre n'est utilisé.

Ollama n'était pas joignable depuis le terminal de maintenance. Aucun résultat
de qualité en inférence réelle n'est donc revendiqué.

Exécuter `bash scripts/tester-ia-locale.sh NOM-DU-MODELE` pour chaque modèle.
Ce contrôle vérifie une instruction courte ; il ne constitue pas un benchmark.
Comparer ensuite une question factuelle, une traduction et une question sur une
note connue, d'abord sans contexte Obsidian, puis avec. Utiliser une nouvelle
conversation et les mêmes paramètres pour chaque modèle. Relever le modèle exact,
la réponse, la latence et toute coupure avant de modifier les paramètres.

Pour les modèles de raisonnement, Ollama sépare `message.thinking` et
`message.content`. Le chat affiche la réponse finale ; une limite trop courte peut
être consommée avant cette réponse. Voir la [documentation officielle Ollama](https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx).

Le chat local expose `list_files`, `read_file` et `write_file` aux deux modèles
locaux. Le dernier outil peut remplacer un fichier et le workspace effectif est
le répertoire de travail du service Super IA. Cette fonction existe donc dans
le code, mais son périmètre ne correspond pas encore à un espace de travail
Mother sûr : voir [le rack](RACK-LOGICIEL.md) et le [plan de mise en route](PLAN-MISE-EN-ROUTE.md).
Les commandes système ne sont pas exposées comme outils de chat.

Le diagnostic opérateur fourni le 12 novembre valide les deux modèles et
`list_files` avec le raisonnement activé. En mode `SUPERIA_TEST_THINK=0`, le
modèle Abliterated a produit du raisonnement interne à la place de la réponse
attendue et le contrôle global a échoué. Ne considérer ce mode comme stable
qu'après correction et nouveau test sur l'hôte.
