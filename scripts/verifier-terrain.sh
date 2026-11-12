#!/usr/bin/env bash
set -u

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
source_root="/home/azoth/serveur-local/sources"
errors=0

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'OK      commande %s\n' "$1"
  else
    printf 'ATTENTE commande %s\n' "$1"
    errors=$((errors + 1))
  fi
}

for command_name in git docker flatpak rclone nvidia-smi; do
  check_command "$command_name"
done

if curl -fsS --max-time 2 http://127.0.0.1:11434/api/version >/dev/null; then
  printf 'OK      API Ollama locale\n'
else
  printf 'ATTENTE API Ollama locale\n'
  errors=$((errors + 1))
fi

for repo in freqtrade super-ia veille-azoth; do
  if [ -d "$source_root/$repo/.git" ]; then
    printf 'OK      depot %s (%s)\n' "$repo" "$(git -C "$source_root/$repo" rev-parse --short HEAD)"
  else
    printf 'ATTENTE depot %s\n' "$repo"
    errors=$((errors + 1))
  fi
done

printf 'Projet : %s\n' "$project_root"
printf 'Points en attente : %s\n' "$errors"
exit "$errors"
