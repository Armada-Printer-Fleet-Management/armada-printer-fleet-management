#!/usr/bin/env bash
# Creates the armada-e2e client the smoke tests sign in through: confidential, password grant only,
# with the armada-server audience the server requires. Run in the Keycloak image on the stack's
# network, against a throwaway target only. Never added to infra/deploy/armada-realm.json, which
# ships to production. An existing client is left alone.
set -euo pipefail

kcadm=/opt/keycloak/bin/kcadm.sh
config=/tmp/kcadm.config
realm=armada
client=armada-e2e

"$kcadm" config credentials --config "$config" --server http://keycloak:8080/auth \
  --realm master --user "$KEYCLOAK_ADMIN_USERNAME" --password "$KEYCLOAK_ADMIN_PASSWORD"

existing=$("$kcadm" get clients --config "$config" -r "$realm" -q clientId="$client" \
  --fields id --format csv --noquotes)
if [ -n "$existing" ]; then
  echo "client $client already exists"
  exit 0
fi

id=$("$kcadm" create clients --config "$config" -r "$realm" -i \
  -s clientId="$client" -s enabled=true -s protocol=openid-connect \
  -s publicClient=false -s secret="$E2E_AUTH_CLIENT_SECRET" \
  -s directAccessGrantsEnabled=true -s standardFlowEnabled=false \
  -s implicitFlowEnabled=false -s serviceAccountsEnabled=false)

# The same mapper armada-web has in armada-realm.json.
"$kcadm" create "clients/$id/protocol-mappers/models" --config "$config" -r "$realm" \
  -s name="armada-server audience" -s protocol=openid-connect \
  -s protocolMapper=oidc-audience-mapper \
  -s 'config."included.custom.audience"=armada-server' \
  -s 'config."access.token.claim"=true' \
  -s 'config."id.token.claim"=false'
echo "created client $client"
