#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LIBRARY_DIR="${REPO_ROOT}/library"
NORMALIZER="${SCRIPT_DIR}/path_normalizer.py"

if [[ ! -d "${LIBRARY_DIR}" ]]; then
  echo "error: library directory not found at ${LIBRARY_DIR}" >&2
  exit 1
fi

mapfile -t JSON_FILES < <(find "${LIBRARY_DIR}" -type f -name '*.json' | sort)

if [[ ${#JSON_FILES[@]} -eq 0 ]]; then
  echo "error: no JSON files found under ${LIBRARY_DIR}" >&2
  exit 1
fi

TOTAL_REPLACEMENTS=0
SUSPICIOUS_FILES=()

for json_file in "${JSON_FILES[@]}"; do
  output="$("${NORMALIZER}" "${json_file}")"
  printf '%s\n' "${output}"

  replacements="$(printf '%s\n' "${output}" | awk -F': ' '/^Paths replaced:/ { print $2 }')"
  replacements="${replacements:-0}"
  TOTAL_REPLACEMENTS=$((TOTAL_REPLACEMENTS + replacements))

  if [[ "${replacements}" -eq 0 ]]; then
    SUSPICIOUS_FILES+=("${json_file}")
  fi
done

echo "Total replacements: ${TOTAL_REPLACEMENTS}"

if [[ ${#SUSPICIOUS_FILES[@]} -gt 0 ]]; then
  echo "error: files with 0 replacements (suspicious):" >&2
  for file in "${SUSPICIOUS_FILES[@]}"; do
    echo "  - ${file}" >&2
  done
  exit 1
fi

exit 0
