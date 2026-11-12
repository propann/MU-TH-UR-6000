#!/usr/bin/env bash
# Monte le coffre Drive en lecture-écriture pour Obsidian. Les brouillons IA
# restent dirigés vers le montage Inbox séparé afin de ne pas écraser une note.
set -euo pipefail

remote="${1:-gdrive}"
vault="/home/azoth/GoogleDrive/SuperIA-Vault"
inbox="/home/azoth/GoogleDrive/SuperIA-Inbox"
folders_file="${AZOTH_DRIVE_FOLDERS_FILE:-$HOME/.config/azoth/drive-folders.env}"
vault_folder_id="${AZOTH_VAULT_FOLDER_ID:-}"
inbox_folder_id="${AZOTH_INBOX_FOLDER_ID:-}"

if [ -z "$vault_folder_id" ] || [ -z "$inbox_folder_id" ]; then
  if [ ! -r "$folders_file" ]; then
    printf 'Configuration Drive absente : %s\n' "$folders_file" >&2
    printf 'Copier config/drive-folders.env.example hors du dépôt et y définir les deux identifiants.\n' >&2
    exit 1
  fi
  while IFS='=' read -r key value; do
    case "$key" in
      AZOTH_VAULT_FOLDER_ID) vault_folder_id="$value" ;;
      AZOTH_INBOX_FOLDER_ID) inbox_folder_id="$value" ;;
    esac
  done < "$folders_file"
fi

if [[ ! "$vault_folder_id" =~ ^[A-Za-z0-9_-]{20,}$ || ! "$inbox_folder_id" =~ ^[A-Za-z0-9_-]{20,}$ ]]; then
  printf 'Identifiants de dossiers Drive absents ou invalides dans %s.\n' "$folders_file" >&2
  exit 1
fi

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
    --drive-root-folder-id "$vault_folder_id" \
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
    --drive-root-folder-id "$inbox_folder_id" \
    --vfs-cache-mode full \
    --vfs-cache-max-size 512M \
    --daemon
fi

printf 'Coffre Obsidian éditable : %s\n' "$vault"
printf 'Brouillons IA séparés : %s\n' "$inbox"
