#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

for tool in git python3 docker; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Outil requis absent : %s\n' "$tool" >&2
    exit 1
  fi
done
if ! docker compose version >/dev/null 2>&1; then
  printf 'Docker Compose v2 est requis.\n' >&2
  exit 1
fi

git submodule update --init --recursive
mkdir -p private/empty-vault private/empty-inbox

new_install=false
if [[ ! -f .env ]]; then
  new_install=true
  python3 - <<'PY'
from pathlib import Path
import secrets

source = Path('deploy/.env.example').read_text()
legacy_path = Path.home() / '.config' / 'azoth' / 'veille-azoth.env'
legacy_password = ''
if legacy_path.is_file():
    for line in legacy_path.read_text().splitlines():
        if line.startswith('VEILLE_PASSWORD='):
            legacy_password = line.split('=', 1)[1].strip()
            break
values = {
    'MUTHUR_PASSWORD': legacy_password or secrets.token_urlsafe(28),
    'FREQTRADE_PASSWORD': secrets.token_urlsafe(32),
    'FREQTRADE_API_JWT_SECRET': secrets.token_hex(32),
    'FREQTRADE_WS_TOKEN': secrets.token_urlsafe(32),
    'FREQTRADE_JWT_SECRET': secrets.token_hex(32),
    'QUANT_RACK_AGENT_TOKEN': secrets.token_hex(32),
    'OBSIDIAN_VAULT_HOST_PATH': str(Path.home() / 'GoogleDrive' / 'SuperIA-Vault'),
    'OBSIDIAN_INBOX_HOST_PATH': str(Path.home() / 'GoogleDrive' / 'SuperIA-Inbox'),
}
for key, value in values.items():
    source = source.replace(f'{key}=GÉNÉRÉ_PAR_LE_SCRIPT', f'{key}={value}')
source = source.replace('FREQTRADE_ADMIN_PASSWORD=IDENTIQUE_AU_MUTHUR_PASSWORD', f"FREQTRADE_ADMIN_PASSWORD={values['MUTHUR_PASSWORD']}")
Path('.env').write_text(source)
Path('.env').chmod(0o600)
Path('.muthur-first-password').write_text(values['MUTHUR_PASSWORD'] + '\n')
Path('.muthur-first-password').chmod(0o600)
PY
  printf 'Configuration locale initialisée. Le mot de passe initial se trouve dans .muthur-first-password (fichier privé).\n'
fi

if command -v systemctl >/dev/null 2>&1 && systemctl --user list-unit-files ollama.service --no-legend 2>/dev/null | grep -q ollama.service; then
  systemctl --user start ollama.service
fi
if command -v systemctl >/dev/null 2>&1 && systemctl --user list-unit-files azoth-vault.service --no-legend 2>/dev/null | grep -q azoth-vault.service; then
  systemctl --user start azoth-vault.service || printf 'Montage Obsidian indisponible : le cockpit démarrera sans mémoire documentaire.\n' >&2
fi

vault="$HOME/GoogleDrive/SuperIA-Vault"
inbox="$HOME/GoogleDrive/SuperIA-Inbox"
if command -v mountpoint >/dev/null 2>&1 && mountpoint -q "$vault" && mountpoint -q "$inbox"; then
  python3 - "$vault" "$inbox" <<'PY'
from pathlib import Path
import sys
p=Path('.env'); text=p.read_text()
for key,value in [('OBSIDIAN_VAULT_HOST_PATH',sys.argv[1]),('OBSIDIAN_INBOX_HOST_PATH',sys.argv[2]),('AZOTH_VAULT_PATH','/mnt/vault'),('AZOTH_INBOX_PATH','/mnt/inbox')]:
 import re
 text=re.sub(rf'(?m)^{key}=.*$',f'{key}={value}',text)
p.write_text(text); p.chmod(0o600)
PY
else
  python3 - <<'PY'
from pathlib import Path
import re
p=Path('.env'); text=p.read_text()
for key,value in [('OBSIDIAN_VAULT_HOST_PATH','./private/empty-vault'),('OBSIDIAN_INBOX_HOST_PATH','./private/empty-inbox'),('AZOTH_VAULT_PATH',''),('AZOTH_INBOX_PATH','')]:
 text=re.sub(rf'(?m)^{key}=.*$',f'{key}={value}',text)
p.write_text(text); p.chmod(0o600)
PY
fi

docker compose --env-file .env -f compose.yaml build
docker compose --env-file .env -f components/freqtrade/docker-compose.coolify.yml build trading-terminal

if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  for unit in veille-azoth.service superia-web.service azoth-quant.service azoth.target; do
    if systemctl --user list-unit-files "$unit" --no-legend | grep -q "^${unit}[[:space:]]"; then
      systemctl --user disable --now "$unit" >/dev/null
    fi
  done
fi

# Le compose historique démarrait aussi le moteur. `down` conserve tous les
# volumes ; le nouveau déploiement ne relancera que l'interface Quant.
legacy_quant_root="$HOME/serveur-local/sources/freqtrade"
if [[ -r "$legacy_quant_root/.env" && -f "$legacy_quant_root/docker-compose.coolify.yml" ]]; then
  docker compose --env-file "$legacy_quant_root/.env" \
    -f "$legacy_quant_root/docker-compose.coolify.yml" down
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl --user start ollama.service || printf 'Ollama indisponible : le chat local sera hors ligne.\n' >&2
  systemctl --user start azoth-vault.service || printf 'Montage Obsidian indisponible : le cockpit démarrera sans mémoire documentaire.\n' >&2
fi

docker compose --env-file .env -f components/freqtrade/docker-compose.coolify.yml up -d trading-terminal
docker compose --env-file .env -f compose.yaml up -d

printf '\nMU-TH-UR est lancé : http://127.0.0.1:8765\n'
printf 'Le moteur Freqtrade reste arrêté. Pour ouvrir le panneau depuis le réseau local, configure le pare-feu selon ton sous-réseau.\n'
if [[ "$new_install" == true ]]; then
  printf 'Mot de passe initial conservé dans %s/.muthur-first-password (0600).\n' "$root"
fi
