"""The dev users' Keycloak IDs are written twice, in the script that creates them and in the dev
data that refers to them, since bash and Python cannot share a constant."""

import re
from pathlib import Path

from api.infrastructure.dev_data import stub_users

DEV_USERS_SCRIPT = Path(__file__).parents[5] / "infra" / "dev" / "keycloak-dev-users.sh"
USER_ID = re.compile(r"^\s*\[(\w+)\]=([0-9a-f-]{36})\s*$", re.M)


def test_each_stub_user_refers_to_the_keycloak_user_of_its_role() -> None:
    keycloak_ids = dict(USER_ID.findall(DEV_USERS_SCRIPT.read_text()))
    stub_refs = {user.role.name.lower(): user.identity_provider_ref for user in stub_users()}

    assert keycloak_ids == stub_refs
