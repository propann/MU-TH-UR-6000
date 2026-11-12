#!/usr/bin/env bash
set -uo pipefail

errors=0
check_url() {
  local label="$1"
  local url="$2"
  local credentials="${3:-}"
  local attempts="${4:-1}"
  local attempt=1
  local curl_args=(-fsS --max-time 3)
  if [ -n "$credentials" ]; then
    curl_args+=(-u "$credentials")
  fi
  while [ "$attempt" -le "$attempts" ]; do
    if curl "${curl_args[@]}" "$url" >/dev/null 2>&1; then
      printf 'OK      %s\n' "$label"
      return
    fi
    if [ "$attempt" -lt "$attempts" ]; then sleep 1; fi
    attempt=$((attempt + 1))
  done
  printf 'ATTENTE %s\n' "$label"
  errors=$((errors + 1))
}

check_url "Ollama" "http://127.0.0.1:11434/api/version"
password_file="${VEILLE_PASSWORD_FILE:-$HOME/.config/azoth/veille-azoth.env}"
veille_password="${VEILLE_PASSWORD:-}"
if [ -z "$veille_password" ] && [ -r "$password_file" ]; then
  veille_password="$(sed -n 's/^VEILLE_PASSWORD=//p' "$password_file")"
elif [ -z "$veille_password" ] && [ -r /etc/veille-azoth.env ]; then
  veille_password="$(sed -n 's/^VEILLE_PASSWORD=//p' /etc/veille-azoth.env)"
elif [ -z "$veille_password" ] && command -v sudo >/dev/null 2>&1 && sudo -n test -r /etc/veille-azoth.env 2>/dev/null; then
  veille_password="$(sudo -n sed -n 's/^VEILLE_PASSWORD=//p' /etc/veille-azoth.env)"
fi
cockpit_url="${AZOTH_COCKPIT_URL:-http://127.0.0.1:8765}"
quant_url="${QUANT_CORE_URL:-http://127.0.0.1:3000/quant}"
check_url "Cockpit" "${cockpit_url}/" "azoth:${veille_password}" 8
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
