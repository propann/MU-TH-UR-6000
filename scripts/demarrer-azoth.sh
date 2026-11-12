#!/usr/bin/env bash
set -euo pipefail

quant_root="/home/azoth/serveur-local/sources/freqtrade"
compose_file="$quant_root/docker-compose.coolify.yml"
env_file="$quant_root/.env"

if [ ! -r "$env_file" ]; then
  printf 'Configuration Quant Core absente : %s\n' "$env_file" >&2
  exit 1
fi

for _ in {1..30}; do
  if docker info >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! docker info >/dev/null 2>&1; then
  printf 'Docker indisponible après 60 secondes.\n' >&2
  exit 1
fi

docker compose --env-file "$env_file" -f "$compose_file" up -d
if [ -z "${INVOCATION_ID:-}" ]; then
  systemctl --user start ollama.service veille-azoth.service
fi

printf 'Azoth démarré : Ollama, cockpit et Quant Core.\n'
