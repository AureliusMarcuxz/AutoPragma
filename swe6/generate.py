"""
Derive SW Qualification Test Specification (SQTS) from SwRS items.

Generation rules:
  - Each SwRS item yields exactly one test case.
  - Test type, environment, coverage requirement, and steps are
    driven by the item's derivation_type and ASIL classification.
  - ASIL-D/C   → HIL, MC/DC, Critical priority
  - ASIL-B/A   → HIL or SIL, branch/statement, High priority
  - QM          → SIL, statement, Medium priority
  - Safety Mech → fault-injection test
  - Cybersec    → security / boundary test
  - Functional  → behavioral (dynamic) or static, driven by
                  verification_method
"""

from swe1.derive import DERIV_CYBERSEC, DERIV_FUNCTIONAL, DERIV_SAFETY_MECH
from swe1.models import ASIL, SwRSItem, VerificationMethod

from .models import TestCase, TestCoverageLink, TestStep

_ASIL_PRIORITY = {
    ASIL.D: "critical",
    ASIL.C: "critical",
    ASIL.B: "high",
    ASIL.A: "high",
    ASIL.QM: "medium",
}

_ASIL_COVERAGE = {
    ASIL.D: "MC/DC",
    ASIL.C: "MC/DC",
    ASIL.B: "branch",
    ASIL.A: "statement",
    ASIL.QM: "statement",
}

_ASIL_ENVIRONMENT = {
    ASIL.D: "HIL",
    ASIL.C: "HIL",
    ASIL.B: "HIL",
    ASIL.A: "SIL",
    ASIL.QM: "SIL",
}


# ── Test type resolution ──────────────────────────────────────────────────────

def _test_type(item: SwRSItem) -> str:
    if item.derivation_type == DERIV_SAFETY_MECH:
        return "fault_injection"
    if item.derivation_type == DERIV_CYBERSEC:
        return "security"
    vm = item.verification_method
    if vm == VerificationMethod.INSPECTION:
        return "inspection"
    if vm == VerificationMethod.ANALYSIS:
        return "static_analysis"
    if vm == VerificationMethod.DEMONSTRATION:
        return "demonstration"
    return "behavioral"


def _test_method(item: SwRSItem) -> str:
    if item.derivation_type in (DERIV_SAFETY_MECH, DERIV_CYBERSEC):
        return "dynamic_test"
    vm = item.verification_method
    if vm == VerificationMethod.INSPECTION:
        return "inspection"
    if vm == VerificationMethod.ANALYSIS:
        return "static_analysis"
    if vm == VerificationMethod.DEMONSTRATION:
        return "demonstration"
    return "dynamic_test"


# ── Objective text ────────────────────────────────────────────────────────────

def _objective(item: SwRSItem) -> str:
    if item.derivation_type == DERIV_SAFETY_MECH:
        return (
            f"Verify that the software monitoring function for [{item.id}] correctly "
            f"detects out-of-range or violated boundary conditions and executes the "
            f"defined safe reaction (safe-state entry, degraded mode, or controlled "
            f"shutdown) within the Fault Tolerant Time Interval (FTTI). "
            f"Verify that a Diagnostic Trouble Code (DTC) is stored via the AUTOSAR "
            f"DEM interface upon fault detection, and that the FIM fault-status flag "
            f"is set correctly."
        )
    if item.derivation_type == DERIV_CYBERSEC:
        return (
            f"Verify that the cryptographic and access-control mechanisms implemented "
            f"for [{item.id}] correctly enforce the cybersecurity policy: authenticate "
            f"legitimate callers, reject unauthorized access attempts, and record all "
            f"security-relevant events as HMAC-chained audit-log entries in the NvM "
            f"SUMS trail (ISO/SAE 21434 WP-08-06)."
        )
    return (
        f"Verify that the software implementation of [{item.id}] produces the "
        f"correct outputs for all nominal operating conditions and specified boundary "
        f"values, and that the implementation is compliant with the requirement text "
        f"as stated in the SW Requirements Specification."
    )


