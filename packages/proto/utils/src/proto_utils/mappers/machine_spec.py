from core_domain.print_preparation import MachineSpec

from proto_utils.gen.fleet.v1 import printer_capabilities_pb2


class MachineSpecMapper:
    """A printer type's capabilities, as the fleet sends them, as print preparation's MachineSpec,
    and back. The only place the two domains' values meet, so neither imports the other."""

    @staticmethod
    def from_capabilities(
        message: printer_capabilities_pb2.PrinterCapabilities,
    ) -> MachineSpec:
        return MachineSpec(
            width_mm=message.build_volume_x_mm,
            depth_mm=message.build_volume_y_mm,
            height_mm=message.build_volume_z_mm,
            nozzle_diameter_mm=message.nozzle_diameter_mm,
            filament_diameter_mm=message.filament_diameter_mm,
        )

    @staticmethod
    def to_capabilities(machine: MachineSpec) -> printer_capabilities_pb2.PrinterCapabilities:
        return printer_capabilities_pb2.PrinterCapabilities(
            build_volume_x_mm=machine.width_mm,
            build_volume_y_mm=machine.depth_mm,
            build_volume_z_mm=machine.height_mm,
            nozzle_diameter_mm=machine.nozzle_diameter_mm,
            filament_diameter_mm=machine.filament_diameter_mm,
        )
