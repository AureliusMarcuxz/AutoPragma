"""
SWE.5 Software Integration engine.

Produces:
  - IntegrationTestCase list (ITC-…) covering:
      intra_component:  interface_contract  — unit A → unit B calling convention
                        data_flow           — application layer end-to-end signal path
                        timing_interaction  — safety layer FDTI/FTTI deadline chain
                        security_chain      — security layer Csm/NvM audit path
                        error_propagation   — callee failure → caller propagation
      cross_component:  safety_chain        — DEM/FIM supervision across components
                        security_chain      — Csm/NvM audit across component boundary
  - IntegrationLink list tracing ITCs to unit or component pairs
  - IntegrationStage list (4 stages) expressing the bottom-up integration plan

Knowledge-base grounding:
  - MISRA C:2012 Rule 17.7 — return value of non-void function shall be used
  - MISRA C:2012 Rule 10.3 — no narrowing essential-type assignment
  - Embedded C §6.2 — never silently discard errors
  - Embedded C §14  — stack safety at call boundaries
  - AUTOSAR DEM: Dem_SetEventStatus / event status byte (autosar_classic.md §5.3)
  - AUTOSAR FIM: FimFunctionAvailability (autosar_classic.md §5.3)
  - AUTOSAR Csm / NvM: Csm_MacVerify, NvM_WriteBlock (autosar_classic.md §5.2/5.4)
  - ISO 26262 Part 3: FTTI / FDTI timing budget (iso_26262.md §5)
  - ISO/SAE 21434: audit log (PERMIT / DENY) requirement
"""

from swe1.models import ASIL
from swe2.models import SwComponent
from swe3.models import SwUnit

from .models import IntegrationLink, IntegrationStage, IntegrationStep, IntegrationTestCase

_ASIL_PRIORITY = {
    ASIL.D:  "critical",
    ASIL.C:  "critical",
    ASIL.B:  "high",
    ASIL.A:  "high",
    ASIL.QM: "medium",
}
_ASIL_ENV = {
    ASIL.D:  "HIL integration harness",
    ASIL.C:  "HIL integration harness",
    ASIL.B:  "HIL or SIL integration harness",
    ASIL.A:  "SIL integration harness",
    ASIL.QM: "SIL integration harness",
}


# ── Intra-component: interface contract ───────────────────────────────────────

def _interface_contract_itc(
    comp: SwComponent, unit_a: SwUnit, unit_b: SwUnit, itc_id: str
) -> IntegrationTestCase:
    primary_op  = unit_b.interface.provided[0] if unit_b.interface.provided else None
    op_name     = primary_op.name        if primary_op else "process"
    op_params   = primary_op.parameters  if primary_op else []
    op_return   = primary_op.return_type if primary_op else "Std_ReturnType"

    return IntegrationTestCase(
        id=itc_id,
        title=f"[ITC-INTF] {unit_a.name} → {unit_b.name}: interface contract",
        objective=(
            f"Verify that the call interface between {unit_a.name} (caller) and "
            f"{unit_b.name} (callee) satisfies the agreed contract: parameter types "
            f"({', '.join(op_params) or 'void'}), return type ({op_return}), and "
            f"return-value consumption per MISRA C:2012 Rule 17.7 (value of non-void "
            f"function shall be used). No implicit narrowing per MISRA Rule 10.3."
        ),
        test_type="interface_contract",
        environment=_ASIL_ENV[comp.asil],
        asil=comp.asil,
        cybersecurity_relevant=comp.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[comp.asil],
        integration_level="intra_component",
        units_under_test=[unit_a.name, unit_b.name],
        components_covered=[comp.name],
        preconditions=[
            f"Both {unit_a.name} and {unit_b.name} have individually passed "
            "SWE.4 unit verification (all dynamic tests and static analysis items).",
            f"Integration harness ({_ASIL_ENV[comp.asil]}) is initialised; "
            "all required stubs configured at nominal state.",
            "Both units compiled at the same baseline commit with zero unresolved "
            "MISRA C:2012 violations (per SWE.4 SCA items).",
        ],
        stimuli=[
            f"Invoke {unit_b.name}.{op_name}() from {unit_a.name} with nominal "
            f"parameter values ({', '.join(op_params) or 'no parameters'}).",
            "Observe the call at the integration boundary using the harness "
            "interception hook (stack-frame inspection or bus monitor).",
        ],
        expected_behavior=[
            f"{unit_b.name}.{op_name}() is invoked with the declared parameter types; "
            "no implicit essential-type conversion (MISRA Rule 10.3) occurs.",
            f"Return value ({op_return}) is captured and evaluated by {unit_a.name} "
            "— not discarded (MISRA Rule 17.7).",
            "No stack overflow or misaligned access at the call boundary "
            "(Embedded C §14 — stack safety).",
            "Post-condition state of both units matches the SWE.3 detailed design "
            "specification (Doxygen pre/post-condition contracts).",
        ],
        pass_criteria=(
            f"Call completes; return value consumed; no MISRA Rule 17.7 or 10.3 "
            f"violation flagged by static analysis; no runtime ABI error; "
            f"post-condition state of {unit_b.name} matches specification."
        ),
        fail_criteria=(
            "Call fails; return value discarded; parameter type mismatch; "
            "stack corruption detected; or any post-condition check fails."
        ),
        coverage_tags=["interface_contract", "MISRA_17_7", "MISRA_10_3", "ABI_safety"],
    )


