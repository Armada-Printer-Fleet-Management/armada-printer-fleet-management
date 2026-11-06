"""production_parts() builds new parts on each call, so each app holds state of its own."""

from dataclasses import fields

from api.main import production_parts


def test_two_calls_share_no_domain_service() -> None:
    first, second = production_parts(), production_parts()

    for field in fields(first.services):
        assert getattr(first.services, field.name) is not getattr(second.services, field.name)


def test_two_calls_share_no_lifespan_resource() -> None:
    first, second = production_parts(), production_parts()

    assert len(first.resources) == len(second.resources)
    for first_resource, second_resource in zip(first.resources, second.resources, strict=True):
        assert first_resource is not second_resource
