#!/usr/bin/env bash
#
# Build the site's CSS with the Tailwind standalone CLI.
#
# The standalone CLI is a single binary with Tailwind baked in, so this project
# needs no Node.js and no package.json. The binary is downloaded on first use
# into bin/ (gitignored) and reused after that.
#
# Usage:
#   ./scripts/tailwind.sh --watch     # development: rebuild on every save
#   ./scripts/tailwind.sh --minify    # what we commit and what ships
#
# Any arguments are passed straight through to the Tailwind CLI.

set -euo pipefail

# Single source of truth for the version, read by local dev AND by CI.
# CI rebuilds the CSS and byte-compares it against the committed file, so a
# version mismatch between your machine and CI shows up as a confusing diff.
# Bump this deliberately, never to a range or "latest".
TAILWIND_VERSION="v4.3.3"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${REPO_ROOT}/bin"
BIN="${BIN_DIR}/tailwindcss"
STAMP="${BIN_DIR}/.tailwind-version"

INPUT="${REPO_ROOT}/app/static/css/input.css"
OUTPUT="${REPO_ROOT}/app/static/css/app.css"

# Map this machine to the right release asset name.
detect_asset() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "${os}" in
    Linux) os="linux" ;;
    Darwin) os="macos" ;;
    *)
      echo "error: unsupported OS '${os}'." >&2
      echo "See https://github.com/tailwindlabs/tailwindcss/releases for available builds." >&2
      exit 1
      ;;
  esac

  case "${arch}" in
    x86_64 | amd64) arch="x64" ;;
    aarch64 | arm64) arch="arm64" ;;
    *)
      echo "error: unsupported architecture '${arch}'." >&2
      exit 1
      ;;
  esac

  echo "tailwindcss-${os}-${arch}"
}

# Download only when the binary is missing or is the wrong version.
ensure_binary() {
  if [[ -x "${BIN}" && -f "${STAMP}" && "$(cat "${STAMP}")" == "${TAILWIND_VERSION}" ]]; then
    return
  fi

  local asset url
  asset="$(detect_asset)"
  url="https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/${asset}"

  echo "Downloading Tailwind CLI ${TAILWIND_VERSION} (${asset})..." >&2
  mkdir -p "${BIN_DIR}"
  if ! curl -fsSL --retry 3 --retry-delay 2 -o "${BIN}.tmp" "${url}"; then
    echo "error: could not download ${url}" >&2
    rm -f "${BIN}.tmp"
    exit 1
  fi

  chmod +x "${BIN}.tmp"
  mv "${BIN}.tmp" "${BIN}"
  echo "${TAILWIND_VERSION}" >"${STAMP}"
}

ensure_binary
exec "${BIN}" -i "${INPUT}" -o "${OUTPUT}" "$@"
