from collections.abc import Iterable

from proto_utils.gen.common.v1.legal_document_pb2 import LegalDocument

from armada_domains.content_asset.service import FileService
from armada_domains.fleet.service import PrinterService
from armada_domains.legal.service import AgreementService
from armada_domains.print_job.service import PrintJobService
from armada_domains.print_preparation.service import SlicerConfigurationService
from armada_domains.queue.service import PrinterQueueService
from armada_ipc.application_info import ApplicationInfo
from armada_ipc.file import FileIpc
from armada_ipc.legal import LegalIpc
from armada_ipc.print_job import PrintJobIpc
from armada_ipc.printer import PrinterIpc
from armada_ipc.printer_queue import PrinterQueueIpc
from armada_ipc.slicer_configuration import SlicerConfigurationIpc


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
        agreements: AgreementService,
        legal_documents: Iterable[LegalDocument],
        slicer_configuration: SlicerConfigurationService,
    ) -> None:
        self.application_info = ApplicationInfo()
        self.print_job = PrintJobIpc(print_jobs)
        self.printer = PrinterIpc(printers)
        self.printer_queue = PrinterQueueIpc(printer_queues)
        self.file = FileIpc(files)
        self.legal = LegalIpc(agreements, legal_documents)
        self.slicer_configuration = SlicerConfigurationIpc(slicer_configuration)
