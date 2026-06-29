from dataclasses import dataclass, field
from swe1.models import ASIL


@dataclass
class TestStep:
    step_number: int
    action: str
    expected_result: str


@dataclass
class TestCase:
    id: str                         # TC-{project_key}-{counter:04d}
    title: str
    objective: str
    test_type: str                  # behavioral | fault_injection | security | performance | inspection | demonstration
    test_method: str                # dynamic_test | static_analysis | inspection | demonstration
    environment: str                # HIL | SIL | MIL
    asil: ASIL
    cybersecurity_relevant: bool
    priority: str                   # critical | high | medium | low
    derived_from: str               # SwRS ID
    preconditions: list[str]
    steps: list[TestStep]
    pass_criteria: str
    fail_criteria: str
    coverage_requirement: str       # MC/DC | branch | statement
    coverage_tags: list[str]
    status: str = "draft"


@dataclass
class TestCoverageLink:
    swrs_id: str
    test_case_id: str
    coverage_type: str              # full | partial
