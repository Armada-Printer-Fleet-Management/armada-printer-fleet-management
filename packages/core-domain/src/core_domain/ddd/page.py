from dataclasses import dataclass


@dataclass(frozen=True)
class Page[T]:
    """One page of a list. The token is opaque to everything but the repository that issued it."""

    items: list[T]
    next_page_token: str = ""
