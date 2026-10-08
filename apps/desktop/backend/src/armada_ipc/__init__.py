from armada_domains.print_job.service import PrintJobService
from armada_ipc.application_info import ApplicationInfo
from armada_ipc.print_job import PrintJobIpc


class Ipc:
    """The single object pywebview exposes as window.pywebview.api. Each
    attribute here becomes its own namespace in JS -- pywebview walks nested
    class instances automatically (e.g. window.pywebview.api.application_info.version()).
    Add a capability by adding an attribute here; its domain service is passed in."""

    def __init__(self, print_jobs: PrintJobService) -> None:
        self.application_info = ApplicationInfo()
        self.print_job = PrintJobIpc(print_jobs)
