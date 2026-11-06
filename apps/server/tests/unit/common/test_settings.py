from pydantic import SecretStr
from sqlalchemy.engine import make_url

from api.common.settings import DatabaseSettings


def test_the_database_url_quotes_reserved_characters() -> None:
    settings = DatabaseSettings(
        host="db.example.test",
        port=5433,
        name="armada",
        user="fleet@ops",
        password=SecretStr("p@ss:w/rd#1"),
    )

    url = make_url(settings.url())

    assert (url.username, url.password) == ("fleet@ops", "p@ss:w/rd#1")
    assert (url.host, url.port, url.database) == ("db.example.test", 5433, "armada")