# ── Preconditions ─────────────────────────────────────────────────────────────

def _preconditions(item: SwRSItem) -> list[str]:
    base = [
        "SW build under test is at a known baseline commit with all CI checks passing.",
        f"Test environment ({_ASIL_ENVIRONMENT[item.asil]}) is calibrated and "
        "connected; self-test passes.",
        f"Requirement [{item.id}] status is APPROVED in the ALM baseline.",
    ]
    if item.derivation_type == DERIV_SAFETY_MECH:
        base += [
            "FTTI value has been captured from the HARA and is available as a "
            "test parameter.",
            "AUTOSAR DEM module is initialised and NvM storage is in the erased "
            "state for the DTC under test.",
            "FIM channel configuration for this fault source is loaded and active.",
        ]
    if item.derivation_type == DERIV_CYBERSEC:
        base += [
            "Crypto Service Manager (Csm) is initialised with the approved key "
            "material for the target vehicle platform.",
            "NvM SUMS audit-log partition is erased; audit-log sequence number "
            "starts at 0.",
            "A valid caller identity (role / session token) is provisioned for "
            "the positive test path.",
        ]
    if item.asil in {ASIL.C, ASIL.D}:
        base.append(
            f"Independent safety monitor is active and configured to observe "
            f"the {item.asil.value}-rated output signals under test."
        )
    return base


# ── Test steps ────────────────────────────────────────────────────────────────

def _steps_behavioral(item: SwRSItem) -> list[TestStep]:
    return [
        TestStep(1,
            "Configure the test harness with nominal input stimuli derived from "
            f"the requirement boundary conditions of [{item.id}].",
            "Harness reports stimulus loaded successfully; no pre-condition faults."),
        TestStep(2,
            "Execute the function / runnable under test with nominal inputs "
            "(equivalence class: typical operating value).",
            "Output values are within the specified nominal range; no error flags set."),
        TestStep(3,
            "Apply lower boundary value inputs (minimum valid operating condition).",
            "Outputs remain within the specified range; no unintended side-effects."),
        TestStep(4,
            "Apply upper boundary value inputs (maximum valid operating condition).",
            "Outputs remain within the specified range; no unintended side-effects."),
        TestStep(5,
            f"Capture code coverage data and verify {_ASIL_COVERAGE[item.asil]} "
            "coverage is achieved for all branches/decisions in scope.",
            f"{_ASIL_COVERAGE[item.asil]} coverage ≥ 100 % for the module under test."),
        TestStep(6,
            "Log test results and capture a coverage report artefact.",
            "Test result artefact is stored and linked to this test case in the ALM."),
    ]


def _steps_fault_injection(item: SwRSItem) -> list[TestStep]:
    return [
        TestStep(1,
            "Start the system under test in the nominal operating mode; confirm "
            "no pre-existing DTCs in DEM.",
            "System in nominal mode; DEM NoDTCsActive."),
        TestStep(2,
            f"Inject a fault stimulus targeting the monitored signal/function of "
            f"[{item.id}] (e.g., out-of-range value, signal timeout, or stuck-at "
            "fault via hardware fault injector or SWFI).",
            "Fault injection acknowledged by test harness; stimulus active."),
        TestStep(3,
            "Measure the elapsed time from fault injection to safe-reaction "
            "completion (safe-state entry or degraded mode activation).",
            f"Safe reaction completes within the FTTI specified for [{item.id}]; "
            "no secondary faults induced."),
        TestStep(4,
            "Query the AUTOSAR DEM via the diagnostic tester for the expected DTC.",
            f"Correct DTC is set with status byte DTCStatusBit.confirmedDTC = 1; "
            "environment data records captured."),
        TestStep(5,
            "Verify the FIM fault-status flag for this fault source is set and "
            "that the inhibited functions are correctly deactivated.",
            "FIM inhibition is active for all functions linked to this fault source."),
        TestStep(6,
            "Clear the injected fault; verify system transitions back to nominal "
            "mode (or stays in degraded mode if defined by FTTI policy).",
            "System behaves as defined in the safety reaction specification; DTC "
            "status transitions correctly on fault clearance."),
    ]


