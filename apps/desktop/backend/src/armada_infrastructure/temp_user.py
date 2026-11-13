# TEMP stub: the desktop has no sign-in yet, so it invents one random user ID per Windows user and
# keeps it in a file, so legal agreements can be recorded on the application server against it.
# Filling it in: once sign-in exists, the signed-in user's UserId replaces this in
# armada_app/composition.py, this file is deleted, and the server makes AgreementService
# authenticated, taking the user from the caller instead of the request.
from pathlib import Path
from uuid import UUID, uuid4

from core_domain.ids import UserId


def temp_user_id(path: Path) -> UserId:
    """The ID kept at path, created there on first use."""
    if path.is_file():
        try:
            return UserId(UUID(path.read_text(encoding="utf-8").strip()))
        except ValueError:
            pass  # A damaged file is replaced, which only asks this user to accept again.
    user_id = UserId(uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(user_id.value), encoding="utf-8")
    return user_id
