import json

import pytest

from tests.integration.docker_stack import leftover_projects


@pytest.mark.parametrize("name", ["armada", "armada-testing", "armada-test", "other-test-ab12"])
def test_exited_projects_from_outside_the_integration_suite_are_never_removed(name: str) -> None:
    listed = json.dumps([{"Name": name, "Status": "exited(3)", "ConfigFiles": "compose.yaml"}])

    assert leftover_projects(listed) == []
