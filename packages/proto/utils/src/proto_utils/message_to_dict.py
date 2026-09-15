from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message


def message_to_dict(message: Message) -> dict[str, object]:
    """Wraps google.protobuf.json_format.MessageToDict with
    always_print_fields_with_no_presence=True. Without it, a proto3 field set
    to its default value (0, "", False) is indistinguishable from "unset" and
    gets silently dropped. This could cause many bugs if it is not always
    available. Every service and app turning a message into a dict for
    IPC/JSON should go through this, not call MessageToDict directly."""
    return MessageToDict(message, always_print_fields_with_no_presence=True)