# ── Intra-component: data flow (application layer) ────────────────────────────

def _data_flow_itc(
    comp: SwComponent, unit_a: SwUnit, unit_b: SwUnit, itc_id: str
) -> IntegrationTestCase:
    return IntegrationTestCase(
        id=itc_id,
        title=f"[ITC-DATA] {unit_a.name} → {unit_b.name}: end-to-end data flow",
        objective=(
            f"Verify that application data produced by {unit_a.name} is correctly "
            f"transferred to and consumed by {unit_b.name} via the internal interface. "
            "No data corruption, silent loss, integer overflow (Embedded C §7.1), "
            "or bit manipulation error (Embedded C §9) shall occur on the path."
        ),
        test_type="data_flow",
        environment=_ASIL_ENV[comp.asil],
        asil=comp.asil,
        cybersecurity_relevant=comp.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[comp.asil],
        integration_level="intra_component",
        units_under_test=[unit_a.name, unit_b.name],
        components_covered=[comp.name],
        preconditions=[
            f"{unit_a.name} and {unit_b.name} are integrated and the interface "
            "contract ITC for this pair has PASSED.",
            "Internal data elements of both units are initialised to reset values "
            "(Embedded C §6.2 — all variables initialised before use).",
            "Integration harness is monitoring all internal data paths.",
        ],
        stimuli=[
            f"Inject representative signal data into {unit_a.name}'s input interface "
            "covering: minimum value, maximum value, and nominal mid-range.",
            f"Allow {unit_a.name} to process and write the result to the shared "
            f"internal interface consumed by {unit_b.name}.",
            f"Trigger {unit_b.name} to read and process the data.",
        ],
        expected_behavior=[
            f"{unit_b.name} reads the exact value written by {unit_a.name}; "
            "no data corruption (bit errors, byte-swap, truncation) detected.",
            "No unsigned integer wrap-around (Embedded C §7.1) occurs "
            "on the data path under boundary inputs.",
            "No silent discard of data at the interface boundary "
            "(Embedded C §6.2).",
            f"Both units' internal state elements reflect the expected post-condition "
            "values per the SWE.3 detailed design.",
        ],
        pass_criteria=(
            "All three input ranges (min, max, nominal) produce correct output "
            "in {unit_b.name}; no data integrity error or silent loss detected; "
            "internal state consistent with SWE.3 specification."
        ),
        fail_criteria=(
            "Data corruption detected; silent loss at interface; integer overflow "
            "or truncation observed; or internal state inconsistent with specification."
        ),
        coverage_tags=["data_flow", "integer_boundaries", "no_silent_loss"],
    )


# ── Intra-component: timing interaction (safety layer) ───────────────────────

