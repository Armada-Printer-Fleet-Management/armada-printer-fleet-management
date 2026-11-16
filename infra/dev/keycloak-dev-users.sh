#!/usr/bin/env bash
# Development stack only: gives the armada realm one user per role, admin, staff and student, each
# named after its role and signing in with DEV_USER_PASSWORD. A user that already exists is left
# alone, so restarting the stack changes nothing.
set -euo pipefail

kcadm=/opt/keycloak/bin/kcadm.sh
config=/tmp/kcadm.config
realm=armada

"$kcadm" config credentials --config "$config" --server http://keycloak:8080/auth \
  --realm master --user "$KEYCLOAK_ADMIN_USERNAME" --password "$KEYCLOAK_ADMIN_PASSWORD"

for role in admin staff student; do
  existing=$("$kcadm" get users --config "$config" -r "$realm" -q username="$role" -q exact=true \
    --fields id --format csv --noquotes)
  if [ -n "$existing" ]; then
    echo "dev user $role already exists"
    continue
  fi
  # Keycloak's user profile asks for a name and email at first sign-in unless they are set.
  "$kcadm" create users --config "$config" -r "$realm" -s username="$role" -s enabled=true \
    -s email="$role@example.com" -s emailVerified=true -s firstName=Dev -s lastName="$role"
  "$kcadm" set-password --config "$config" -r "$realm" --username "$role" \
    --new-password "$DEV_USER_PASSWORD"
  "$kcadm" add-roles --config "$config" -r "$realm" --uusername "$role" --rolename "$role"
  echo "created dev user $role"
done
