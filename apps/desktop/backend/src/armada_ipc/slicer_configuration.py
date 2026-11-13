"""The settings a print may be sliced with, asked of the application server through the print
preparation domain."""

from proto_utils.gen.server.v1.slicer_configuration_service_pb2 import (
    GetSliceSettingsRequest,
    GetSliceSettingsResponse,
)
from proto_utils.mappers import MachineSpecMapper, SliceSettingsMapper

from armada_domains.print_preparation.service import SlicerConfigurationService
from armada_ipc._base import IpcModule, proto_call


class SlicerConfigurationIpc(IpcModule):
    _mapper = SliceSettingsMapper()

    def __init__(self, configuration: SlicerConfigurationService) -> None:
        self._configuration = configuration

    @proto_call(GetSliceSettingsRequest)
    def get_slice_settings(self, request: GetSliceSettingsRequest) -> GetSliceSettingsResponse:
        machine = MachineSpecMapper.from_capabilities(request.printer_type.capabilities)
        settings = self._configuration.slice_settings(
            request.printer_type.model, machine, dict(request.overrides)
        )
        return GetSliceSettingsResponse(slice_settings=self._mapper.to_proto(settings))
