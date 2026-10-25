#!/usr/bin/env bash
# Installs Armada on a Linux machine that already has Docker, then hands over to the armada
# command, which manages the installation from then on. Run it once, as root:
#
#   sudo bash install.sh [--domain <name>] [--admin-email <address>]
#                        [--update-policy notify|auto|off] [--update-window HH:MM-HH:MM]
#                        [--update-interval <time span>] [--version <version>|latest]
#                        [--track production|staging|testing] [--non-interactive]
#
# Each option answers one question in advance; anything not given is asked, unless
# --non-interactive is set, which makes a missing answer an error. Running it again on an
# installed machine keeps its generated passwords, so a reinstall finds its data.
#
# A GitHub release's copy installs production. The copy inside the private release image installs
# testing or staging, and needs `docker login ghcr.io` with read access to the preview packages.
#
# release.sh stamps the @ARMADA_…@ values below. The ARMADA_… environment variables override
# them, which is how the tests point it at a local registry.
set -euo pipefail

CHANNEL="${ARMADA_CHANNEL:-@ARMADA_CHANNEL@}"
RELEASE_VERSION="${ARMADA_VERSION:-@ARMADA_VERSION@}"
RELEASE_URL="${ARMADA_RELEASE_URL:-https://github.com/@ARMADA_REPOSITORY@/releases/download}"
IMAGE_OWNER="${ARMADA_IMAGE_OWNER:-@ARMADA_IMAGE_OWNER@}"
REGISTRY="${ARMADA_REGISTRY:-ghcr.io}"
ARMADA_HOME=/opt/armada
ENV_FILE="$ARMADA_HOME/.env"
BIN=/usr/local/bin/armada

# Colour only for a person at a terminal, as in armada.
colour() { [ -t "$1" ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != dumb ]; }
if colour 1; then BOLD=$'\e[1m' RESET=$'\e[0m'; else BOLD="" RESET=""; fi
if colour 2; then ERR_RED=$'\e[31m' ERR_RESET=$'\e[0m'; else ERR_RED="" ERR_RESET=""; fi

die() {
  printf '%sinstall: %s%s\n' "$ERR_RED" "$*" "$ERR_RESET" >&2
  exit 1
}

# Tracks are shown only on the preview channel; production installs have exactly one.
usage() {
  cat <<EOF
Installs Armada on a Linux machine that already has Docker. Run it once, as root:

  sudo bash install.sh [--domain <name>] [--admin-email <address>]
                       [--update-policy notify|auto|off] [--update-window HH:MM-HH:MM]
                       [--update-interval <time span>] [--version <version>|latest]
                       [--non-interactive]

Each option answers one question in advance; anything not given is asked, unless
--non-interactive is set, which makes a missing answer an error. Running it again on an
installed machine keeps its generated passwords, so a reinstall finds its data.

  --version <version>|latest  The version to install: this installer's own, $RELEASE_VERSION,
                              unless another is given. latest is the newest available.
EOF
  if [ "$CHANNEL" = preview ]; then
    cat <<'EOF'

  --track testing|staging    The track to follow; testing by default. Needs
                             docker login ghcr.io with read access to the preview packages.
EOF
  fi
}

# ── options ──────────────────────────────────────────────────────────────────────────────────────

version=$RELEASE_VERSION
track=""
settings=()
while [ $# -gt 0 ]; do
  case "$1" in
    --version) version=${2:?--version needs a value}; shift ;;
    --track) track=${2:?--track needs a value}; shift ;;
    --domain | --admin-email | --update-policy | --update-interval)
      settings+=("$1" "${2:?$1 needs a value}"); shift ;;
    --update-window) settings+=("$1" "${2-}"); shift ;;
    --non-interactive) settings+=("$1") ;;
    -h | --help)
      usage
      exit 0
      ;;
    *) die "'$1' is not a valid option. See --help." ;;
  esac
  shift
done

[[ $CHANNEL$RELEASE_VERSION$RELEASE_URL$IMAGE_OWNER != *@ARMADA_* ]] ||
  die "This copy of install.sh was not taken from a release. Download it from the releases page."
# Each channel installs only its own tracks: preview images are private, release images public.
case "$CHANNEL" in
  release)
    channel_tracks='^production$' default_track=production image_suffix=""
    wrong_track="Testing and staging builds are private and installed from the preview channel. To install Armada, use --track production (the default)."
    ;;
  preview)
    channel_tracks='^(testing|staging)$' default_track=testing image_suffix=-preview
    wrong_track="This installer is for testing and staging. Production installs from the GitHub release."
    ;;
  *) die "Unknown channel: $CHANNEL" ;;
esac
[ -z "$track" ] || [[ $track =~ $channel_tracks ]] ||
  die "'$track' is not a valid track for this installer. $wrong_track"

