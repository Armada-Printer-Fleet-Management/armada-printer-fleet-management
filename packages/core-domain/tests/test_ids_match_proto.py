"""Drift guard: the ID kernel mirrors packages/proto/id/v1. Reads the .proto sources as text,
because core-domain may not depend on protobuf."""

import importlib
import re
from pathlib import Path

from core_domain.ddd import TypedId

PROTO_IDS = Path(__file__).resolve().parents[2] / "proto" / "id" / "v1"
KERNEL = Path(__file__).resolve().parents[1] / "src" / "core_domain" / "ids"


def test_every_proto_id_has_a_kernel_id_in_the_matching_module() -> None:
    for proto in sorted(PROTO_IDS.glob("*.proto")):
        module = importlib.import_module(f"core_domain.ids.{proto.stem}")
        for name in re.findall(r"^message (\w+)", proto.read_text(), re.MULTILINE):
            kernel_id = getattr(module, name, None)
            assert isinstance(kernel_id, type) and issubclass(kernel_id, TypedId), (
                f"{proto.name} defines {name}; add it to core_domain/ids/{proto.stem}.py"
            )


def test_every_kernel_module_has_a_proto() -> None:
    protos = {p.stem for p in PROTO_IDS.glob("*.proto")}
    modules = {p.stem for p in KERNEL.glob("*.py") if p.stem != "__init__"}
    assert modules <= protos, f"no id/v1 proto for {sorted(modules - protos)}"