def _steps_security(item: SwRSItem) -> list[TestStep]:
    return [
        TestStep(1,
            "Send a well-formed, authenticated request using a valid caller identity "
            f"for the security service under [{item.id}].",
            "Request is processed successfully; response contains valid cryptographic "
            "output; audit log records one ALLOW entry."),
        TestStep(2,
            "Replay the same request with an expired or tampered session token "
            "(authentication failure injection).",
            "Request is rejected; error code returned; audit log records one DENY "
            "entry with caller identity and timestamp."),
        TestStep(3,
            "Send a request that exceeds the authorised key-usage counter or "
            "violates the cryptographic policy (policy enforcement test).",
            "Operation is refused; CsmReturnValue = E_NOT_OK; audit log records "
            "one POLICY_VIOLATION entry."),
        TestStep(4,
            "Verify audit-log entry integrity: replay the HMAC-chained log and "
            "confirm the chain is unbroken and all entries are present.",
            "HMAC chain verification passes; no entries missing or reordered; "
            "sequence numbers are monotonically increasing."),
        TestStep(5,
            "Verify that audit-log entries are persisted in NvM across a power "
            "cycle (loss of volatile memory).",
            "After power cycle, all audit-log entries are recoverable from NvM "
            "and HMAC chain is intact."),
    ]


def _steps_inspection(item: SwRSItem) -> list[TestStep]:
    return [
        TestStep(1,
            f"Open the source module(s) implementing [{item.id}] in the code "
            "review tool and cross-reference against the requirement text.",
            "Reviewer confirms that all requirement clauses are addressable in "
            "the implementation."),
        TestStep(2,
            "Verify MISRA C compliance for the module(s) using the configured "
            "static analysis tool; record all deviations with justification.",
            "Zero unmitigated MISRA violations; all deviations are documented "
            "and approved."),
        TestStep(3,
            "Check that all function interfaces are documented with pre- and "
            "post-conditions matching the requirement constraints.",
            "Interface documentation is complete and consistent with requirement."),
        TestStep(4,
            "Record inspection findings in the review log; close the inspection "
            "record.",
            "Inspection log is signed off by reviewer and development lead; "
            "finding count is zero or all findings are resolved."),
    ]


def _steps_demonstration(item: SwRSItem) -> list[TestStep]:
    return [
        TestStep(1,
            f"Configure the target system in its intended operating environment "
            f"to exercise the capability described in [{item.id}].",
            "System is operational; pre-demonstration self-test passes."),
        TestStep(2,
            "Operate the system through the complete demonstration scenario "
            "as defined in the test plan, observed by the witness.",
            "System behaves as described in the requirement; witness confirms "
            "observable outcome matches expected behaviour."),
        TestStep(3,
            "Capture evidence artefacts (screenshots, log files, or video) "
            "of the demonstrated behaviour.",
            "Evidence artefacts are stored and linked to this test case in the ALM."),
        TestStep(4,
            "Witness signs the demonstration record.",
            "Signed demonstration record is stored as gate evidence."),
    ]


def _steps(item: SwRSItem) -> list[TestStep]:
    tt = _test_type(item)
    if tt == "fault_injection":
        return _steps_fault_injection(item)
    if tt == "security":
        return _steps_security(item)
    if tt == "inspection":
        return _steps_inspection(item)
    if tt == "demonstration":
        return _steps_demonstration(item)
    return _steps_behavioral(item)


# ── Pass / fail criteria ──────────────────────────────────────────────────────

