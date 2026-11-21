import pytest

from api.common.paging import PageSizes

SIZES = PageSizes(default=20, maximum=50)


@pytest.mark.parametrize("requested", [0, -1], ids=["zero", "negative"])
def test_asking_for_no_size_gives_the_default(requested: int) -> None:
    assert SIZES.size(requested) == 20


@pytest.mark.parametrize("requested", [1, 20, 50], ids=["smallest", "default", "maximum"])
def test_a_size_within_range_is_kept(requested: int) -> None:
    assert SIZES.size(requested) == requested


def test_a_size_over_the_maximum_is_capped() -> None:
    assert SIZES.size(51) == 50
