#!/usr/bin/env bash
# Assembles the files a release publishes: the deploy stack, the armada command, its timer units
# and the installer, with the installer's @ARMADA_…@ values filled in, plus VERSION and SHA256SUMS
# over them all. Machines install exactly these. The release channel attaches them to a GitHub
# release; the preview channel packs them into the private release image.
#
#   infra/deploy/release.sh <preview|release> <version> <owner/repository> <image owner> <output directory>
set -euo pipefail

[ $# -eq 5 ] || {
  echo "usage: $0 <preview|release> <version> <owner/repository> <image owner> <output directory>" >&2
  exit 1
}
channel=$1 version=$2 repository=$3 owner=$4 out=$5
[[ $channel =~ ^(preview|release)$ ]] || {
  echo "$0: the channel must be preview or release, not $channel" >&2
  exit 1
}
deploy=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$out"
cp "$deploy/compose.yaml" "$deploy/garage.toml" "$deploy/armada" \
  "$deploy/systemd/armada-update.service" "$deploy/systemd/armada-update.timer" "$out/"
sed -e "s|@ARMADA_CHANNEL@|$channel|g" \
  -e "s|@ARMADA_VERSION@|$version|g" \
  -e "s|@ARMADA_REPOSITORY@|$repository|g" \
  -e "s|@ARMADA_IMAGE_OWNER@|$owner|g" \
  "$deploy/install.sh" >"$out/install.sh"
printf '%s\n' "$version" >"$out/VERSION"
(
  cd "$out"
  sha256sum compose.yaml garage.toml armada armada-update.service armada-update.timer install.sh \
    VERSION >SHA256SUMS
)
