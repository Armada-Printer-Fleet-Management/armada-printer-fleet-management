# Stub: one slice profile, written in code, for every slice. Adhesion is always a skirt, and
# students may only switch supports on or off: the engine reads that setting directly, while most
# others feed derived settings that nothing recomputes yet, so changing them would only half apply.
# Replacing it means deciding where profiles live (deployment configuration or the database) and
# what each one belongs to (a printer type or a queue), then writing that repository for
# api/domains/print_preparation/repository.py and constructing it in api/main.py.
from uuid import UUID

from core_domain.ddd import EntityNotFound
from core_domain.ids import SliceProfileId
from core_domain.print_preparation import SettingRange, SliceProfile

from api.domains.print_preparation.repository import SliceProfileRepository

STUB_SLICE_PROFILE_ID = SliceProfileId(UUID("00000000-0000-4000-8000-000000000701"))

_DEFAULT = SliceProfile(
    id=STUB_SLICE_PROFILE_ID,
    name="Default",
    fixed={"adhesion_type": "skirt"},
    adjustable={"support_enable": SettingRange()},
)


class StubSliceProfiles(SliceProfileRepository):
    async def get(self, entity_id: SliceProfileId) -> SliceProfile:
        if entity_id != STUB_SLICE_PROFILE_ID:
            raise EntityNotFound(entity_id)
        return _DEFAULT

    async def default(self) -> SliceProfile:
        return _DEFAULT
