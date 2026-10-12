from plugin_api.file_store import FileStoreError, StoredFileNotFoundError


def test_a_missing_file_is_a_file_store_error() -> None:
    """Code that handles any store failure also handles a missing file."""
    assert issubclass(StoredFileNotFoundError, FileStoreError)