def _timing_interaction_itc(
    comp: SwComponent, unit_a: SwUnit, unit_b: SwUnit, itc_id: str
) -> IntegrationTestCase:
    return IntegrationTestCase(
        id=itc_id,
        title=f"[ITC-TIME] {unit_a.name} → {unit_b.name}: FDTI/FTTI timing chain",
        objective=(
            f"Verify the end-to-end timing of the safety supervision chain: "
            f"{unit_a.name} (fault detection) must detect a fault and invoke "
            f"{unit_b.name} (safe reaction) within the Fault Detection Time Interval "
            f"(FDTI); {unit_b.name} must drive the safe state within the Fault Tolerant "
            f"Time Interval (FTTI) as defined by ISO 26262 Part 3."
        ),
        test_type="timing_interaction",
        environment="HIL integration harness",  # timing requires HIL
        asil=comp.asil,
        cybersecurity_relevant=comp.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[comp.asil],
        integration_level="intra_component",
        units_under_test=[unit_a.name, unit_b.name],
        components_covered=[comp.name],
        preconditions=[
            f"Both {unit_a.name} and {unit_b.name} have passed SWE.4 unit verification.",
            "HIL harness timestamp injection is configured with ≤ 1 ms resolution.",
            "FTTI and FDTI values are taken from the system-level safety concept "
            "(ISO 26262 Part 4) and configured in the HIL test script.",
            f"DEM stub is configured to record all Dem_SetEventStatus() calls "
            f"with timestamps.",
        ],
        stimuli=[
            f"Inject a hardware-level fault stimulus via HIL (e.g., signal stuck-at "
            f"or out-of-range) to trigger {unit_a.name}'s monitoring function.",
            f"Timestamp T0 = injection time; record T1 = {unit_a.name} detection time; "
            f"record T2 = {unit_b.name} safe-state output time.",
            "Repeat for fault types: stuck-at-high, stuck-at-low, oscillating.",
        ],
        expected_behavior=[
            f"{unit_a.name} detects the fault within FDTI: (T1 - T0) ≤ FDTI.",
            f"{unit_b.name} drives the safe-state output within FTTI: "
            f"(T2 - T0) ≤ FTTI.",
            f"DEM stub records Dem_SetEventStatus({unit_a.name}_FAULT_ID, "
            "DEM_EVENT_STATUS_FAILED) exactly once per fault event.",
            "No spurious safe-state activations during nominal (non-fault) operation.",
        ],
        pass_criteria=(
            "FDTI and FTTI deadlines met for all fault injection variants; "
            "DEM event correctly recorded; no spurious activations; "
            "HIL timing trace stored as gate evidence (ISO 26262 Part 6 §9)."
        ),
        fail_criteria=(
            "FTTI or FDTI deadline exceeded; DEM event missing or duplicated; "
            "spurious safe-state activation observed; or HIL trace unavailable."
        ),
        coverage_tags=["timing_interaction", "FTTI", "FDTI", "ISO_26262_P3", "DEM"],
    )


# ── Intra-component: security chain (security layer) ─────────────────────────

