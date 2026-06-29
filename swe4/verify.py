"""
SWE.4 Software Unit Verification engine.

Generates a unit verification specification from SW units (SWE.3):

  Dynamic test cases (UVTC-…):
    - positive     — nominal inputs, verify correct return values / state
    - negative     — invalid/null/out-of-range inputs, verify error handling
    - structural   — MC/DC or branch coverage (ASIL-B and above only)

  Static analysis items (SCA-…):
    - MISRA_C      — MISRA C:2012 rule compliance
    - complexity   — McCabe cyclomatic complexity limit
    - documentation— function-header completeness (pre/post-conditions)

ASIL mapping:
  ASIL-D/C → MC/DC coverage, critical priority, HIL harness
  ASIL-B   → branch coverage, high priority, HIL or SIL harness
  ASIL-A   → statement coverage, high priority, SIL harness
  QM       → statement coverage, medium priority, SIL harness
"""

from swe1.models import ASIL
from swe3.models import SwUnit

from .models import StaticCheckItem, UnitTestCase, UnitVerificationLink

_ASIL_PRIORITY = {ASIL.D: "critical", ASIL.C: "critical",
                  ASIL.B: "high",     ASIL.A: "high", ASIL.QM: "medium"}
_ASIL_COVERAGE = {ASIL.D: "MC/DC",   ASIL.C: "MC/DC",
                  ASIL.B: "branch",   ASIL.A: "statement", ASIL.QM: "statement"}
_ASIL_HARNESS  = {ASIL.D: "HIL unit-test harness",
                  ASIL.C: "HIL unit-test harness",
                  ASIL.B: "HIL or SIL unit-test harness",
                  ASIL.A: "SIL unit-test harness",
                  ASIL.QM: "SIL unit-test harness"}
_COMPLEXITY_LIMIT = {ASIL.D: 5, ASIL.C: 5, ASIL.B: 10, ASIL.A: 15, ASIL.QM: 20}

_NEEDS_STRUCTURAL = {ASIL.D, ASIL.C, ASIL.B, ASIL.A}

# ── Preconditions (shared base) ───────────────────────────────────────────────

def _base_preconditions(unit: SwUnit) -> list[str]:
    preconds = [
        f"Unit under test ({unit.name}) is compiled at the target baseline "
        "commit with all CI pre-checks passing.",
        f"Unit-test harness ({_ASIL_HARNESS[unit.asil]}) is initialised "
        "and all required stubs/drivers are configured.",
    ]
    if unit.stub_requirements if hasattr(unit, "stub_requirements") else unit.interface.required:
        stubs = unit.interface.required
        preconds.append(
            "Stubs configured for: " + "; ".join(stubs[:3])
            + ("…" if len(stubs) > 3 else ".")
        )
    if unit.asil in {ASIL.C, ASIL.D}:
        preconds.append(
            f"Independent safety checker is active and observing the "
            f"{unit.asil.value}-rated outputs under test."
        )
    return preconds


# ── Positive test ─────────────────────────────────────────────────────────────

def _positive_test(unit: SwUnit, tc_id: str) -> UnitTestCase:
    primary_op = unit.interface.provided[0]
    return UnitTestCase(
        id=tc_id,
        title=f"[UVTC-POS] {unit.name} — nominal operation ({primary_op.name})",
        unit_id=unit.id,
        unit_name=unit.name,
        component_name=unit.component_name,
        layer=unit.layer,
        test_category="positive",
        test_method="dynamic_test",
        environment=_ASIL_HARNESS[unit.asil],
        asil=unit.asil,
        cybersecurity_relevant=unit.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[unit.asil],
        objective=(
            f"Verify that {unit.name}.{primary_op.name}() returns the correct "
            f"result ({primary_op.return_type}) and does not corrupt internal "
            f"state when called with nominal, valid inputs."
        ),
        preconditions=_base_preconditions(unit),
        inputs=[
            f"All parameters of {primary_op.name}() set to nominal mid-range values "
            "within the specified operating domain.",
            "All stubs configured to return success / nominal data.",
            "Internal state variables initialised to their default reset values.",
        ],
        expected_outputs=[
            f"{primary_op.name}() returns the expected nominal value / E_OK.",
            "No error flags or fault codes are set after the call.",
            "Internal data elements reflect the expected post-condition state.",
            f"No call to any error-handling stub (Dem_SetEventStatus, FIM, etc.).",
        ],
        pass_criteria=(
            f"Return value matches specification; all post-condition state checks "
            f"pass; {_ASIL_COVERAGE[unit.asil]} coverage ≥ 100 % on "
            f"{unit.name}.{primary_op.name}(). No stubs report unexpected calls."
        ),
        fail_criteria=(
            "Return value outside specification; any post-condition check fails; "
            "coverage below target; or unexpected stub call recorded."
        ),
        coverage_target=_ASIL_COVERAGE[unit.asil],
        stub_requirements=list(unit.interface.required),
    )


