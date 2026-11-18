"""Builds the ASGI app from the services and infrastructure it is handed. api/main.py hands it the
production ones; tests hand it fakes, so both run the same routes, mounts and middleware."""

from collections.abc import Awaitable, Callable, Coroutine, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass

from core_domain.ids import UserId
from fastapi import FastAPI
from organization_info import read
from proto_utils.gen.organization.v1 import organization_info_pb2
from proto_utils.gen.server.v1.agreement_service_connect import AgreementServiceASGIApplication
from proto_utils.gen.server.v1.file_service_connect import FileServiceASGIApplication
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication
from proto_utils.gen.server.v1.printer_queue_service_connect import (
    PrinterQueueServiceASGIApplication,
)
from proto_utils.gen.server.v1.printer_service_connect import PrinterServiceASGIApplication
from proto_utils.gen.server.v1.slicer_configuration_service_connect import (
    SlicerConfigurationServiceASGIApplication,
)

from api.common.access_policy import ACCESS, AccessPolicy
from api.common.authentication import Caller
from api.common.consts import API_PREFIX
from api.common.dependencies import application_info
from api.common.models import DependencyCheck
from api.common.openapi import openapi_schema
from api.domains.auth.service import UserService
from api.domains.content_asset.service import FileService
from api.domains.fleet.service import PrinterService
from api.domains.legal.service import AgreementService
from api.domains.print_job.service import PrintJobService
from api.domains.print_preparation.service import SlicerConfigurationService
from api.domains.queue.service import PrinterQueueService
from api.lifespan import lifespan
from api.middleware.authentication import AuthenticationMiddleware
from api.middleware.request_context import RequestContextMiddleware
from api.routers.file import file_router
from api.routers.health import health_router
from api.services.agreement_service import AgreementServiceImplementation
from api.services.file_service import FileServiceImplementation
from api.services.health_check_service import HealthCheckServiceImplementation
from api.services.mount import mount_rpc
from api.services.print_job_service import PrintJobServiceImplementation
from api.services.printer_queue_service import PrinterQueueServiceImplementation
from api.services.printer_service import PrinterServiceImplementation
from api.services.slicer_configuration_service import SlicerConfigurationServiceImplementation


@dataclass(frozen=True)
class AppServices:
    print_jobs: PrintJobService
    files: FileService
    printers: PrinterService
    printer_queues: PrinterQueueService
    agreements: AgreementService
    slicer_configuration: SlicerConfigurationService
    users: UserService


@dataclass(frozen=True)
class AppParts:
    services: AppServices
    caller: Callable[[], UserId]
    verify: Callable[[str], Awaitable[Caller]]
    enforce: bool
    dependency_checks: Mapping[str, DependencyCheck]
    resources: Sequence[AbstractAsyncContextManager[object]]
    background: Sequence[Callable[[], Coroutine[object, object, None]]] = ()


def build_app(parts: AppParts) -> FastAPI:
    """The app over parts. The lifespan opens parts.resources and runs parts.background."""
    services = parts.services
    organization = read(organization_info_pb2.OrganizationInfo())
    app = FastAPI(
        title=organization.title,
        version=application_info().version_string(),
        lifespan=lifespan(parts.resources, background=parts.background),
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.openapi = lambda: openapi_schema(app)

    # Added first so it runs inside RequestContextMiddleware, which then logs the requests it
    # rejects.
    app.add_middleware(
        AuthenticationMiddleware,
        verify=parts.verify,
        policy=AccessPolicy(ACCESS),
        enforce=parts.enforce,
    )
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health_router(parts.dependency_checks), prefix=API_PREFIX)
    app.include_router(file_router(services.files), prefix=API_PREFIX)

    # Named handlers, so they do not clash with the domain services.
    health_check_handler = HealthCheckServiceImplementation(
        application_info(), parts.dependency_checks
    )
    print_job_handler = PrintJobServiceImplementation(
        services.print_jobs,
        services.files,
        services.printers,
        services.printer_queues,
        caller=parts.caller,
    )
    mount_rpc(app, HealthCheckServiceASGIApplication(health_check_handler))
    mount_rpc(app, PrintJobServiceASGIApplication(print_job_handler))
    mount_rpc(app, PrinterServiceASGIApplication(PrinterServiceImplementation(services.printers)))
    mount_rpc(
        app,
        PrinterQueueServiceASGIApplication(
            PrinterQueueServiceImplementation(services.printer_queues)
        ),
    )
    mount_rpc(app, FileServiceASGIApplication(FileServiceImplementation(services.files)))
    mount_rpc(
        app,
        AgreementServiceASGIApplication(
            AgreementServiceImplementation(services.agreements, organization.legal_documents)
        ),
    )
    mount_rpc(
        app,
        SlicerConfigurationServiceASGIApplication(
            SlicerConfigurationServiceImplementation(
                services.printers, services.slicer_configuration
            )
        ),
    )
    return app