def _security_chain_itc(
    comp: SwComponent, unit_a: SwUnit, unit_b: SwUnit, itc_id: str
) -> IntegrationTestCase:
    return IntegrationTestCase(
        id=itc_id,
        title=f"[ITC-SEC] {unit_a.name} → {unit_b.name}: crypto-to-audit chain",
        objective=(
            f"Verify the intra-component security chain: {unit_a.name} performs "
            f"Csm_MacVerify / Csm_Encrypt and passes the result to {unit_b.name} "
            f"(AuditLogger), which persists the PERMIT or DENY event to NvM via "
            f"NvM_WriteBlock. Verify both the happy path and the authentication-failure "
            f"path; no information leakage on failure (ISO/SAE 21434 audit log)."
        ),
        test_type="security_chain",
        environment=_ASIL_ENV[comp.asil],
        asil=comp.asil,
        cybersecurity_relevant=True,
        priority=_ASIL_PRIORITY[comp.asil],
        integration_level="intra_component",
        units_under_test=[unit_a.name, unit_b.name],
        components_covered=[comp.name],
        preconditions=[
            f"Both {unit_a.name} and {unit_b.name} have passed SWE.4 unit verification.",
            "Csm stub is configured to simulate both E_OK and CRYPTO_E_VER_NOT_OK.",
            "NvM stub is configured to confirm write acceptance (E_OK) and "
            "then simulate write failure (E_NOT_OK) in a second test run.",
            "Volatile audit log is cleared before each test run.",
        ],
        stimuli=[
            f"Path A — PERMIT: call {unit_a.name}.authenticate() with a valid MAC token; "
            f"Csm stub returns E_OK; observe {unit_b.name}.logEvent(PERMIT, keyId).",
            f"Path B — DENY: call {unit_a.name}.authenticate() with an invalid / tampered "
            f"token; Csm stub returns CRYPTO_E_VER_NOT_OK; observe "
            f"{unit_b.name}.logEvent(DENY, keyId).",
            "Path C — NvM failure: valid token but NvM_WriteBlock returns E_NOT_OK; "
            "verify volatile fallback log captures the event.",
        ],
        expected_behavior=[
            f"Path A: {unit_b.name} records PERMIT entry with correct keyId and "
            "timestamp; NvM_WriteBlock called exactly once.",
            f"Path B: {unit_b.name} records DENY entry; {unit_a.name} returns AUTH_FAILED "
            "to caller; no sensitive key material in output buffers.",
            "Path C: volatile audit log captures the event; no silent loss; "
            "NvM error does not crash {unit_a.name} or {unit_b.name}.",
        ],
        pass_criteria=(
            "All three paths produce correct audit log entries; NvM persistence "
            "confirmed on Path A; no information leakage on Path B; graceful "
            "NvM-failure handling on Path C; Csm stub call counts match expectations."
        ),
        fail_criteria=(
            "Missing or incorrect audit log entry; information leakage on DENY path; "
            "crash or undefined behaviour on NvM failure; Csm stub call count mismatch."
        ),
        coverage_tags=["security_chain", "Csm_MacVerify", "NvM_WriteBlock",
                       "audit_log", "ISO_21434", "no_info_leakage"],
    )


# ── Intra-component: error propagation (all layers) ──────────────────────────

def _error_propagation_itc(
    comp: SwComponent, unit_a: SwUnit, unit_b: SwUnit, itc_id: str
) -> IntegrationTestCase:
    if comp.layer == "safety":
        stimuli = [
            f"Configure {unit_b.name} (SafeReactionExecutor) stub to return E_NOT_OK "
            "when executeSafeState() is called.",
            f"Trigger a fault detection event in {unit_a.name} (FaultDetector); "
            "observe how it handles the downstream failure.",
        ]
        expected = [
            f"{unit_a.name} receives E_NOT_OK from {unit_b.name} and does not "
            "silently discard it (Embedded C §6.2).",
            f"A secondary DEM event (SAFE_REACTION_FAILED) is raised to signal the "
            "loss of the safety mechanism (defense-in-depth).",
            "No undefined behaviour, memory corruption, or watchdog reset occurs.",
        ]
        pass_c = (
            "Secondary DEM event raised; error not silently discarded; "
            "system remains in a defined (degraded) state; no crash."
        )
    elif comp.layer == "security":
        stimuli = [
            f"Configure NvM stub inside {unit_b.name} (AuditLogger) to return E_NOT_OK.",
            f"Trigger {unit_a.name} (CryptoProvider) to invoke logEvent; "
            "observe fallback handling.",
        ]
        expected = [
            f"{unit_b.name} switches to volatile (RAM-only) audit log without "
            "silent loss of the security event.",
            f"{unit_a.name} receives the fallback status; no sensitive data leaks.",
            "System continues to function; no crash or undefined behaviour.",
        ]
        pass_c = (
            "Volatile fallback active; security event not lost; no information "
            "leakage; graceful degradation confirmed."
        )
    else:
        primary_op = unit_b.interface.provided[0] if unit_b.interface.provided else None
        op_name    = primary_op.name if primary_op else "process"
        stimuli = [
            f"Configure {unit_b.name} to return E_NOT_OK from {op_name}() "
            "(stub injection or compile-time test variant).",
            f"Call {op_name}() from {unit_a.name} and observe error handling path.",
            "Verify no silent failure: error must be propagated to the caller of "
            f"{unit_a.name} (Embedded C §6.2 — never silently discard errors).",
        ]
        expected = [
            f"{unit_a.name} captures E_NOT_OK and returns an error code to its caller; "
            "no silent swallow.",
            f"Internal state of {unit_a.name} remains consistent (no partial update); "
            "post-condition matches the defined error state in SWE.3.",
            "No crash, hang, or memory corruption at the integration boundary.",
        ]
        pass_c = (
            "Error returned to caller; internal state consistent; no silent failure; "
            "no crash or memory corruption detected."
        )

    return IntegrationTestCase(
        id=itc_id,
        title=f"[ITC-EPROP] {unit_b.name} → {unit_a.name}: error propagation",
        objective=(
            f"Verify that a failure returned by {unit_b.name} is correctly propagated "
            f"by {unit_a.name} to its caller without silent discard "
            f"(Embedded C §6.2 — never silently discard errors; "
            f"MISRA C:2012 Rule 17.7 — return value shall be used). "
            "Internal state must remain consistent after the failure."
        ),
        test_type="error_propagation",
        environment=_ASIL_ENV[comp.asil],
        asil=comp.asil,
        cybersecurity_relevant=comp.cybersecurity_relevant,
        priority=_ASIL_PRIORITY[comp.asil],
        integration_level="intra_component",
        units_under_test=[unit_a.name, unit_b.name],
        components_covered=[comp.name],
        preconditions=[
            f"Interface contract ITC for {unit_a.name}/{unit_b.name} has PASSED.",
            "Integration harness is configured to inject failure codes into "
            f"{unit_b.name}'s return path.",
            f"Internal state of {unit_a.name} is at a known valid pre-condition.",
        ],
        stimuli=stimuli,
        expected_behavior=expected,
        pass_criteria=pass_c,
        fail_criteria=(
            "Error silently discarded; internal state corrupted; crash or undefined "
            "behaviour; or error not propagated to the caller of the integrated pair."
        ),
        coverage_tags=["error_propagation", "MISRA_17_7", "no_silent_failure",
                       "Embedded_C_6_2"],
    )