def _pass_criteria(item: SwRSItem) -> str:
    if item.derivation_type == DERIV_SAFETY_MECH:
        return (
            "Safe reaction completes within FTTI; correct DTC is stored in DEM "
            "with expected status byte; FIM inhibition is active; no secondary "
            "faults induced. All sub-steps must PASS."
        )
    if item.derivation_type == DERIV_CYBERSEC:
        return (
            "Positive path succeeds; all unauthorized / policy-violating requests "
            "are rejected with correct error codes; every security-relevant event "
            "produces an audit-log entry; HMAC chain is intact after power cycle. "
            "All sub-steps must PASS."
        )
    return (
        f"All output values are within specification for nominal and boundary inputs; "
        f"{_ASIL_COVERAGE[item.asil]} coverage ≥ 100 %; no MISRA violations; "
        "no unintended side-effects. All sub-steps must PASS."
    )


def _fail_criteria(item: SwRSItem) -> str:
    if item.derivation_type == DERIV_SAFETY_MECH:
        return (
            "Safe reaction exceeds FTTI; DTC not set or incorrect; FIM inhibition "
            "not active; or any secondary fault induced. Any sub-step FAIL => "
            "test FAIL."
        )
    if item.derivation_type == DERIV_CYBERSEC:
        return (
            "Unauthorized request accepted; audit-log entry missing or HMAC chain "
            "broken; or NvM entries not recoverable after power cycle. Any sub-step "
            "FAIL => test FAIL."
        )
    return (
        "Any output value outside specification; coverage below required threshold; "
        "unmitigated MISRA violation; or unintended side-effect observed. Any "
        "sub-step FAIL => test FAIL."
    )


# ── Coverage tags ─────────────────────────────────────────────────────────────

def _coverage_tags(item: SwRSItem) -> list[str]:
    tags = [_ASIL_COVERAGE[item.asil]]
    if item.derivation_type == DERIV_SAFETY_MECH:
        tags += ["fault_injection", "DEM", "FIM", "safe_state"]
    elif item.derivation_type == DERIV_CYBERSEC:
        tags += ["authentication", "audit_log", "HMAC", "NvM_SUMS"]
    else:
        tags += ["boundary_value", "equivalence_class"]
    if item.asil in {ASIL.C, ASIL.D}:
        tags.append("independent_monitor")
    return tags


# ── Title ─────────────────────────────────────────────────────────────────────

def _title(item: SwRSItem) -> str:
    type_prefix = {
        "fault_injection":  "[SQTS-FAULT]",
        "security":         "[SQTS-SEC]",
        "inspection":       "[SQTS-INSP]",
        "demonstration":    "[SQTS-DEMO]",
        "static_analysis":  "[SQTS-ANALYSIS]",
        "behavioral":       "[SQTS-FUNC]",
    }
    prefix = type_prefix.get(_test_type(item), "[SQTS]")
    clean = (
        item.title
        .replace("[SW-FUNC] ", "")
        .replace("[SW-SAF] ", "")
        .replace("[SW-SEC] ", "")
    )
    return f"{prefix} {clean}"


# ── Main generator ────────────────────────────────────────────────────────────

def generate_sqts(
    swrs_items: list[SwRSItem], project_key: str
) -> tuple[list[TestCase], list[TestCoverageLink]]:
    test_cases: list[TestCase] = []
    links: list[TestCoverageLink] = []
    counter = 1

    for item in swrs_items:
        tc_id = f"TC-{project_key}-{counter:04d}"

        tc = TestCase(
            id=tc_id,
            title=_title(item),
            objective=_objective(item),
            test_type=_test_type(item),
            test_method=_test_method(item),
            environment=_ASIL_ENVIRONMENT[item.asil],
            asil=item.asil,
            cybersecurity_relevant=item.cybersecurity_relevant,
            priority=_ASIL_PRIORITY[item.asil],
            derived_from=item.id,
            preconditions=_preconditions(item),
            steps=_steps(item),
            pass_criteria=_pass_criteria(item),
            fail_criteria=_fail_criteria(item),
            coverage_requirement=_ASIL_COVERAGE[item.asil],
            coverage_tags=_coverage_tags(item),
        )

        test_cases.append(tc)
        links.append(TestCoverageLink(
            swrs_id=item.id,
            test_case_id=tc_id,
            coverage_type="full",
        ))
        counter += 1

    return test_cases, links
