"""Tests for scripts/compose_run.py: which settings it fills into each stack's env file.

Standard library only, like the script:

    python -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import compose_run


class DevUserPasswordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.config = mock.patch.object(compose_run, "CONFIG", Path(self.temp.name))
        self.config.start()

    def tearDown(self) -> None:
        self.config.stop()
        self.temp.cleanup()

    def test_only_the_dev_stack_gets_the_dev_user_password(self) -> None:
        dev = compose_run.read_env(compose_run.prepare_env("dev", None, None))
        deploy = compose_run.read_env(
            compose_run.prepare_env("deploy", ":80", "ops@example.com")
        )

        self.assertEqual(dev.get("DEV_USER_PASSWORD"), "123456")
        self.assertNotIn("DEV_USER_PASSWORD", deploy)


if __name__ == "__main__":
    unittest.main()
