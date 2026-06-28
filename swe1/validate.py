from .models import ASIL, SyRSItem, ValidationFinding

# (rule_id, attribute_name, severity, message)
_COMPLETENESS_RULES: list[tuple[str, str, str, str]] = [
    ("VAL-001", "text",                "ERROR",   "Requirement text is missing or empty"),
    ("VAL-002", "title",               "ERROR",   "Requirement title is missing or empty"),
    ("VAL-003", "rationale",           "WARNING", "Rationale is missing — required for CL3 process record"),
    ("VAL-004", "verification_method", "WARNING", "Verification method not specified"),
]

# ASIL levels that require more than inspection as verification evidence
_SAFETY_ASILS = {ASIL.A, ASIL.B, ASIL.C, ASIL.D}


def validate(items: list[SyRSItem]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    seen_ids: set[str] = set()

    for item in items:
        # Duplicate ID
        if item.id in seen_ids:
            findings.append(ValidationFinding(
                item_id=item.id,
                severity="ERROR",
                rule_id="VAL-000",
                message=f"Duplicate requirement ID '{item.id}'",
            ))
        seen_ids.add(item.id)

        # Completeness
        for rule_id, attr, severity, message in _COMPLETENESS_RULES:
            value = getattr(item, attr, None)
            if not value or (isinstance(value, str) and not value.strip()):
                findings.append(ValidationFinding(
                    item_id=item.id,
                    severity=severity,
                    rule_id=rule_id,
                    message=message,
                ))

        # Safety-rated items should not rely solely on inspection
        if item.asil in _SAFETY_ASILS and item.verification_method.value == "inspection":
            findings.append(ValidationFinding(
                item_id=item.id,
                severity="WARNING",
                rule_id="VAL-005",
                message=(
                    f"{item.asil.value}-rated requirement uses 'inspection' as sole "
                    "verification method — test or analysis provides stronger evidence "
                    "for safety assessment"
                ),
            ))

        # Cybersecurity-relevant items must have rationale referencing TARA
        if item.cybersecurity_relevant and not item.rationale.strip():
            findings.append(ValidationFinding(
                item_id=item.id,
                severity="WARNING",
                rule_id="VAL-006",
                message=(
                    "Cybersecurity-relevant requirement has no rationale — "
                    "ISO/SAE 21434 traceability requires a TARA reference"
                ),
            ))

        # Parent reference consistency: parent_id must appear in the item set
        # (checked after full set is known — see validate_cross_references)

    findings.extend(_validate_cross_references(items, seen_ids))
    return findings


def _validate_cross_references(
    items: list[SyRSItem], all_ids: set[str]
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for item in items:
        if item.parent_id and item.parent_id not in all_ids:
            findings.append(ValidationFinding(
                item_id=item.id,
                severity="ERROR",
                rule_id="VAL-007",
                message=(
                    f"parent_id '{item.parent_id}' not found in this SyRS — "
                    "broken traceability link"
                ),
            ))
    return findings


def finding_counts(findings: list[ValidationFinding]) -> dict[str, int]:
    counts: dict[str, int] = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts
