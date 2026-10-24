from armada_domains.file.service import FileService
from armada_domains.print_job.service import PrintJobService
from armada_domains.printer.service import PrinterService
from armada_domains.printer_queue.service import PrinterQueueService
from armada_ipc.application_info import ApplicationInfo
from armada_ipc.file import FileIpc
from armada_ipc.print_job import PrintJobIpc
from armada_ipc.printer import PrinterIpc
from armada_ipc.printer_queue import PrinterQueueIpc


class Ipc:
    """The single object pywebview exposes as window.pywebview.api. Each
    attribute here becomes its own namespace in JS -- pywebview walks nested
    class instances automatically (e.g. window.pywebview.api.application_info.version()).
    Add a capability by adding an attribute here; its domain service is passed in."""

    def __init__(
        self,
        print_jobs: PrintJobService,
        printers: PrinterService,
        printer_queues: PrinterQueueService,
        files: FileService,
    ) -> None:
        self.application_info = ApplicationInfo()
        self.print_job = PrintJobIpc(print_jobs)
        self.printer = PrinterIpc(printers)
        self.printer_queue = PrinterQueueIpc(printer_queues)
        self.file = FileIpc(files)
