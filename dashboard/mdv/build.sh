#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MDV_SHA="${MDV_SHA:-b9d5a8c1bb66b094a8745775cb9bf1389f08403f}"
MDV_CACHE_DIR="${MDV_CACHE_DIR:-${TMPDIR:-/tmp}/mdv-${MDV_SHA}}"

export npm_config_cache="${npm_config_cache:-${TMPDIR:-/tmp}/npm-cache-mdv}"
export PUPPETEER_SKIP_DOWNLOAD="${PUPPETEER_SKIP_DOWNLOAD:-1}"

if [ ! -d "$MDV_CACHE_DIR/.git" ]; then
  git clone https://github.com/drasimwagan/mdv.git "$MDV_CACHE_DIR"
fi

git -C "$MDV_CACHE_DIR" fetch --depth 1 origin "$MDV_SHA"
git -C "$MDV_CACHE_DIR" checkout --detach "$MDV_SHA"
(
  cd "$MDV_CACHE_DIR"
  npm install --include-workspace-root --workspaces --package-lock=false --silent
  npm run build --workspace @mdv/core --silent
  npm run build --workspace @mdv/cli --silent
)

uv run python3 "$HERE/generate_data.py"
node "$MDV_CACHE_DIR/packages/mdv-cli/dist/index.js" render "$HERE/dashboard.mdv" --out "$HERE/index.html"
