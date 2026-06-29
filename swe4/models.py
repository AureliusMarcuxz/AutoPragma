from dataclasses import dataclass, field
from swe1.models import ASIL


@dataclass
class UnitTestCase:
    id: str                         # UVTC-{project_key}-{counter:04d}
    title: str
    unit_id: str
    unit_name: str
    component_name: str
    layer: str
    test_category: str              # positive | negative | boundary | structural
    test_method: str                # dynamic_test | inspection
    environment: str                # unit_test_harness | static_tool
    asil: ASIL
    cybersecurity_relevant: bool
    priority: str                   # critical | high | medium | low
    objective: str
    preconditions: list[str]
    inputs: list[str]
    expected_outputs: list[str]
    pass_criteria: str
    fail_criteria: str
    coverage_target: str            # MC/DC | branch | statement | N/A
    stub_requirements: list[str]    # services that must be stubbed
    status: str = "draft"


@dataclass
class StaticCheckItem:
    id: str                         # SCA-{project_key}-{counter:04d}
    unit_id: str
    unit_name: str
    component_name: str
    asil: ASIL
    category: str                   # MISRA_C | complexity | documentation | naming
    description: str
    tool: str
    acceptance_criteria: str
    status: str = "pending"


@dataclass
class UnitVerificationLink:
    unit_id: str
    item_id: str                    # UVTC or SCA id
    item_type: str                  # dynamic_test | static_check