cat <<'EOF'

    _                             _
   / \   _ __ _ __ ___   __ _  __| | __ _
  / _ \ | '__| '_ ` _ \ / _` |/ _` |/ _` |
 / ___ \| |  | | | | | | (_| | (_| | (_| |
/_/   \_\_|  |_| |_| |_|\__,_|\__,_|\__,_|

EOF
if [ "$CHANNEL" = preview ]; then
  echo "Installer for testing and staging builds"
else
  echo "Installer for Armada $RELEASE_VERSION"
fi
echo

# ── what this machine needs ──────────────────────────────────────────────────────────────────────

docker_docs() {
  local id=""
  # shellcheck source=/dev/null
  [ -r /etc/os-release ] && id=$(. /etc/os-release && printf '%s' "${ID:-}")
  case "$id" in
    ubuntu | debian | fedora | centos | rhel | raspbian | sles)
      printf 'https://docs.docker.com/engine/install/%s/' "$id" ;;
    *) printf 'https://docs.docker.com/engine/install/' ;;
  esac
}

[ "$(id -u)" -eq 0 ] || die "Run as root: sudo bash install.sh"
[ -d /run/systemd/system ] || die "Armada needs a machine that runs systemd."
for tool in curl flock sha256sum awk getent; do
  command -v "$tool" >/dev/null || die "$tool is required. Install it with your package manager."
done
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  die "Docker Engine with the Compose plugin is required. Install it as described at $(docker_docs), then run this again."
fi
docker info >/dev/null 2>&1 || die "Docker is installed but not running. Start it: systemctl start docker"

# A reinstall keeps the machine's track unless told otherwise.
if [ -z "$track" ]; then
  [ -f "$ENV_FILE" ] && track=$(sed -n 's/^TRACK=//p' "$ENV_FILE" | tail -n 1)
  [[ $track =~ $channel_tracks ]] || track=$default_track
fi

# Preview builds are private, so a machine without access stops here with what to do, not later
# with a Docker error.
if [ "$CHANNEL" = preview ]; then
  probe="$REGISTRY/$IMAGE_OWNER/armada-release-preview:$track"
  docker pull --quiet "$probe" >/dev/null 2>&1 ||
    die "Could not pull $probe. Log in first with an account that can read the preview packages: docker login $REGISTRY"
fi

# ── the armada command, from this release ────────────────────────────────────────────────────────

# The preview channel's files arrive beside this script, out of the release image.
if [ "$CHANNEL" = preview ]; then
  download=$(cd "$(dirname "$0")" && pwd)
else
  download=$(mktemp -d)
  trap 'rm -rf "$download"' EXIT
  for file in SHA256SUMS armada; do
    curl -fsSL --retry 3 -o "$download/$file" "$RELEASE_URL/v$RELEASE_VERSION/$file" ||
      die "Could not download $file from $RELEASE_URL/v$RELEASE_VERSION."
  done
fi
(cd "$download" && grep -E ' [ *]armada$' SHA256SUMS | sha256sum --quiet --strict -c -) ||
  die "The armada command failed its checksum check. Nothing was installed."
install -m 0755 "$download/armada" "$BIN"

# ── settings, with passwords generated rather than asked ─────────────────────────────────────────

# Same formats as scripts/compose_run.py: Garage wants hex secrets and an access key starting GK.
random_hex() { od -An -N"$1" -tx1 /dev/urandom | tr -d ' \n'; }

set_kv() {
  local tmp
  tmp=$(mktemp "$ENV_FILE.XXXXXX")
  KEY=$1 VALUE=$2 awk '
    index($0, ENVIRON["KEY"] "=") == 1 { if (!done) print ENVIRON["KEY"] "=" ENVIRON["VALUE"]; done = 1; next }
    { print }
    END { if (!done) print ENVIRON["KEY"] "=" ENVIRON["VALUE"] }
  ' "$ENV_FILE" >"$tmp"
  mv -f "$tmp" "$ENV_FILE"
}

install -d -m 0755 "$ARMADA_HOME"
if [ ! -f "$ENV_FILE" ]; then
  (
    umask 077
    cat >"$ENV_FILE" <<EOF
# Armada's settings. Change them with: armada config <key> <value>, or armada reconfigure.
# The generated values are stored by the database and file storage on their first start; changing
# them locks the installation out of its own data.
DB_PASSWORD=$(random_hex 16)
GARAGE_RPC_SECRET=$(random_hex 32)
GARAGE_DEFAULT_ACCESS_KEY=GK$(random_hex 16)
GARAGE_DEFAULT_SECRET_KEY=$(random_hex 32)
GARAGE_DEFAULT_BUCKET=armada
KEYCLOAK_DB_PASSWORD=$(random_hex 16)
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=$(random_hex 16)
VERSION=
EOF
  )
fi
set_kv GHCR_OWNER "$IMAGE_OWNER"
set_kv RELEASE_URL "$RELEASE_URL"
set_kv REGISTRY "$REGISTRY"
set_kv TRACK "$track"
set_kv IMAGE_SUFFIX "$image_suffix"

# ── hand over to the armada command ──────────────────────────────────────────────────────────────

"$BIN" reconfigure --install ${settings[@]+"${settings[@]}"}
echo
"$BIN" update "$version" || die "Armada did not start. See: armada logs"
# An older version than the newest is replaced by automatic updates at the next check; this says
# so, and records what is available for armada status.
if [ "$("$BIN" config update-policy)" != off ]; then
  echo
  "$BIN" check-for-updates || true
fi

domain=$("$BIN" config domain)
case "$domain" in
  :*)
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -n "$ip" ] || ip="<this machine's address>"
    address="http://$ip${domain#:80}"
    ;;
  *) address="https://$domain" ;;
esac
policy=$("$BIN" config update-policy)
case "$policy" in
  notify) policy_text="notify: you are told when a new version exists; nothing installs itself" ;;
  auto) policy_text="auto: new versions install themselves" ;;
  off) policy_text="off: nothing checks for new versions" ;;
esac
cat <<EOF

${BOLD}Armada $("$BIN" version) is running at $address${RESET}

  Updates   $policy_text
            change with: armada config update-policy <notify|auto|off>
  Status    armada status
  Logs      armada logs
  Help      armada help
EOF
