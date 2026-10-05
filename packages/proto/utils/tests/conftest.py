"""The compiled descriptors of packages/proto, shared by the contract-rule tests."""

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from google.protobuf.descriptor_pb2 import DescriptorProto, FileDescriptorSet

REPO_ROOT = Path(__file__).resolve().parents[4]

# (package, fully qualified message name, message)
type Message = tuple[str, str, DescriptorProto]


def _walk(package: str, prefix: str, messages: list[DescriptorProto]) -> Iterator[Message]:
    for message in messages:
        name = f"{prefix}.{message.name}"
        yield package, name, message
        yield from _walk(package, name, list(message.nested_type))


@pytest.fixture(scope="session")
def messages(tmp_path_factory: pytest.TempPathFactory) -> list[Message]:
    """Every message in the contract, nested ones included. Built with buf, which a missing
    install fails loudly rather than skipping."""
    image = tmp_path_factory.mktemp("buf") / "image.binpb"
    subprocess.run(
        ["buf", "build", "--exclude-imports", "-o", str(image)], cwd=REPO_ROOT, check=True
    )
    files = FileDescriptorSet.FromString(image.read_bytes()).file
    return [found for f in files for found in _walk(f.package, f.package, list(f.message_type))]
