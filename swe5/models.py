from dataclasses import dataclass, field
from swe1.models import ASIL


@dataclass
class IntegrationStep:
    step_number: int
    title: str
    units: list[str]           # unit names integrated in this step
    components: list[str]      # component names involved
    stubs_needed: list[str]    # services still stubbed at this step
    exit_criteria: str


@dataclass
class IntegrationStage:
    stage_number: int
    title: str
    description: str
    integration_level: str     # intra_component | cross_component | full
    steps: list[IntegrationStep]
    components_covered: list[str]


@dataclass
class IntegrationTestCase:
    id: str                           # ITC-{project_key}-{counter:04d}
    title: str
    objective: str
    test_type: str                    # interface_contract | data_flow | timing_interaction
                                      # error_propagation | safety_chain | security_chain
    environment: str
    asil: ASIL
    cybersecurity_relevant: bool
    priority: str                     # critical | high | medium
    integration_level: str            # intra_component | cross_component
    units_under_test: list[str]
    components_covered: list[str]
    preconditions: list[str]
    stimuli: list[str]
    expected_behavior: list[str]
    pass_criteria: str
    fail_criteria: str
    coverage_tags: list[str]
    status: str = "draft"


@dataclass
class IntegrationLink:
    itc_id: str
    source_id: str    # unit_id or component_id (caller / supervisor side)
    target_id: str    # unit_id or component_id (callee / monitored side)
    link_type: str    # unit_pair | component_pair
