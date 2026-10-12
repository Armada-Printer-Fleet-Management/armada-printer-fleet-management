import os

# api.main builds the file store from these when it is imported. Nothing connects to the store
# until a request uses it, so placeholders are enough for every test that imports the app.
for name, value in {
    "FILE_STORE_ENDPOINT_URL": "http://file-store.invalid",
    "FILE_STORE_REGION": "test",
    "FILE_STORE_BUCKET": "test",
    "FILE_STORE_ACCESS_KEY": "test",
    "FILE_STORE_SECRET_KEY": "test",
}.items():
    os.environ.setdefault(name, value)
