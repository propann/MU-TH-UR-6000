#!/usr/bin/env bash
set -uo pipefail

errors=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf 'OK      %s\n' "$label"
  else
    printf 'ATTENTE %s\n' "$label"
    errors=$((errors + 1))
  fi
}

check "Node >= 22.5" node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(a>22||(a===22&&b>=5)?0:1)'
check "npm" npm --version
check "Bun" bun --version
check "uv" uv --version
check "Docker utilisateur" docker info
check "Docker Compose" docker compose version
check "groupe dialout" bash -c 'id -nG | tr " " "\n" | grep -qx dialout'
check "Meshtastic CLI" bash -c 'command -v meshtastic'
check "PlatformIO" bash -c 'command -v pio'
check "MQTT client" bash -c 'command -v mosquitto_pub'
check "ADB" adb version
check "Git LFS" git lfs version
check "ShellCheck" shellcheck --version
check "VS Code Flatpak" flatpak info com.visualstudio.code

printf '\nPoints en attente : %d\n' "$errors"
exit "$errors"
