from dataclasses import dataclass, field
from swe1.models import ASIL


@dataclass
class UnitOperation:
    name: str
    description: str
    parameters: list[str]           # e.g. ["sig: VehicleSignal", "timeout: uint32"]
    return_type: str                 # e.g. "void", "boolean", "Std_ReturnType"


@dataclass
class UnitInterface:
    provided: list[UnitOperation]   # operations this unit exposes
    required: list[str]             # names of operations/services this unit consumes


@dataclass
class SwUnit:
    id: str                         # UT-{project_key}-{counter:04d}
    name: str
    component_id: str
    component_name: str
    layer: str                      # application | safety | security
    asil: ASIL
    cybersecurity_relevant: bool
    responsibility: str
    interface: UnitInterface
    internal_data: list[str]        # key internal state/data elements
    allocated_swrs: list[str]       # SwRS IDs this unit contributes to
    status: str = "draft"


@dataclass
class UnitLink:
    component_id: str
    unit_id: str
    link_type: str = "decomposes"   # decomposes | depends
