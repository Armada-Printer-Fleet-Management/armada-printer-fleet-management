from fastapi import FastAPI
from organization_info import read
from proto_utils.gen.common.v1 import organization_info_pb2
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication

from api.common.clock import clock
from api.common.consts import API_PREFIX
from api.common.dependencies import application_info
from api.common.health import raising_probe
from api.common.models import DependencyCheck
from api.common.openapi import openapi_schema
from api.common.settings import FileStoreSettings
from api.domains.file.service import FileService
from api.domains.print_job.service import PrintJobService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.stub_data import STUB_STUDENT_ID, stub_files, stub_print_jobs
from api.lifespan import lifespan
from api.middleware.request_context import RequestContextMiddleware
from api.plugins import build_file_store
from api.routers.file import file_router
from api.routers.health import health_router
from api.services.health_check_service import HealthCheckServiceImplementation
from api.services.mount import mount_rpc
from api.services.print_job_service import PrintJobServiceImplementation

# Infrastructure
files = FileStoreFiles(lambda: build_file_store(FileStoreSettings()))  # Built at lifespan

# Services (note difference from an RPC service, this is the domain service)

# The in-memory repositories stand in until the server has a database. Switching means
# constructing the real adapters here; nothing else changes.
print_job_service = PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock)
file_service = FileService(InMemoryFileRepository(stub_files()), files, clock)

# App

app = FastAPI(
    title=read(organization_info_pb2.OrganizationInfo()).title,
    version=application_info().version_string(),
    lifespan=lifespan(files),
)
app.openapi = lambda: openapi_schema(app)
dependency_checks = {"file_storage": DependencyCheck(raising_probe(files.health_check))}

# Middlewares

app.add_middleware(RequestContextMiddleware)

# Routers

app.include_router(health_router(dependency_checks), prefix=API_PREFIX)
app.include_router(file_router(file_service), prefix=API_PREFIX)

# RPC services (named handlers to fit DDD and not clash with the domain services)
health_check_handler = HealthCheckServiceImplementation(application_info(), dependency_checks)

# Stub: every caller is the seeded student until the server authenticates requests.
print_job_handler = PrintJobServiceImplementation(
    print_job_service, file_service, caller=lambda: STUB_STUDENT_ID
)

mount_rpc(app, HealthCheckServiceASGIApplication(health_check_handler))
mount_rpc(app, PrintJobServiceASGIApplication(print_job_handler))
