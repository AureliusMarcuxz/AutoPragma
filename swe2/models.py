from dataclasses import dataclass, field
from swe1.models import ASIL


@dataclass
class SwComponent:
    id: str                                # COMP-{project_key}-{counter:04d}
    name: str                              # e.g., "ComStack"
    layer: str                             # application | safety | security
    description: str
    asil: ASIL
    cybersecurity_relevant: bool
    allocated_swrs: list[str] = field(default_factory=list)
    monitors: list[str] = field(default_factory=list)  # component names this comp monitors
    secures: list[str] = field(default_factory=list)   # component names this comp secures


@dataclass
class AllocationLink:
    swrs_id: str
    component_id: str
    component_name: str
    rationale: str
