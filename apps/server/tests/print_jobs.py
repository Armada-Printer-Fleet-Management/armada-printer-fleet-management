"""The print job RPCs served over fakes, and helpers for calling them."""

import asyncio
import hashlib
from collections.abc import Callable
from datetime import datetime, timedelta

from core_domain.content_asset import File
from fastapi import FastAPI
from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication

from api.common.consts import API_PREFIX
from api.domains.content_asset.service import FileService
from api.domains.fleet.service import PrinterService
from api.domains.print_job.service import PrintJobService
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.dev_data import (
    STUB_STUDENT_ID,
    stub_print_jobs,
    stub_printer_queues,
    stub_printers,
)
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.routers.file import file_router
from api.services.print_job_service import PrintJobServiceImplementation
from api.services.printer_poller import PrinterPoller
from tests.fakes import MemoryFileStore
from tests.rpc import Json, id_json

PRINT_JOB_RPC = "/server.v1.PrintJobService"
CONTENT = b"G28\nG1 X10 Y10 F3000\n"
METADATA = {
    "filename": "part.gcode",
    "sizeBytes": str(len(CONTENT)),
    "sha256": hashlib.sha256(CONTENT).hexdigest(),
    "fileType": "FILE_TYPE_GCODE",
}


def fake_client_and_poller(
    files: list[File], clock: Callable[[], datetime]
) -> tuple[TestClient, PrinterPoller]:
    """The RPCs over in-memory adapters and a fake file store. The file routes are served beside
    them, so an upload_url can be PUT to."""
    storage = FileStoreFiles(MemoryFileStore)
    asyncio.run(storage.__aenter__())
    print_jobs = PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock)
    file_service = FileService(InMemoryFileRepository(files), storage, clock)
    printers = PrinterService(MockPrinterServer(stub_printers(), clock))
    printer_queues = PrinterQueueService(InMemoryPrinterQueueRepository(stub_printer_queues()))
    handler = PrintJobServiceImplementation(
        print_jobs, file_service, printers, printer_queues, caller=lambda: STUB_STUDENT_ID
    )
    rest = FastAPI()
    rest.include_router(file_router(file_service), prefix=API_PREFIX)
    rest.mount("/", PrintJobServiceASGIApplication(handler))
    poller = PrinterPoller(printers, print_jobs, timedelta(seconds=1))
    return TestClient(rest), poller


def call(client: TestClient, rpc: str, body: Json, expect: int = 200, prefix: str = "") -> Json:
    """Calls one PrintJobService RPC and checks its status. The real app serves it under prefix."""
    response = client.post(f"{prefix}{PRINT_JOB_RPC}/{rpc}", json=body)
    assert response.status_code == expect, response.text
    result: Json = response.json()
    return result


def upload_slot(client: TestClient, print_job_id: object, prefix: str = "") -> Json:
    """Creates the file record for a job's upload of CONTENT. The slot holds its fileId and the
    uploadUrl to PUT the bytes to."""
    body = {"printJobId": id_json(print_job_id), "metadata": METADATA}
    slot: Json = call(client, "CreatePrintJobUpload", body, prefix=prefix)["slot"]
    return slot
