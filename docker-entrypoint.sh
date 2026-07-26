#!/bin/sh
# Description: Maps GitHub Action inputs to the wakIndex CLI and preserves normal CLI use.
set -eu

if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  scan_path="${INPUT_PATH:-.}"
  policy_path="${INPUT_POLICY:-wakindex-policy.toml}"
  output_path="${INPUT_OUTPUT:-wakindex.sarif}"
  exec wakindex check "$scan_path" --policy "$policy_path" --format sarif --output "$output_path"
fi

exec wakindex "$@"
