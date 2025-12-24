#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
input_dir="$root_dir/docs/diagrams"
output_dir="$root_dir/docs/diagrams/exports"

mkdir -p "$output_dir"

for file in "$input_dir"/*.mmd; do
  base_name="$(basename "${file%.mmd}")"
  npx -y @mermaid-js/mermaid-cli -i "$file" -o "$output_dir/$base_name.png" -e png -s 2
  printf 'Generated %s\n' "$output_dir/$base_name.png"
done
