#!/usr/bin/env bash
# Render a Mermaid diagram to SVG or PNG using mermaid-cli.
#
# Usage:
#   ./scripts/render-mermaid.sh <input.mmd> [output.png|.svg]
#
# Output defaults to the same path as the input, with a .png extension.
# Requires Node/npx. The first run downloads mermaid-cli and a headless
# Chromium, so it is slow once.

set -euo pipefail

input="${1:?usage: render-mermaid.sh <input.mmd> [output.svg|.png]}"
output="${2:-${input%.mmd}.png}"

npx --yes @mermaid-js/mermaid-cli \
  --input "$input" \
  --output "$output" \
  --backgroundColor white

# mermaid-cli writes width="100%" and no height, which makes <img> sizing
# unpredictable. Pin the size to the viewBox so it renders deterministically.
case "$output" in
  *.svg)
    node -e '
      const fs = require("fs");
      const p = process.argv[1];
      let s = fs.readFileSync(p, "utf8");
      const m = s.match(/viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"/);
      if (m) s = s.replace(/width="[^"]*"/, `width="${m[3]}" height="${m[4]}"`);
      fs.writeFileSync(p, s);
    ' "$output"
    ;;
esac

echo "Wrote $output"
