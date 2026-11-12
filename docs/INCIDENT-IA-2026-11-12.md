# Incident IA du 12 novembre 2026

## Symptôme

Les réponses locales paraissaient incohérentes, excessives ou aléatoires après
plusieurs essais dans le chat Super IA.

## Cause confirmée

Les journaux Ollama montrent une transition nette :

- requêtes normales à température `0.7` jusqu'au 11 novembre à 20 h 40 ;
- requêtes à température `2.0` à partir de 20 h 41 ;
- réutilisation de `2.0` après le redémarrage du 12 novembre.

Le navigateur conservait ce réglage dans `localStorage` et l'interface comme le
serveur acceptaient une valeur maximale de `2.0`. Les requêtes concernées
utilisaient en plus le modèle expérimental
`hf.co/richardyoung/Qwen3-8B-Abliterated-GGUF:Q4_K_M`. Ce modèle expérimental
n'est pas le modèle de référence. Comme les autres modèles locaux, il reçoit le
même catalogue d'outils workspace; leurs filtres de chemins ne sont pas encore
suffisants pour déclarer l'écriture sûre. Aucun ne reçoit d'outil de trading.

Le GPU n'est pas en cause : Ollama a détecté la RTX 3060 Ti, utilisé CUDA, chargé
le modèle en VRAM et terminé les générations sans troncature. Aucun OOM ni Xid
NVIDIA pertinent n'apparaît dans les journaux.

## Correction

Super IA applique désormais les barrières suivantes :

- température par défaut `0.7` ;
- maximum `1.0` dans l'interface et côté serveur ;
- valeur absente, invalide ou non numérique ramenée à `0.7` ;
- modèle stable affiché avant les modèles expérimentaux ;
- suffixe `EXPÉRIMENTAL` visible dans la liste ;
- ancien choix expérimental non restauré automatiquement au chargement.

La barrière serveur est l'autorité : une requête modifiée manuellement ou une
ancienne préférence navigateur ne peut plus imposer une température de `2.0`.

## Validation

### Résultat sur l'hôte

Validation terminée le 12 novembre 2026 à 06 h 59 :

- `superia-web.service` arrêté puis redémarré normalement ;
- build corrigé chargé depuis le worktree actif ;
- modèle stable `qwen3:8b` chargé intégralement sur la RTX 3060 Ti ;
- génération de référence lancée à température `0.200` ;
- réponse Ollama terminée en HTTP `200` ;
- `106` jetons traités, `truncated = 0` ;
- aucune erreur GPU, mémoire ou serveur pendant le test.

L'incident est donc corrigé et la barrière est active en production locale.

Contrôles de code exécutés :

```bash
cd ~/serveur-local/worktrees/super-ia-lan-auth
npm run build
node tests/web.test.mjs
```

Le test unitaire de normalisation passe. Le test d'écoute HTTP ne peut pas
s'exécuter dans une session de maintenance qui interdit la création de sockets ;
il échoue alors explicitement avec `listen EPERM`.

Après redémarrage du service sur l'hôte :

```bash
systemctl --user restart superia-web.service
bash scripts/tester-ia-locale.sh
journalctl --user -u ollama.service -n 100 --no-pager | grep 'temp ='
```

Le test de référence utilise `qwen3:8b` à température `0.2`. Le journal ne doit
plus montrer de température supérieure à `1.000` pour les nouvelles requêtes du
chat.

## Usage recommandé

- Conversation factuelle : température `0.2` à `0.5`.
- Conversation générale : température `0.7`.
- Créativité : jusqu'à `1.0`, avec vérification humaine.
- Modèle `Abliterated` : expérimental, jamais sélectionné par défaut; mêmes
  outils locaux bornés que les autres modèles, sans secret ni accès trading.

## Retour arrière

La modification touche uniquement Super IA et son interface. Pour interrompre
le service sans toucher aux modèles ni aux données :

```bash
systemctl --user stop superia-web.service
```

Ne pas supprimer les modèles Ollama ni le coffre documentaire pour revenir en
arrière. Les conversations du navigateur ne constituent pas une source de
vérité documentaire.
