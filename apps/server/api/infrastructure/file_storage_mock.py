# Stub: stands in for the object store that will hold file bytes. Its upload URLs use the
# reserved .invalid domain, so they never resolve and clients skip the PUT, and it reports every
# file as uploaded. Replacing it means a FileStorage that returns presigned PUT URLs and checks
# the stored object's size and SHA-256 in has_upload.
from core_domain.file import File
from core_domain.ids import FileId


class MockFileStorage:
    def upload_url(self, file_id: FileId) -> str:
        return f"https://upload.invalid/{file_id}"

    async def has_upload(self, file: File) -> bool:
        return True
