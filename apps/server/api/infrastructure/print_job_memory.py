# Stub: keeps print jobs in process memory, so the other apps can integrate before the server has
# a database. Everything is lost on restart. Replacing it means writing a SqlPrintJobRepository
# that passes tests/contract/test_print_job_repository.py and constructing that in api/main.py.
import base64
import binascii
from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from core_domain.ddd import EntityNotFound, InvalidPageToken, Page
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob

type _SortKey = tuple[datetime, UUID]


def _sort_key(print_job: PrintJob) -> _SortKey:
    return print_job.created_at, print_job.id.value


# The token is the last item's sort key, the same keyset a SQL adapter would page by.
def _encode_token(key: _SortKey) -> str:
    created_at, id_value = key
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{id_value}".encode()).decode()


def _decode_token(token: str) -> _SortKey:
    try:
        created_at, id_value = base64.urlsafe_b64decode(token).decode().split("|")
        key = datetime.fromisoformat(created_at), UUID(id_value)
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise InvalidPageToken() from error
    # A naive timestamp cannot be compared with the stored aware ones.
    if key[0].tzinfo is None:
        raise InvalidPageToken()
    return key


class InMemoryPrintJobRepository:
    def __init__(self, print_jobs: Iterable[PrintJob] = ()) -> None:
        self._print_jobs = {print_job.id: print_job for print_job in print_jobs}

    async def get(self, entity_id: PrintJobId) -> PrintJob:
        if entity_id not in self._print_jobs:
            raise EntityNotFound(entity_id)
        # A copy, as a database would return, so a change is only stored once it is saved.
        return replace(self._print_jobs[entity_id])

    async def save(self, entity: PrintJob) -> None:
        self._print_jobs[entity.id] = replace(entity)

    async def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        newest_first = sorted(self._print_jobs.values(), key=_sort_key, reverse=True)
        if page_token:
            after = _decode_token(page_token)
            newest_first = [job for job in newest_first if _sort_key(job) < after]
        items = [replace(job) for job in newest_first[:page_size]]
        more = len(newest_first) > page_size
        return Page(items, _encode_token(_sort_key(items[-1])) if more else "")
