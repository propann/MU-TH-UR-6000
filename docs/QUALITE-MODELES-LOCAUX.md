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

Les fonctions d'édition et de commandes ne sont pas encore raccordées au chat
local : supprimer une distinction dans le sélecteur ne crée pas ces outils.
