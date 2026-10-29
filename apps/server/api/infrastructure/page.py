import base64
import binascii
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from core_domain.ddd import InvalidPageToken, Page, TypedId

type SortKey = tuple[datetime, UUID]


# Read-only properties, so an entity whose id is a TypedId subclass still matches.
class _Keyed(Protocol):
    @property
    def id(self) -> TypedId: ...

    @property
    def created_at(self) -> datetime: ...


def sort_key(entity: _Keyed) -> SortKey:
    return entity.created_at, entity.id.value


# The token is the last item's sort key, so every adapter paging newest first by
# (created_at, id) issues and accepts the same tokens.
def encode_token(key: SortKey) -> str:
    created_at, id_value = key
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{id_value}".encode()).decode()


def decode_token(token: str) -> SortKey:
    try:
        created_at, id_value = base64.urlsafe_b64decode(token).decode().split("|")
        key = datetime.fromisoformat(created_at), UUID(id_value)
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise InvalidPageToken() from error
    # A naive timestamp cannot be compared with the stored aware ones.
    if key[0].tzinfo is None:
        raise InvalidPageToken()
    return key


def newest_first_page[EntityT: _Keyed](
    entities: Iterable[EntityT], page_size: int, page_token: str
) -> Page[EntityT]:
    """Pages entities held in memory. Returns them as given; copying is the caller's concern."""
    newest_first = sorted(entities, key=sort_key, reverse=True)
    if page_token:
        after = decode_token(page_token)
        newest_first = [entity for entity in newest_first if sort_key(entity) < after]
    items = newest_first[:page_size]
    more = len(newest_first) > page_size
    return Page(items, encode_token(sort_key(items[-1])) if more else "")
