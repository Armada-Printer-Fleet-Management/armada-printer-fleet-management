#!/usr/bin/env bash
# Gives the armada realm one user per role, admin, staff and student, each named after its role and
# signing in with DEV_USER_PASSWORD. Used by the development stack, and by e2e.ci.yml for the
# throwaway stack it tests; never by a deployed machine. Each user has a fixed ID, the subject the
# server's development data (apps/server/api/infrastructure/dev_data.py) stores for it. A user that
# already exists with its ID is left alone, so restarting the stack changes nothing.
set -euo pipefail

kcadm=/opt/keycloak/bin/kcadm.sh
config=/tmp/kcadm.config
realm=armada

declare -A user_ids=(
  [student]=00000000-0000-4000-8000-000000000110
  [staff]=00000000-0000-4000-8000-000000000111
  [admin]=00000000-0000-4000-8000-000000000112
)

"$kcadm" config credentials --config "$config" --server http://keycloak:8080/auth \
  --realm master --user "$KEYCLOAK_ADMIN_USERNAME" --password "$KEYCLOAK_ADMIN_PASSWORD"

for role in admin staff student; do
  id=${user_ids[$role]}
  existing=$("$kcadm" get users --config "$config" -r "$realm" -q username="$role" -q exact=true \
    --fields id --format csv --noquotes)
  if [ "$existing" = "$id" ]; then
    echo "dev user $role already exists"
    continue
  fi
  # Made before users had fixed IDs, so the server's data cannot refer to it.
  if [ -n "$existing" ]; then
    "$kcadm" delete "users/$existing" --config "$config" -r "$realm"
    echo "replacing dev user $role, whose ID did not match the server's development data"
  fi
  # Keycloak ignores a supplied ID when creating a user, but a partial import keeps it. Its name
  # and email are set because Keycloak's user profile asks for them at first sign-in otherwise.
  body=/tmp/dev-user-$role.json
  cat >"$body" <<EOF
{
  "ifResourceExists": "SKIP",
  "users": [
    {
      "id": "$id",
      "username": "$role",
      "enabled": true,
      "email": "$role@example.com",
      "emailVerified": true,
      "firstName": "Dev",
      "lastName": "$role"
    }
  ]
}
EOF
  "$kcadm" create partialImport --config "$config" -r "$realm" -f "$body" >/dev/null
  "$kcadm" set-password --config "$config" -r "$realm" --username "$role" \
    --new-password "$DEV_USER_PASSWORD"
  "$kcadm" add-roles --config "$config" -r "$realm" --uusername "$role" --rolename "$role"
  echo "created dev user $role"
done