# ── Negative / error-handling test ────────────────────────────────────────────

def _negative_test(unit: SwUnit, tc_id: str) -> UnitTestCase:
    primary_op = unit.interface.provided[0]
    has_params  = bool(primary_op.parameters)

    if unit.layer == "safety":
        input_desc = [
            "Inject a fault stimulus: set monitored signal to a value that "
            "violates the defined safety boundary (out-of-range or stuck-at).",
            "Configure the DEM stub to confirm the expected DTC is stored.",
        ]
        expected = [
            "FaultDetector detects the violation within the FDTI.",
            "SafeReactionExecutor is called; DEM stub records the expected DTC.",
            "Safe-state output is set within the FTTI deadline.",
        ]
    elif unit.layer == "security":
        input_desc = [
            "Supply an invalid / tampered authentication token or an expired key ID.",
            "Configure Csm stub to return E_NOT_OK for the operation.",
        ]
        expected = [
            "Operation is rejected; return value indicates E_NOT_OK or AUTH_FAILED.",
            "No sensitive data is written to output buffers.",
            "AuditLogger stub records a DENY or POLICY_VIOLATION event.",
        ]
    else:
        input_desc = [
            "Pass NULL pointer or out-of-range parameter to "
            f"{primary_op.name}()." if has_params else
            f"Configure dependent stubs to return failure codes before calling "
            f"{primary_op.name}().",
            "Ensure internal state is in a valid pre-condition (not already faulted).",
        ]
        expected = [
            f"{primary_op.name}() returns an error code (E_NOT_OK / FALSE) rather "
            "than crashing or causing undefined behaviour.",
            "No internal data corruption occurs (internal state remains consistent).",
            "Error is propagated to the caller without silent failure.",
        ]

    return UnitTestCase(
        id=tc_id,
        title=f"[UVTC-NEG] {unit.name} — error / fault input handling",
        unit_id=unit.id,
        unit_name=unit.name,
        component_name=unit.component_name,
        layer=unit.layer,
        test_category="negative",
        test_method="dynamic_test",
        environment=_ASIL_HARNESS[unit.asil],
        asil=unit.asil,
        cybersecurity_relevant=unit.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[unit.asil],
        objective=(
            f"Verify that {unit.name} handles invalid inputs, stub failures, "
            f"and fault stimuli robustly — returning a defined error value and "
            f"leaving internal state consistent without silent failure or "
            f"undefined behaviour."
        ),
        preconditions=_base_preconditions(unit),
        inputs=input_desc,
        expected_outputs=expected,
        pass_criteria=(
            "Error code returned as specified; internal state consistent; "
            "no crash, hang, or memory corruption; error propagated to caller. "
            "All sub-checks PASS."
        ),
        fail_criteria=(
            "Silent failure observed; internal state corrupted; crash or "
            "undefined behaviour detected; or error not propagated."
        ),
        coverage_target=_ASIL_COVERAGE[unit.asil],
        stub_requirements=list(unit.interface.required),
    )


# ── Structural / MC/DC test ───────────────────────────────────────────────────

def _structural_test(unit: SwUnit, tc_id: str) -> UnitTestCase:
    cov = _ASIL_COVERAGE[unit.asil]
    return UnitTestCase(
        id=tc_id,
        title=f"[UVTC-STRUCT] {unit.name} — {cov} structural coverage",
        unit_id=unit.id,
        unit_name=unit.name,
        component_name=unit.component_name,
        layer=unit.layer,
        test_category="structural",
        test_method="dynamic_test",
        environment=_ASIL_HARNESS[unit.asil],
        asil=unit.asil,
        cybersecurity_relevant=unit.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[unit.asil],
        objective=(
            f"Achieve {cov} structural code coverage on all provided operations "
            f"of {unit.name} by exercising every decision/condition independently. "
            f"Required by ISO 26262-6 Table 12 for {unit.asil.value}."
        ),
        preconditions=_base_preconditions(unit) + [
            f"Coverage instrumentation is active in the build configuration "
            f"(gcov / LDRA / Polyspace coverage mode).",
        ],
        inputs=[
            "Execute the full positive and negative test suites for this unit "
            "while coverage instrumentation is active.",
            "Add supplementary test vectors specifically targeting uncovered "
            "branches or condition combinations identified in the coverage report.",
        ],
        expected_outputs=[
            f"{cov} coverage ≥ 100 % across all provided operations of {unit.name}.",
            "Coverage report artefact generated and stored as gate evidence.",
            "No untested dead code or unreachable branches identified.",
        ],
        pass_criteria=(
            f"{cov} coverage ≥ 100 %; coverage report linked to this test case "
            f"in the ALM. Required per ISO 26262-6 Table 12 for {unit.asil.value}."
        ),
        fail_criteria=(
            f"{cov} coverage < 100 %; untested branches or conditions remain; "
            "coverage report missing or incomplete."
        ),
        coverage_target=cov,
        stub_requirements=list(unit.interface.required),
    )


