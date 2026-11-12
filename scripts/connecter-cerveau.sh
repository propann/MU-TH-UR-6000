#!/usr/bin/env bash
# Monte le coffre Drive en lecture-écriture pour Obsidian. Les brouillons IA
# restent dirigés vers le montage Inbox séparé afin de ne pas écraser une note.
set -euo pipefail

remote="${1:-gdrive}"
vault="/home/azoth/GoogleDrive/SuperIA-Vault"
inbox="/home/azoth/GoogleDrive/SuperIA-Inbox"

if ! rclone listremotes | grep -Fxq -- "${remote}:"; then
  printf 'Configurer rclone avec le remote %s.\n' "$remote"
  exit 1
fi

mkdir -p "$vault" "$inbox"
if ! mountpoint -q "$vault"; then
  if [ -n "$(ls -A "$vault")" ]; then
    printf 'Le point de montage du coffre contient déjà des fichiers : arrêt.\n' >&2
    exit 1
  fi
  rclone mount "${remote}:" "$vault" \
    --drive-root-folder-id 1qOd-SetSWtOGONX7CujzBCBhB9U72Ygf \
    --vfs-cache-mode full \
    --vfs-cache-max-size 2G \
    --daemon
fi

if ! mountpoint -q "$inbox"; then
  if [ -n "$(ls -A "$inbox")" ]; then
    printf 'Le point de montage Inbox contient déjà des fichiers : arrêt.\n' >&2
    exit 1
  fi
  rclone mount "${remote}:" "$inbox" \
    --drive-root-folder-id 1m9_atNUZuM-hyv8lZHbDR2vucHFBOS5y \
    --vfs-cache-mode full \
    --vfs-cache-max-size 512M \
    --daemon
fi

printf 'Coffre Obsidian éditable : %s\n' "$vault"
printf 'Brouillons IA séparés : %s\n' "$inbox"
