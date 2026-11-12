#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
source_root="/home/azoth/serveur-local/sources"

for repo in freqtrade super-ia veille-azoth; do
  source_path="$source_root/$repo"
  target_path="$project_root/services/$repo"
  if [ ! -d "$source_path/.git" ]; then
    printf 'Source absente : %s\n' "$source_path"
    printf 'Restaurer ou cloner ce dépôt dans %s, puis relancer ce script.\n' "$source_root"
    exit 1
  fi
  if [ -L "$target_path" ]; then
    continue
  fi
  if [ -e "$target_path" ]; then
    printf 'Cible existante non modifiee : %s\n' "$target_path"
    exit 1
  fi
  ln -s "$source_path" "$target_path"
done

actual_trade_commit="$(git -C "$source_root/freqtrade" rev-parse HEAD)"
printf 'Freqtrade local : %s\n' "$actual_trade_commit"
printf 'Sources rattachees dans %s/services\n' "$project_root"
