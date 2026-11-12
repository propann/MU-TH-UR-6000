#!/usr/bin/env bash
set -uo pipefail

errors=0
check_url() {
  local label="$1"
  local url="$2"
  local credentials="${3:-}"
  local curl_args=(-fsS --max-time 3)
  if [ -n "$credentials" ]; then
    curl_args+=(-u "$credentials")
  fi
  if curl "${curl_args[@]}" "$url" >/dev/null; then
    printf 'OK      %s\n' "$label"
  else
    printf 'ATTENTE %s\n' "$label"
    errors=$((errors + 1))
  fi
}

check_url "Ollama" "http://127.0.0.1:11434/api/version"
veille_password="$(sed -n 's/^VEILLE_PASSWORD=//p' /home/azoth/.config/azoth/veille-azoth.env)"
cockpit_url="${AZOTH_COCKPIT_URL:-http://127.0.0.1:8765}"
quant_url="${QUANT_CORE_URL:-http://127.0.0.1:3000/quant}"
check_url "Cockpit" "${cockpit_url}/" "azoth:${veille_password}"
check_url "Super IA locale" "http://127.0.0.1:3210/healthz"
check_url "Quant Core local" "${quant_url}/api/health"

for container in quantapex-freqtrade-core quantapex-rack-agent quantapex-ui-terminal; do
  if [ "$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null)" = "true" ]; then
    printf 'OK      conteneur %s\n' "$container"
  else
    printf 'ATTENTE conteneur %s\n' "$container"
    errors=$((errors + 1))
  fi
done

printf '\nPoints en attente : %d\n' "$errors"
exit "$errors"
