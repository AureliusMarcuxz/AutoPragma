from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ASIL(str, Enum):
    QM = "QM"
    A = "ASIL-A"
    B = "ASIL-B"
    C = "ASIL-C"
    D = "ASIL-D"


class VerificationMethod(str, Enum):
    TEST = "test"
    ANALYSIS = "analysis"
    INSPECTION = "inspection"
    DEMONSTRATION = "demonstration"


class RequirementStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    OBSOLETE = "obsolete"


@dataclass
class SyRSItem:
    id: str
    title: str
    text: str
    type: str                          # functional | interface | performance | constraint
    status: RequirementStatus
    asil: ASIL
    cybersecurity_relevant: bool
    rationale: str
    verification_method: VerificationMethod
    parent_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SwRSItem:
    id: str
    title: str
    text: str
    type: str
    asil: ASIL
    cybersecurity_relevant: bool
    verification_method: VerificationMethod
    derived_from: str                  # SyRS item ID
    rationale: str = ""
    status: str = "draft"
    tags: list[str] = field(default_factory=list)
    derivation_type: str = "derives_functional"  # derives_functional | derives_safety_mechanism | derives_cybersec_impl


@dataclass
class TraceabilityLink:
    source_id: str                     # SyRS ID
    target_id: str                     # SwRS ID
    link_type: str = "derives"


@dataclass
class ValidationFinding:
    item_id: str
    severity: str                      # ERROR | WARNING | INFO
    rule_id: str
    message: str