# ── Cross-component: safety supervision chain ────────────────────────────────

def _cross_safety_chain_itc(
    safety_comp: SwComponent, app_comp: SwComponent, itc_id: str
) -> IntegrationTestCase:
    return IntegrationTestCase(
        id=itc_id,
        title=(
            f"[ITC-XSAF] {safety_comp.name} supervises {app_comp.name}: "
            "DEM/FIM safety chain"
        ),
        objective=(
            f"Verify the cross-component safety supervision chain: "
            f"{app_comp.name} raises a DEM fault event; "
            f"{safety_comp.name} (FaultDetector) detects it via DEM event status; "
            "FIM updates FimFunctionAvailability to FUNCTION_INHIBITED; "
            "SafeReactionExecutor drives the safe-state output within FTTI. "
            "Grounded in AUTOSAR DEM (autosar_classic.md §5.3) and "
            "ISO 26262 Part 3 (FTTI/FDTI)."
        ),
        test_type="safety_chain",
        environment="HIL integration harness",
        asil=safety_comp.asil,
        cybersecurity_relevant=False,
        priority=_ASIL_PRIORITY[safety_comp.asil],
        integration_level="cross_component",
        units_under_test=[
            f"{safety_comp.name}: FaultDetector, SafeReactionExecutor",
        ],
        components_covered=[safety_comp.name, app_comp.name],
        preconditions=[
            f"All intra-component ITCs for {safety_comp.name} and {app_comp.name} "
            "have PASSED.",
            "Both components are compiled and loaded in the same integration build.",
            "AUTOSAR DEM and FIM are configured with the correct event ID and "
            "FID-to-function mapping for this component pair.",
            "HIL harness timestamps all DEM calls with ≤ 1 ms resolution.",
        ],
        stimuli=[
            f"Inject a fault into {app_comp.name} via HIL to trigger "
            f"Dem_SetEventStatus(APP_FAULT_ID, DEM_EVENT_STATUS_FAILED).",
            f"Observe: DEM event status → FIM inhibit update → "
            f"{safety_comp.name} FaultDetector polling → SafeReactionExecutor call.",
            "Verify FTTI budget: time from fault injection to safe-state output "
            "≤ FTTI specified in the Technical Safety Concept.",
        ],
        expected_behavior=[
            f"Dem_SetEventStatus() from {app_comp.name} sets the confirmed DTC "
            "within FDTI.",
            "FIM updates FimFunctionAvailability(FID_APP_FUNCTION) to "
            "FUNCTION_INHIBITED; application function is suppressed.",
            "SafeReactionExecutor drives the ASIL-safe output within FTTI.",
            "No unintended inhibition of unrelated FIDs (side-effect free).",
        ],
        pass_criteria=(
            "DTC confirmed; FIM inhibit applied; safe-state driven within FTTI; "
            "no spurious FID inhibition; HIL timing trace stored as evidence."
        ),
        fail_criteria=(
            "DTC not confirmed; FIM inhibit missing or applied to wrong FID; "
            "FTTI deadline exceeded; safe-state not reached; or spurious inhibition."
        ),
        coverage_tags=["safety_chain", "DEM", "FIM", "FTTI", "FDTI",
                       "AUTOSAR_DEM", "AUTOSAR_FIM", "cross_component"],
    )


