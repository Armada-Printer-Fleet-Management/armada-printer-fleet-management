from collections.abc import Mapping
from functools import cached_property

from core_domain.ids import SliceProfileId
from core_domain.print_preparation import MachineSpec, SliceSettings
from proto_utils.gen.fleet.v1.printer_capabilities_pb2 import PrinterCapabilities
from proto_utils.gen.fleet.v1.printer_type_pb2 import PrinterType
from proto_utils.gen.id.v1 import slice_profile_id_pb2
from proto_utils.gen.server.v1.slicer_configuration_service_connect import (
    SlicerConfigurationServiceClientSync,
)
from proto_utils.gen.server.v1.slicer_configuration_service_pb2 import GetSliceSettingsRequest
from proto_utils.mappers import SliceSettingsMapper

from armada_domains.print_preparation.repository import SlicerConfigurationRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerSlicerConfiguration(
    ApplicationServerClient[SliceProfileId, slice_profile_id_pb2.SliceProfileId],
    SlicerConfigurationRepository,
):
    """Asks the application server, which owns the slice profiles, for slice settings."""

    _id_message_type = slice_profile_id_pb2.SliceProfileId
    _mapper = SliceSettingsMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._server = server

    @cached_property
    def _client(self) -> SlicerConfigurationServiceClientSync:
        # Built on first use, so a missing server address fails the call rather than startup.
        return SlicerConfigurationServiceClientSync(
            self._server.address(), http_client=self._server.http_client
        )

    def request_slice_settings(
        self, model: str, machine: MachineSpec, overrides: Mapping[str, str]
    ) -> SliceSettings:
        request = GetSliceSettingsRequest(
            printer_type=PrinterType(
                model=model,
                capabilities=PrinterCapabilities(
                    build_volume_x_mm=machine.width_mm,
                    build_volume_y_mm=machine.depth_mm,
                    build_volume_z_mm=machine.height_mm,
                    nozzle_diameter_mm=machine.nozzle_diameter_mm,
                    filament_diameter_mm=machine.filament_diameter_mm,
                ),
            ),
            overrides=dict(overrides),
        )
        with self._server_errors_as_domain():
            response = self._client.get_slice_settings(request)
        return self._mapper.to_entity(response.slice_settings)