# ── Static analysis items ─────────────────────────────────────────────────────

_STATIC_CHECKS = [
    ("MISRA_C",
     "Verify MISRA C:2012 compliance using an approved static analysis tool. "
     "All rule violations must be resolved or formally deviated with rationale.",
     "PC-lint Plus / LDRA / Polyspace Bug Finder",
     "Zero unapproved MISRA violations; all deviations documented and reviewed."),
    ("complexity",
     "Measure McCabe cyclomatic complexity for every function in the unit. "
     "Complexity must not exceed the limit defined for the ASIL classification.",
     "Polyspace Code Prover / LDRA / Understand",
     "All functions within the complexity limit; no function exceeds the threshold."),
    ("documentation",
     "Verify that every provided operation has a complete Doxygen/AUTOSAR-style "
     "header comment stating: description, parameters, return value, pre-conditions, "
     "post-conditions, and ASIL classification.",
     "Doxygen / peer review checklist",
     "All function headers complete; peer review sign-off recorded in the ALM."),
]


def _static_checks(unit: SwUnit, start_id: int, project_key: str) -> list[StaticCheckItem]:
    items = []
    for i, (cat, desc, tool, accept) in enumerate(_STATIC_CHECKS):
        full_desc = desc
        if cat == "complexity":
            limit = _COMPLEXITY_LIMIT[unit.asil]
            full_desc = (
                f"McCabe cyclomatic complexity ≤ {limit} per function "
                f"(ISO 26262-6 Table 12 limit for {unit.asil.value}). " + desc
            )
        items.append(StaticCheckItem(
            id=f"SCA-{project_key}-{start_id + i:04d}",
            unit_id=unit.id,
            unit_name=unit.name,
            component_name=unit.component_name,
            asil=unit.asil,
            category=cat,
            description=full_desc,
            tool=tool,
            acceptance_criteria=accept,
        ))
    return items


# ── Main generator ────────────────────────────────────────────────────────────

def verify_units(
    units: list[SwUnit], project_key: str
) -> tuple[list[UnitTestCase], list[StaticCheckItem], list[UnitVerificationLink]]:
    test_cases:    list[UnitTestCase]         = []
    static_checks: list[StaticCheckItem]      = []
    links:         list[UnitVerificationLink] = []
    tc_counter  = 1
    sca_counter = 1

    for unit in units:
        # Positive test
        tc_id = f"UVTC-{project_key}-{tc_counter:04d}"; tc_counter += 1
        tc = _positive_test(unit, tc_id)
        test_cases.append(tc)
        links.append(UnitVerificationLink(unit.id, tc_id, "dynamic_test"))

        # Negative test
        tc_id = f"UVTC-{project_key}-{tc_counter:04d}"; tc_counter += 1
        tc = _negative_test(unit, tc_id)
        test_cases.append(tc)
        links.append(UnitVerificationLink(unit.id, tc_id, "dynamic_test"))

        # Structural test (ASIL-A and above)
        if unit.asil in _NEEDS_STRUCTURAL:
            tc_id = f"UVTC-{project_key}-{tc_counter:04d}"; tc_counter += 1
            tc = _structural_test(unit, tc_id)
            test_cases.append(tc)
            links.append(UnitVerificationLink(unit.id, tc_id, "dynamic_test"))

        # Static analysis checks
        checks = _static_checks(unit, sca_counter, project_key)
        for chk in checks:
            static_checks.append(chk)
            links.append(UnitVerificationLink(unit.id, chk.id, "static_check"))
        sca_counter += len(checks)

    return test_cases, static_checks, links
