from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.print_preparation import MachineSpec
from proto_utils.gen.server.v1.slicer_configuration_service_pb2 import (
    GetSliceSettingsRequest,
    GetSliceSettingsResponse,
)
from proto_utils.mappers import PrinterTypeMapper, SliceSettingsMapper

from api.domains.fleet.service import PrinterService
from api.domains.print_preparation.service import SlicerConfigurationService
from api.services.domain_errors import domain_errors_as_connect


class SlicerConfigurationServiceImplementation:
    """The Connect handler for server.v1.SlicerConfigurationService. Joins the fleet, which says
    which printer types exist, to print preparation, which builds the settings."""

    _type_mapper = PrinterTypeMapper()
    _settings_mapper = SliceSettingsMapper()

    def __init__(self, printers: PrinterService, configuration: SlicerConfigurationService) -> None:
        self._printers = printers
        self._configuration = configuration

    async def get_slice_settings(
        self,
        request: GetSliceSettingsRequest,
        ctx: RequestContext[GetSliceSettingsRequest, GetSliceSettingsResponse],
        /,
    ) -> GetSliceSettingsResponse:
        with domain_errors_as_connect():
            try:
                printer_type = self._type_mapper.to_entity(request.printer_type)
            except ValueError as error:
                raise ConnectError(Code.INVALID_ARGUMENT, str(error)) from error
            # The settings come from the fleet's own capabilities, never from the client's copy.
            if printer_type not in await self._printers.types():
                raise ConnectError(
                    Code.NOT_FOUND,
                    f"No {printer_type.model} with these capabilities is in the fleet",
                )
            capabilities = printer_type.capabilities
            machine = MachineSpec(
                width_mm=capabilities.build_volume_x_mm,
                depth_mm=capabilities.build_volume_y_mm,
                height_mm=capabilities.build_volume_z_mm,
                nozzle_diameter_mm=capabilities.nozzle_diameter_mm,
                filament_diameter_mm=capabilities.filament_diameter_mm,
            )
            settings = await self._configuration.slice_settings(machine, dict(request.overrides))
        return GetSliceSettingsResponse(slice_settings=self._settings_mapper.to_proto(settings))
