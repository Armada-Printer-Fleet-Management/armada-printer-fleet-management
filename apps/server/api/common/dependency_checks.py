import asyncio
from collections.abc import Awaitable, Callable, Mapping

DependencyCheck = Callable[[], Awaitable[bool]]


async def run_dependency_checks(checks: Mapping[str, DependencyCheck]) -> dict[str, str]:
    # A check that raises counts as a failure; its message is deliberately not reported,
    # because it can carry internal details such as hostnames.
    results = await asyncio.gather(*(check() for check in checks.values()), return_exceptions=True)
    return {
        name: "pass" if result is True else "fail"
        for name, result in zip(checks.keys(), results, strict=True)
    }


def all_passed(dependencies: Mapping[str, str]) -> bool:
    return all(status == "pass" for status in dependencies.values())