# ── Cross-component: security audit chain ────────────────────────────────────

def _cross_security_chain_itc(
    sec_comp: SwComponent, app_comp: SwComponent, itc_id: str
) -> IntegrationTestCase:
    return IntegrationTestCase(
        id=itc_id,
        title=(
            f"[ITC-XSEC] {sec_comp.name} secures {app_comp.name}: "
            "Csm/NvM audit chain"
        ),
        objective=(
            f"Verify the cross-component security audit chain: "
            f"{app_comp.name} requests authentication from {sec_comp.name} "
            "(CryptoProvider) via a C/S Rte_Call_* interface; CryptoProvider invokes "
            "Csm_MacVerify; the result triggers AuditLogger to persist a PERMIT or DENY "
            "entry via NvM_WriteBlock. Grounded in AUTOSAR Csm/NvM "
            "(autosar_classic.md §5.2/5.4) and ISO/SAE 21434 audit log requirement."
        ),
        test_type="security_chain",
        environment=_ASIL_ENV[sec_comp.asil],
        asil=sec_comp.asil,
        cybersecurity_relevant=True,
        priority=_ASIL_PRIORITY[sec_comp.asil],
        integration_level="cross_component",
        units_under_test=[
            f"{sec_comp.name}: CryptoProvider, AuditLogger",
        ],
        components_covered=[sec_comp.name, app_comp.name],
        preconditions=[
            f"All intra-component ITCs for {sec_comp.name} and {app_comp.name} "
            "have PASSED.",
            "Both components are compiled and loaded in the same integration build.",
            "AUTOSAR Csm and NvM blocks are configured; key material provisioned "
            "in the Csm key manager.",
            "NvM audit log block initialised (ROM default if first write).",
        ],
        stimuli=[
            f"Path A: {app_comp.name} calls Rte_Call_Security_Authenticate(validToken) "
            "→ CryptoProvider → Csm_MacVerify returns E_OK → AuditLogger PERMIT.",
            f"Path B: {app_comp.name} calls Rte_Call_Security_Authenticate(badToken) "
            "→ CryptoProvider → Csm_MacVerify returns CRYPTO_E_VER_NOT_OK "
            "→ AuditLogger DENY; caller receives AUTH_FAILED.",
            "Path C: NvM_WriteBlock returns E_NOT_OK → volatile fallback; "
            "event must not be silently lost.",
        ],
        expected_behavior=[
            f"Path A: {app_comp.name} receives AUTH_OK; NvM PERMIT entry written "
            "with keyId and timestamp; no key material in RTE output buffer.",
            f"Path B: {app_comp.name} receives AUTH_FAILED; NvM DENY entry written; "
            "no sensitive key information returned to caller (no leakage).",
            "Path C: volatile log captures event; NvM error does not crash system; "
            "graceful degradation confirmed.",
        ],
        pass_criteria=(
            "All three paths verified; NvM entries correct on Paths A and B; "
            "no information leakage on Path B; graceful fallback on Path C; "
            "Csm call counts match; audit log entries auditable."
        ),
        fail_criteria=(
            "Missing or incorrect NvM entry; information leakage to caller on DENY; "
            "crash on NvM failure; or authentication result incorrect."
        ),
        coverage_tags=["security_chain", "Csm_MacVerify", "NvM_WriteBlock",
                       "Rte_Call", "audit_log", "ISO_21434", "cross_component",
                       "no_info_leakage"],
    )


# ── Main generator ────────────────────────────────────────────────────────────

