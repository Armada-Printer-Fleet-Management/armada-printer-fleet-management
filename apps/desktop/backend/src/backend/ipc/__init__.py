from backend.ipc.application_information import ApplicationInformation


class Ipc:
    """The single object pywebview exposes as window.pywebview.api. Each
    attribute here becomes its own namespace in JS -- pywebview walks nested
    class instances automatically (e.g. window.pywebview.api.application_information.version()).
    Add a capability by adding an attribute here."""

    def __init__(self) -> None:
        self.application_information = ApplicationInformation()
