#!/usr/bin/env bash
# Installation reproductible du poste de développement Azoth.
# À lancer avec le compte normal : bash installer-socle-dev.sh
set -euo pipefail
umask 077

if [ "$(id -u)" -eq 0 ]; then
  echo "Lancer ce script avec le compte normal, sans sudo devant bash." >&2
  exit 1
fi

repo="$HOME/serveur-local/sources/super-ia"
tools="$repo/install/tools"
audit="$HOME/serveur-local/audit"
mkdir -p "$audit"
exec > >(tee "$audit/socle-dev-$(date +%Y%m%d-%H%M%S).log") 2>&1
trap 'echo "Installation interrompue à la ligne $LINENO." >&2' ERR

for required_script in \
  "$tools/system-packages-debian.sh" \
  "$tools/bootstrap-user-tools.sh" \
  "$tools/verify-toolchain.sh"; do
  if [ ! -r "$required_script" ]; then
    echo "Script Super IA absent ou illisible : $required_script" >&2
    exit 1
  fi
done

echo "==> Autorisation administrateur"
sudo -v

echo "==> Dépendances système Super IA"
sudo bash "$tools/system-packages-debian.sh" --profile standard

echo "==> Dépendances développement, embarqué et supervision"
sudo apt-get install -y --no-install-recommends \
  git-lfs shellcheck jq pipx python3-venv btop nvtop smartmontools lm-sensors \
  mosquitto mosquitto-clients adb minicom screen avahi-utils unzip

echo "==> Accès Docker et ports série"
sudo systemctl enable --now docker
sudo usermod -aG docker,dialout "$USER"
git lfs install --skip-repo

echo "==> Toolchain utilisateur Super IA"
bash "$tools/bootstrap-user-tools.sh" --profile standard
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"

echo "==> Bun utilisateur"
bun_version="1.4.4"
if ! command -v bun >/dev/null 2>&1; then
  bun_installer="$audit/bun-install-$bun_version.sh"
  curl --fail --location --retry 3 --proto '=https' --proto-redir '=https' \
    https://bun.com/install -o "$bun_installer"
  bash "$bun_installer" -s "bun-v$bun_version"
fi

echo "==> Meshtastic et PlatformIO isolés"
if ! command -v meshtastic >/dev/null 2>&1; then
  pipx install meshtastic
fi
if ! command -v pio >/dev/null 2>&1; then
  pipx install platformio
fi

echo "==> Vérification sans démarrage des applications"
bash "$tools/verify-toolchain.sh" --profile standard || true
node --version
npm --version
bun --version
docker --version
docker compose version
meshtastic --version || true
pio --version || true

cat <<'TXT'

Socle installé. Aucune clé et aucun compte n'ont été configurés.
Fermer complètement la session utilisateur puis la rouvrir pour appliquer les
groupes docker et dialout. Ensuite lancer :

  bash scripts/valider-socle-dev.sh
TXT
