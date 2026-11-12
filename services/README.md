# Registre des composants

Ce dossier reçoit localement des liens vers les clones conservés sous
`~/serveur-local/sources/`. Ces liens sont reconstruits par
`scripts/rattacher-sources.sh` et ne sont jamais publiés.

| Lien local cible | Dépôt officiel | État observé le 12/11/2026 |
|---|---|---|
| `services/veille-azoth` | `propann/MU-TH-UR-6000` | `main`, HEAD `8a4e3c6` |
| `services/super-ia` | `propann/super-ia` | source `main`, HEAD `8f8407b`; runtime séparé `fix/lan-token-login`, HEAD `8baa911`, modifié |
| `services/freqtrade` | `propann/freqtrade` | `rebuild/engine-optional`, HEAD `48d8024` (propre) |
| `services/Az-N8N` | `propann/Az-N8N` | `main`, référence archivée, HEAD `8c742a1` |

Les liens indiqués sont les destinations prévues par le script de rattachement;
ils n'étaient pas présents dans ce checkout au moment de la revue.

État relevé le 12 novembre 2026. MU-TH-UR 6000 est le dépôt canonique de
livraison du projet. Les dépôts listés
restent les sources actuellement utilisées par les services; ils ne sont pas
encore consolidés dans ce dépôt. Toute migration doit préserver l'historique,
les licences, les tests, la provenance et les chemins de déploiement. La cible
et ses étapes sont suivies dans [`../docs/PLAN-MISE-EN-ROUTE.md`](../docs/PLAN-MISE-EN-ROUTE.md).
