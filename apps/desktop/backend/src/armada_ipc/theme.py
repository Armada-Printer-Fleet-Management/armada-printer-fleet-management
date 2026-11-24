"""The user's light or dark theme choice, kept in the per-user theme file."""

from proto_utils.gen.desktop.v1.theme_settings_pb2 import (
    ThemePreference as ThemePreferenceMessage,
)
from proto_utils.gen.desktop.v1.theme_settings_pb2 import ThemeSettings

from armada_ipc._base import IpcModule, proto_call, proto_response
from armada_runtime.theme import ThemeFile, ThemePreference

_TO_PROTO = {
    ThemePreference.SYSTEM: ThemePreferenceMessage.THEME_PREFERENCE_SYSTEM,
    ThemePreference.LIGHT: ThemePreferenceMessage.THEME_PREFERENCE_LIGHT,
    ThemePreference.DARK: ThemePreferenceMessage.THEME_PREFERENCE_DARK,
}
_FROM_PROTO = {message: preference for preference, message in _TO_PROTO.items()}


class ThemeIpc(IpcModule):
    def __init__(self, theme_file: ThemeFile) -> None:
        self._theme_file = theme_file

    @proto_response
    def theme_preference(self) -> ThemeSettings:
        return ThemeSettings(preference=_TO_PROTO[self._theme_file.theme_preference()])

    @proto_call(ThemeSettings)
    def set_theme_preference(self, request: ThemeSettings) -> ThemeSettings:
        """UNSPECIFIED is stored as SYSTEM, its meaning on every client."""
        preference = _FROM_PROTO.get(request.preference, ThemePreference.SYSTEM)
        self._theme_file.set_theme_preference(preference)
        return ThemeSettings(preference=_TO_PROTO[preference])
