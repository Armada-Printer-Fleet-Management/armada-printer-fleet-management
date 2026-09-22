#!/usr/bin/env bash
set -euo pipefail

# Copies a Bruno collection from bruno/public into bruno/private, overwriting
# any existing copy, and adds the shared bruno/.env so the private copy has
# credentials the public one can't carry. The copy is renamed with a
# "_private" suffix, in the folder and in its opencollection.yml, so it's
# obvious in the Bruno desktop UI which copy you're working in.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -ne 1 ]; then
    echo "Usage: $(basename "$0") <collection-name>" >&2
    exit 1
fi

COLLECTION_NAME="$1"
PRIVATE_NAME="${COLLECTION_NAME}_private"
SRC_DIR="$SCRIPT_DIR/public/$COLLECTION_NAME"
DEST_DIR="$SCRIPT_DIR/private/$PRIVATE_NAME"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -d "$SRC_DIR" ]; then
    echo "No collection named '$COLLECTION_NAME' in $SCRIPT_DIR/public" >&2
    exit 1
fi

rm -rf "$DEST_DIR"
cp -r "$SRC_DIR" "$DEST_DIR"

MANIFEST="$DEST_DIR/opencollection.yml"
if [ -f "$MANIFEST" ]; then
    sed -i "s/^\(\s*name:\s*\)$COLLECTION_NAME\s*\$/\1$PRIVATE_NAME/" "$MANIFEST"
fi

if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$DEST_DIR/.env"
else
    echo "Warning: no .env found at $ENV_FILE, skipping" >&2
fi

echo "Copied '$COLLECTION_NAME' to $DEST_DIR"
