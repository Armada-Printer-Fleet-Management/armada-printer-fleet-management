from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"
API_PREFIX = "/api"
S3_FILE_STORE_BACKEND = "s3"
FILES_PATH = "/files"
OIDC_AUTH_BACKEND = "oidc"
