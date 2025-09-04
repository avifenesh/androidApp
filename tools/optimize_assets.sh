#!/usr/bin/env bash
set -euo pipefail

# Optimize gallery assets by downscaling and converting to WebP.
# - Requires: ImageMagick (mogrify/convert) and cwebp (from libwebp).
# - Usage examples:
#   tools/optimize_assets.sh app/src/main/assets/animals 2048 80
#     ^ downscale to max 2048px on longest side and WebP quality 80.

ASSET_DIR=${1:-app/src/main/assets/animals}
MAX_DIM=${2:-2048}
QUALITY=${3:-80}

if ! command -v mogrify >/dev/null 2>&1; then
  echo "ImageMagick 'mogrify' not found. Install ImageMagick." >&2
  exit 1
fi
if ! command -v cwebp >/dev/null 2>&1; then
  echo "'cwebp' not found. Install libwebp tools." >&2
  exit 1
fi

shopt -s nullglob nocaseglob
pushd "$ASSET_DIR" >/dev/null

echo "Downscaling large JPG/PNG to <= ${MAX_DIM}px..."
mogrify -resize ${MAX_DIM}x${MAX_DIM}\> -strip *.jpg *.jpeg *.png || true

echo "Converting to WebP (q=${QUALITY})..."
for f in *.jpg *.jpeg *.png; do
  [ -e "$f" ] || continue
  base="${f%.*}"
  out="${base}.webp"
  if [ ! -f "$out" ]; then
    cwebp -q "$QUALITY" "$f" -o "$out" >/dev/null
  fi
done

echo "Removing original JPG/PNG where WebP exists..."
for f in *.jpg *.jpeg *.png; do
  [ -e "$f" ] || continue
  base="${f%.*}"
  if [ -f "${base}.webp" ]; then
    rm -f "$f"
  fi
done

echo "Done. Remaining files:" 
ls -lh | sed -n '1,200p'

popd >/dev/null
exit 0

