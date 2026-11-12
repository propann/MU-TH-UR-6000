#!/usr/bin/env bash
set -euo pipefail

modele="${1:-qwen3:8b}"
api_ollama="http://127.0.0.1:11434"

if [[ "${modele,,}" == *"abliterated"* || "${modele,,}" == *"uncensored"* ]]; then
  echo "ERREUR  Le modèle expérimental ${modele} ne doit pas servir au test de référence."
  exit 2
fi

if ! curl --fail --silent --show-error --max-time 5 "${api_ollama}/api/version" >/dev/null; then
  echo "ERREUR  API Ollama inaccessible sur ${api_ollama}."
  exit 3
fi

if ! curl --fail --silent --show-error --max-time 5 "${api_ollama}/api/tags" |
  python3 -c 'import json,sys; wanted=sys.argv[1]; models=json.load(sys.stdin).get("models", []); raise SystemExit(0 if any((m.get("name") or m.get("model")) == wanted for m in models) else 1)' "${modele}"; then
  echo "ERREUR  Modèle stable absent : ${modele}."
  exit 4
fi

reponse="$({
  printf '%s' '{"model":'
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]), end="")' "${modele}"
  printf '%s' ',"stream":false,"messages":[{"role":"system","content":"Réponds sobrement, factuellement et en français. N’invente rien."},{"role":"user","content":"Réponds uniquement par: TEST IA OK"}],"options":{"temperature":0.2,"num_predict":64}}'
} | curl --fail --silent --show-error --max-time 120 \
  --header 'Content-Type: application/json' \
  --data-binary @- "${api_ollama}/api/chat")"

if ! python3 -c 'import json,sys; text=json.load(sys.stdin).get("message", {}).get("content", ""); raise SystemExit(0 if "TEST IA OK" in text.upper() else 1)' <<<"${reponse}"; then
  echo "ERREUR  Réponse incohérente du modèle stable ${modele}."
  exit 5
fi

echo "OK      Ollama accessible"
echo "OK      Modèle stable présent : ${modele}"
echo "OK      Réponse de référence cohérente à température 0,2"
