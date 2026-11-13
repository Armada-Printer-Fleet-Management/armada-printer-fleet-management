from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.ids import SliceProfileId
from proto_utils.gen.server.v1.slicer_configuration_service_pb2 import (
    GetSliceProfileRequest,
    GetSliceProfileResponse,
    GetSliceSettingsRequest,
    GetSliceSettingsResponse,
)
from proto_utils.mappers import (
    MachineSpecMapper,
    PrinterTypeMapper,
    SliceProfileMapper,
    SliceSettingsMapper,
)

from api.domains.fleet.service import PrinterService
from api.domains.print_preparation.service import SlicerConfigurationService
from api.services.domain_errors import domain_errors_as_connect, request_id


class SlicerConfigurationServiceImplementation:
    """The Connect handler for server.v1.SlicerConfigurationService. Joins the fleet, which says
    which printer types exist, to print preparation, which builds the settings."""

    _type_mapper = PrinterTypeMapper()
    _profile_mapper = SliceProfileMapper()
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
            machine = MachineSpecMapper.from_capabilities(request.printer_type.capabilities)
            settings = await self._configuration.slice_settings(machine, dict(request.overrides))
        return GetSliceSettingsResponse(slice_settings=self._settings_mapper.to_proto(settings))

    async def get_slice_profile(
        self,
        request: GetSliceProfileRequest,
        ctx: RequestContext[GetSliceProfileRequest, GetSliceProfileResponse],
        /,
    ) -> GetSliceProfileResponse:
        profile_id = request_id(SliceProfileId, request.slice_profile_id)
        with domain_errors_as_connect():
            profile = await self._configuration.profile(profile_id)
        return GetSliceProfileResponse(slice_profile=self._profile_mapper.to_proto(profile))
