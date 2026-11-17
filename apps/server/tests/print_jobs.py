"""Helpers for calling the print job RPCs on the app, whether it runs over fakes or the stack."""

import hashlib
from uuid import UUID

from core_domain.ids import PrintJobId
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from tests.rpc import Json, id_json, post

PRINT_JOB_RPC = f"{API_PREFIX}/server.v1.PrintJobService"
CONTENT = b"G28\nG1 X10 Y10 F3000\n"
METADATA = {
    "filename": "part.gcode",
    "sizeBytes": str(len(CONTENT)),
    "sha256": hashlib.sha256(CONTENT).hexdigest(),
    "fileType": "FILE_TYPE_GCODE",
}


def call(client: TestClient, rpc: str, body: Json, expect: int = 200) -> Json:
    """Calls one PrintJobService RPC and checks its status."""
    return post(client, f"{PRINT_JOB_RPC}/{rpc}", body, expect)


def new_draft(client: TestClient) -> PrintJobId:
    """Creates a DRAFT job with no file and returns its ID."""
    created = call(client, "CreatePrintJob", {"userNotes": ""})["printJob"]
    return PrintJobId(UUID(created["id"]["value"]))


def upload_slot(client: TestClient, print_job_id: object, filename: str = "part.gcode") -> Json:
    """Creates the file record for a job's upload of CONTENT. The slot holds its fileId and the
    uploadUrl to PUT the bytes to."""
    body = {"printJobId": id_json(print_job_id), "metadata": {**METADATA, "filename": filename}}
    slot: Json = call(client, "CreatePrintJobUpload", body)["slot"]
    return slot


def file_url(slot: Json) -> str:
    """Where the slot's file downloads from, once its bytes are uploaded."""
    return f"{API_PREFIX}/files/{slot['fileId']['value']}"
