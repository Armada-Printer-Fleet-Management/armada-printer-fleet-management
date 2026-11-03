"""As a student, I create a print job, upload its G-code and submit it. Then, as staff, I find
it among the jobs, start its review and approve it."""

import hashlib

import httpx2
import pytest
from proto_utils.gen.common.v1.page_pb2 import PageRequest
from proto_utils.gen.content_asset.v1.file_pb2 import FILE_TYPE_GCODE
from proto_utils.gen.content_asset.v1.file_upload_pb2 import FileUploadMetadata
from proto_utils.gen.id.v1.print_job_id_pb2 import PrintJobId
from proto_utils.gen.print_job.v1.print_job_pb2 import (
    PRINT_JOB_STATUS_APPROVED,
    PRINT_JOB_STATUS_DRAFT,
    PRINT_JOB_STATUS_SUBMITTED,
    PRINT_JOB_STATUS_UNDER_REVIEW,
)
from proto_utils.gen.server.v1.print_job_service_pb2 import (
    CreatePrintJobRequest,
    CreatePrintJobUploadRequest,
    ListPrintJobsRequest,
    SubmitPrintJobRequest,
    TransitionPrintJobRequest,
)

from e2e.auth import KeycloakTokens
from e2e.conftest import SignedIn
from e2e.settings import E2eRole

_GCODE = b"G28\nG1 X10 Y10 F3000\n"
_MAX_PAGES = 50


def _listed(staff: SignedIn, print_job_id: PrintJobId) -> bool:
    token = ""
    for _ in range(_MAX_PAGES):
        page = staff.print_jobs.list_print_jobs(
            ListPrintJobsRequest(page=PageRequest(page_size=100, page_token=token))
        )
        if any(job.id == print_job_id for job in page.print_jobs):
            return True
        token = page.page.next_page_token
        if not token:
            return False
    return False


@pytest.mark.xfail(
    strict=True,
    reason="needs the deploy stack to run the database migrations; its database is empty",
)
def test_a_student_submits_a_job_and_staff_approve_it(
    as_student: SignedIn, as_staff: SignedIn, rest: httpx2.Client, tokens: KeycloakTokens
) -> None:
    created = as_student.print_jobs.create_print_job(
        CreatePrintJobRequest(user_notes="e2e smoke test")
    ).print_job
    assert created.status == PRINT_JOB_STATUS_DRAFT
    job = created.id

    slot = as_student.print_jobs.create_print_job_upload(
        CreatePrintJobUploadRequest(
            print_job_id=job,
            metadata=FileUploadMetadata(
                filename="smoke-test.gcode",
                size_bytes=len(_GCODE),
                sha256=hashlib.sha256(_GCODE).hexdigest(),
                file_type=FILE_TYPE_GCODE,
            ),
        )
    ).slot
    uploaded = rest.put(
        slot.upload_url,
        content=_GCODE,
        headers={"authorization": f"Bearer {tokens.token(E2eRole.STUDENT)}"},
    )
    assert uploaded.status_code == 204, uploaded.text

    submitted = as_student.print_jobs.submit_print_job(SubmitPrintJobRequest(print_job_id=job))
    assert submitted.print_job.status == PRINT_JOB_STATUS_SUBMITTED
    assert submitted.file.id == slot.file_id

    assert _listed(as_staff, job), "staff cannot find the submitted job"

    reviewing = as_staff.print_jobs.transition_print_job(
        TransitionPrintJobRequest(
            print_job_id=job, start_review=TransitionPrintJobRequest.StartReview()
        )
    )
    assert reviewing.print_job.status == PRINT_JOB_STATUS_UNDER_REVIEW
    approved = as_staff.print_jobs.transition_print_job(
        TransitionPrintJobRequest(print_job_id=job, approve=TransitionPrintJobRequest.Approve())
    )
    assert approved.print_job.status == PRINT_JOB_STATUS_APPROVED
