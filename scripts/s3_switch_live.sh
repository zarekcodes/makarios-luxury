#!/usr/bin/env bash
# The blue/green switch: point the class S3 folder's pointer at one slot.
#
#   S3_BUCKET=<bucket> S3_PREFIX=<your folder> scripts/s3_switch_live.sh green
#   scripts/s3_switch_live.sh green --dry-run     # print the pointer, upload nothing
#
# The deploy job (.github/workflows/ci.yml) uploads a build into
# <folder>/blue/ or <folder>/green/ and changes nothing else, so a deploy never
# changes what visitors get. This is the release: it rewrites the two small
# files at the root of the folder, index.html (sends a visitor to the live
# slot) and live.json (which slot is live, for scripts and evidence). Rolling
# back is running it again with the other color; that slot's build is still there.
#
# Needs the AWS CLI with the class credentials (aws configure, or the
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY variables). docs/DEPLOY.md has
# the whole sequence.
set -euo pipefail

color="${1:-}"
dry_run=false
[[ "${2:-}" == "--dry-run" ]] && dry_run=true
case "$color" in
  blue | green) ;;
  *)
    echo "usage: $0 blue|green [--dry-run]" >&2
    exit 2
    ;;
esac

switched_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

cat >"$workdir/index.html" <<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex">
  <meta http-equiv="refresh" content="0; url=${color}/index.html">
  <title>Makarios Luxury: ${color} is live</title>
</head>
<body>
  <p>Live slot: <strong>${color}</strong>, since ${switched_at}.
     <a href="${color}/index.html">Go to the ${color} build</a>.</p>
</body>
</html>
HTML

printf '{\n  "live": "%s",\n  "switched_at": "%s"\n}\n' "$color" "$switched_at" >"$workdir/live.json"

if $dry_run; then
  echo "== index.html"
  cat "$workdir/index.html"
  echo "== live.json"
  cat "$workdir/live.json"
  exit 0
fi

: "${S3_BUCKET:?set S3_BUCKET to the class bucket}"
: "${S3_PREFIX:?set S3_PREFIX to your folder in it}"
base="s3://${S3_BUCKET}/${S3_PREFIX%/}"

# Refuse to send visitors to a slot that was never deployed.
if ! deployed="$(aws s3 cp "${base}/${color}/version.json" - 2>/dev/null)"; then
  echo "Nothing is deployed in ${color}/ yet: run the deploy job for ${color} first." >&2
  exit 1
fi
echo "Switching to ${color}:"
echo "$deployed"
previous="$(aws s3 cp "${base}/live.json" - 2>/dev/null || echo '(no pointer yet)')"
echo "Was: ${previous}"

# no-cache, so the switch is seen at once rather than after a cached copy expires.
aws s3 cp "$workdir/index.html" "${base}/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache"
aws s3 cp "$workdir/live.json" "${base}/live.json" \
  --content-type "application/json" --cache-control "no-cache"
echo "Live: ${color}. Roll back with: $0 $([[ $color == blue ]] && echo green || echo blue)"
