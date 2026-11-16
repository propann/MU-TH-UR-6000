# Banc d'essai des modèles locaux — 16 novembre 2026

Machine : RTX 3060 Ti 8 Go (CUDA v13, driver 595.104.02), 15 Go RAM, Ollama 0.40.16, contexte 8192, `think:false`, température 0.7. Génération mesurée sur 300 tokens ; prompt long (~2 100 tokens) pour la vitesse de traitement du contexte (pp).

| Modèle | Rôle | Params | Quant | Taille disque | VRAM | Chargement | pp tok/s | **tok/s (génération)** | Qualité |
|---|---|---|---|---|---|---|---|---|---|
| `qwen3.5:9b` | primaire | 9.0B | Q4_K_M | 6.6 Go | 5.62 Go | 10.55 s | 2117.1 | **52.3** | 3/3 |
| `qwen3:8b` | repli | 8.2B | Q4_K_M | 5.2 Go | 5.63 Go | 21.36 s | 2230.9 | **65.6** | 3/3 |
| `qwen3.5:0.8b` | rapide (veille) | 752.39M | Q8_0 | 1.3 Go | 0.63 Go | 9.28 s | 9189.7 | **123.7** | 3/3 |
| `huihui_ai/qwen3.5-abliterated:9b` | lab libéré | 9.7B | Q4_K_M | 6.6 Go | 5.52 Go | 20.4 s | 2065.9 | **64.0** | 2/3 |

## Détail qualité (3 questions, reasoning actif, budget 2048)

| Modèle | instruction | calcul (17×6) | contexte (port) |
|---|---|---|---|
| `qwen3.5:9b` | OK | OK | OK |
| `qwen3:8b` | OK | OK | OK |
| `qwen3.5:0.8b` | OK | OK | OK |
| `huihui_ai/qwen3.5-abliterated:9b` | OK | KO | OK |

## Lecture

- **`qwen3.5:9b` (primaire)** : meilleur compromis qualité/vitesse pour 8 Go de VRAM ; 100 % en VRAM (5,62 Go), ~52 tok/s. Plus récent que le 8B (256K natif, vision, meilleure compréhension).
- **`qwen3.5:0.8b` (rapide)** : ~124 tok/s, 0,63 Go de VRAM — idéal pour résumer les flux RSS, traduire, classer.
- **`qwen3:8b` (repli)** : ~66 tok/s, qualité 3/3.
- **`huihui_ai/qwen3.5-abliterated:9b` (lab)** : ~64 tok/s, 2/3 en reasoning (budget 2048 consommé par le raisonnement interne sur le calcul — quirk documenté ; utiliser `think:false` avec ce modèle).
- Chargement 9–21 s selon le modèle ; le keep-alive 30 min évite de le repayer entre deux conversations.
- Tous les modèles tiennent à 100 % en VRAM à ctx 8192 (flash attention + KV q8_0 actifs).

Résultats bruts : `/tmp/bench_results.json` (script `/tmp/bench_models.py`).
