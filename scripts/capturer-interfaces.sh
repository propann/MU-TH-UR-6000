#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
capture_dir="${project_root}/docs/captures"
firefox_bin="${FIREFOX_BIN:-/usr/bin/firefox}"

if [[ ! -x "${firefox_bin}" ]]; then
  echo "ERREUR  Firefox introuvable : ${firefox_bin}"
  exit 1
fi

mkdir -p "${capture_dir}"

capture() {
  local name="$1"
  local url="$2"

  "${firefox_bin}" --headless --no-remote \
    --screenshot "${capture_dir}/${name}.png" \
    --window-size 1440,1000 "${url}"
  echo "CRÉÉ    ${capture_dir}/${name}.png"
}

capture "cockpit" "${AZOTH_COCKPIT_URL:-http://127.0.0.1:8765/}"
capture "ia-locale" "${SUPERIA_URL:-http://127.0.0.1:3210/}"
capture "quant-core" "${QUANT_CORE_URL:-http://127.0.0.1:3000/quant/}"

echo "ATTENTION  Relire chaque image avant git add -f docs/captures/*.png"