def integrate_components(
    components: list[SwComponent],
    units: list[SwUnit],
    project_key: str,
) -> tuple[list[IntegrationTestCase], list[IntegrationLink], list[IntegrationStage]]:
    units_by_comp: dict[str, list[SwUnit]] = {}
    for u in units:
        units_by_comp.setdefault(u.component_id, []).append(u)

    itcs:  list[IntegrationTestCase] = []
    links: list[IntegrationLink]     = []
    counter = 1

    stage1_steps: list[IntegrationStep] = []
    stage2_steps: list[IntegrationStep] = []
    stage3_steps: list[IntegrationStep] = []
    stage1_comps: list[str] = []
    stage2_comps: list[str] = []
    stage3_comps: list[str] = []

    app_comps = [c for c in components if c.layer == "application"]

    # ── Stage 1: intra-component unit integration ──────────────────────────────
    for comp in components:
        comp_units = units_by_comp.get(comp.id, [])
        if len(comp_units) < 2:
            continue

        unit_a, unit_b = comp_units[0], comp_units[1]

        # interface_contract
        itc_id = f"ITC-{project_key}-{counter:04d}"; counter += 1
        itcs.append(_interface_contract_itc(comp, unit_a, unit_b, itc_id))
        links.append(IntegrationLink(itc_id, unit_a.id, unit_b.id, "unit_pair"))

        # layer-specific middle test
        itc_id = f"ITC-{project_key}-{counter:04d}"; counter += 1
        if comp.layer == "safety":
            itcs.append(_timing_interaction_itc(comp, unit_a, unit_b, itc_id))
        elif comp.layer == "security":
            itcs.append(_security_chain_itc(comp, unit_a, unit_b, itc_id))
        else:
            itcs.append(_data_flow_itc(comp, unit_a, unit_b, itc_id))
        links.append(IntegrationLink(itc_id, unit_a.id, unit_b.id, "unit_pair"))

        # error_propagation
        itc_id = f"ITC-{project_key}-{counter:04d}"; counter += 1
        itcs.append(_error_propagation_itc(comp, unit_a, unit_b, itc_id))
        links.append(IntegrationLink(itc_id, unit_b.id, unit_a.id, "unit_pair"))

        stubs = list(set(unit_a.interface.required + unit_b.interface.required))[:4]
        step_n = len(stage1_steps) + 1
        mid_label = (
            "FDTI/FTTI timing"  if comp.layer == "safety"   else
            "crypto-audit chain" if comp.layer == "security" else
            "data flow"
        )
        stage1_steps.append(IntegrationStep(
            step_number=step_n,
            title=f"Integrate {comp.name}: {unit_a.name} + {unit_b.name}",
            units=[unit_a.name, unit_b.name],
            components=[comp.name],
            stubs_needed=stubs if stubs else ["No external stubs required"],
            exit_criteria=(
                f"Interface contract, {mid_label}, and error propagation ITCs "
                f"for {comp.name} all PASS."
            ),
        ))
        stage1_comps.append(comp.id)

    # ── Stage 2: cross-component safety supervision ────────────────────────────
    for safety_comp in [c for c in components if c.layer == "safety"]:
        for monitored_name in safety_comp.monitors:
            app = next((c for c in app_comps if c.name == monitored_name), None)
            if not app:
                continue

            itc_id = f"ITC-{project_key}-{counter:04d}"; counter += 1
            itcs.append(_cross_safety_chain_itc(safety_comp, app, itc_id))
            links.append(IntegrationLink(itc_id, safety_comp.id, app.id, "component_pair"))

            step_n = len(stage2_steps) + 1
            stage2_steps.append(IntegrationStep(
                step_number=step_n,
                title=f"Safety supervision: {safety_comp.name} → {monitored_name}",
                units=[
                    f"{safety_comp.name}: FaultDetector, SafeReactionExecutor",
                    f"{monitored_name}: application units",
                ],
                components=[safety_comp.name, monitored_name],
                stubs_needed=["DEM (AUTOSAR)", "FIM (AUTOSAR)", "SchM exclusive area"],
                exit_criteria=(
                    f"DEM fault event from {monitored_name} triggers FIM inhibit "
                    f"and {safety_comp.name} safe-state execution within FTTI."
                ),
            ))
            stage2_comps.extend([safety_comp.id, app.id])

    # ── Stage 3: cross-component security audit ────────────────────────────────
    for sec_comp in [c for c in components if c.layer == "security"]:
        for secured_name in sec_comp.secures:
            app = next((c for c in app_comps if c.name == secured_name), None)
            if not app:
                continue

            itc_id = f"ITC-{project_key}-{counter:04d}"; counter += 1
            itcs.append(_cross_security_chain_itc(sec_comp, app, itc_id))
            links.append(IntegrationLink(itc_id, sec_comp.id, app.id, "component_pair"))

            step_n = len(stage3_steps) + 1
            stage3_steps.append(IntegrationStep(
                step_number=step_n,
                title=f"Security audit chain: {sec_comp.name} ↔ {secured_name}",
                units=[
                    f"{sec_comp.name}: CryptoProvider, AuditLogger",
                    f"{secured_name}: application units",
                ],
                components=[sec_comp.name, secured_name],
                stubs_needed=["Csm (AUTOSAR)", "NvM (AUTOSAR)", "SchM exclusive area"],
                exit_criteria=(
                    f"Csm_MacVerify + AuditLogger NvM persistence verified on "
                    f"PERMIT, DENY, and NvM-failure paths for "
                    f"{sec_comp.name} ↔ {secured_name}."
                ),
            ))
            stage3_comps.extend([sec_comp.id, app.id])

    # ── Stage 4: full software integration ────────────────────────────────────
    full_step = IntegrationStep(
        step_number=1,
        title="Full software integration — all components",
        units=[u.name for u in units],
        components=[c.name for c in components],
        stubs_needed=["All BSW modules live (no stubs)"],
        exit_criteria=(
            "All integration test cases PASS. End-to-end data flow, safety-chain "
            "timing, and security audit chain verified with full software build. "
            "Integration test report generated as ASPICE SWE.5 work product evidence."
        ),
    )

    stages: list[IntegrationStage] = []
    if stage1_steps:
        stages.append(IntegrationStage(
            stage_number=1,
            title="Intra-Component Unit Integration",
            description=(
                "Integrate SW unit pairs within each component in isolation. "
                "Verify interface contracts (MISRA C:2012 Rule 17.7 — return value "
                "used; Rule 10.3 — no narrowing), data flows (Embedded C §6.2 — no "
                "silent loss), timing chains (ISO 26262 FTTI/FDTI for safety units), "
                "and Csm/NvM audit chains (ISO/SAE 21434 for security units)."
            ),
            integration_level="intra_component",
            steps=stage1_steps,
            components_covered=list(dict.fromkeys(stage1_comps)),
        ))
    if stage2_steps:
        stages.append(IntegrationStage(
            stage_number=2,
            title="Cross-Component Safety Supervision Integration",
            description=(
                "Integrate safety components with the application components they "
                "monitor via the AUTOSAR DEM/FIM chain. Verify DEM event propagation, "
                "FIM function inhibition, and safe-state execution within FTTI "
                "(ISO 26262 Part 3)."
            ),
            integration_level="cross_component",
            steps=stage2_steps,
            components_covered=list(dict.fromkeys(stage2_comps)),
        ))
    if stage3_steps:
        stages.append(IntegrationStage(
            stage_number=3,
            title="Cross-Component Security Audit Chain Integration",
            description=(
                "Integrate security components with the application components they "
                "secure via the AUTOSAR Csm/NvM chain. Verify Csm_MacVerify invocation, "
                "AuditLogger NvM persistence on PERMIT/DENY paths, and graceful "
                "NvM-failure fallback (ISO/SAE 21434)."
            ),
            integration_level="cross_component",
            steps=stage3_steps,
            components_covered=list(dict.fromkeys(stage3_comps)),
        ))

    stages.append(IntegrationStage(
        stage_number=len(stages) + 1,
        title="Full Software Integration",
        description=(
            "All software components integrated in the target build configuration "
            "with no BSW stubs. Full end-to-end integration tests executed. "
            "Exit: all ITC cases PASS; integration test report filed as ASPICE SWE.5 "
            "work product evidence."
        ),
        integration_level="full",
        steps=[full_step],
        components_covered=[c.id for c in components],
    ))

    return itcs, links, stages
