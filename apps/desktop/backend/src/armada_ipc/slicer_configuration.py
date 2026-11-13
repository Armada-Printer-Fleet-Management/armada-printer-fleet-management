"""The settings a print may be sliced with, asked of the application server through the print
preparation domain."""

from core_domain.print_preparation import MachineSpec
from proto_utils.gen.server.v1.slicer_configuration_service_pb2 import (
    GetSliceSettingsRequest,
    GetSliceSettingsResponse,
)
from proto_utils.mappers import SliceSettingsMapper

from armada_domains.print_preparation.service import SlicerConfigurationService
from armada_ipc._base import IpcModule, proto_call


class SlicerConfigurationIpc(IpcModule):
    _mapper = SliceSettingsMapper()

    def __init__(self, configuration: SlicerConfigurationService) -> None:
        self._configuration = configuration

    @proto_call(GetSliceSettingsRequest)
    def get_slice_settings(self, request: GetSliceSettingsRequest) -> GetSliceSettingsResponse:
        capabilities = request.printer_type.capabilities
        machine = MachineSpec(
            width_mm=capabilities.build_volume_x_mm,
            depth_mm=capabilities.build_volume_y_mm,
            height_mm=capabilities.build_volume_z_mm,
            nozzle_diameter_mm=capabilities.nozzle_diameter_mm,
            filament_diameter_mm=capabilities.filament_diameter_mm,
        )
        settings = self._configuration.slice_settings(
            request.printer_type.model, machine, dict(request.overrides)
        )
        return GetSliceSettingsResponse(slice_settings=self._mapper.to_proto(settings))
