"""The desktop's composition root: the only place infrastructure is constructed and handed to the
domain services that IPC exposes."""

from armada_domains.file.service import FileService
from armada_domains.print_job.service import PrintJobService
from armada_domains.printer.service import PrinterService
from armada_domains.printer_queue.service import PrinterQueueService
from armada_infrastructure.application_server.connection import ApplicationServerConnection
from armada_infrastructure.application_server.file import ApplicationServerFiles
from armada_infrastructure.application_server.print_job import ApplicationServerPrintJobs
from armada_infrastructure.application_server.printer import ApplicationServerPrinters
from armada_infrastructure.application_server.printer_queue import ApplicationServerPrinterQueues
from armada_ipc import Ipc


def build_ipc() -> Ipc:
    server = ApplicationServerConnection()
    return Ipc(
        print_jobs=PrintJobService(ApplicationServerPrintJobs(server)),
        printers=PrinterService(ApplicationServerPrinters(server)),
        printer_queues=PrinterQueueService(ApplicationServerPrinterQueues(server)),
        files=FileService(ApplicationServerFiles(server)),
    )
