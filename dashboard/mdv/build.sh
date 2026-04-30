#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MDV_SHA="${MDV_SHA:-b9d5a8c1bb66b094a8745775cb9bf1389f08403f}"
MDV_CACHE_ROOT="${XDG_CACHE_HOME:-${HOME:-${TMPDIR:-/tmp}}/.cache}/fusion_issue_analysis"
MDV_CACHE_DIR="${MDV_CACHE_DIR:-${MDV_CACHE_ROOT}/mdv-${MDV_SHA}}"
NPM_CACHE_DIR="${npm_config_cache:-${NPM_CONFIG_CACHE:-${HOME:-${TMPDIR:-/tmp}}/.npm}}"

export npm_config_cache="$NPM_CACHE_DIR"
export PUPPETEER_SKIP_DOWNLOAD="${PUPPETEER_SKIP_DOWNLOAD:-1}"

mkdir -p "$(dirname "$MDV_CACHE_DIR")" "$npm_config_cache"

if [ ! -d "$MDV_CACHE_DIR/.git" ]; then
  git clone https://github.com/drasimwagan/mdv.git "$MDV_CACHE_DIR"
fi

git -C "$MDV_CACHE_DIR" fetch --depth 1 origin "$MDV_SHA"
git -C "$MDV_CACHE_DIR" checkout --detach "$MDV_SHA"

MDV_CLI="$MDV_CACHE_DIR/packages/mdv-cli/dist/index.js"
if [ ! -f "$MDV_CLI" ] || [ ! -d "$MDV_CACHE_DIR/node_modules" ]; then
  (
    cd "$MDV_CACHE_DIR"
    npm install --prefer-offline --no-audit --no-fund --include-workspace-root --workspaces --package-lock=false --silent
    npm run build --workspace @mdv/core --silent
    npm run build --workspace @mdv/cli --silent
  )
fi

uv run python3 "$HERE/generate_data.py"
node "$MDV_CLI" render "$HERE/dashboard.mdv" --out "$HERE/index.html"
