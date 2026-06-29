"""
Render a PlantUML sequence diagram for the SWE.5 integration sequence.

Shows representative unit pairs per layer (application, safety, security) and
the four integration stages as UML groupings. Uses AUTOSAR BSW service actors
(DEM, FIM, Csm, NvM) to illustrate cross-component interactions.
"""

from datetime import datetime, timezone

from swe2.models import SwComponent
from swe3.models import SwUnit

from .models import IntegrationStage


def _alias(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c == "_")


def render_integration_sequence(
    components: list[SwComponent],
    units: list[SwUnit],
    stages: list[IntegrationStage],
    project_key: str,
    metadata: dict,
) -> str:
    # Collect one representative unit pair per layer
    units_by_comp: dict[str, list[SwUnit]] = {}
    for u in units:
        units_by_comp.setdefault(u.component_id, []).append(u)

    app_pair: tuple | None = None
    safety_pair: tuple | None = None
    security_pair: tuple | None = None

    for comp in components:
        cu = units_by_comp.get(comp.id, [])
        if len(cu) >= 2:
            if comp.layer == "application" and app_pair is None:
                app_pair = (comp, cu[0], cu[1])
            elif comp.layer == "safety" and safety_pair is None:
                safety_pair = (comp, cu[0], cu[1])
            elif comp.layer == "security" and security_pair is None:
                security_pair = (comp, cu[0], cu[1])

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "@startuml",
        f"' AutoPragma — SWE.5 Integration Sequence — {project_key}",
        f"' Generated: {now}",
        "",
        "skinparam sequenceArrowThickness 2",
        "skinparam sequenceParticipantBorderColor #444",
        "skinparam sequenceGroupBorderColor #777",
        "skinparam noteBorderColor #aaa",
        "skinparam backgroundColor white",
        "",
        f"title SW Integration Sequence — {project_key}\\n"
        + f"(bottom-up, {len(stages)} stages)",
        "",
    ]

    # ── Participants ──────────────────────────────────────────────────────────

    if app_pair:
        _, ua, ub = app_pair
        lines += [
            f'participant "{ua.name}\\n(application)" as {_alias(ua.name)} <<application>>',
            f'participant "{ub.name}\\n(application)" as {_alias(ub.name)} <<application>>',
        ]
    if safety_pair:
        _, us, usr = safety_pair
        lines += [
            f'participant "{us.name}\\n(safety)" as {_alias(us.name)} <<safety>>',
            f'participant "{usr.name}\\n(safety)" as {_alias(usr.name)} <<safety>>',
        ]
    if security_pair:
        _, ucp, ual = security_pair
        lines += [
            f'participant "{ucp.name}\\n(security)" as {_alias(ucp.name)} <<security>>',
            f'participant "{ual.name}\\n(security)" as {_alias(ual.name)} <<security>>',
        ]

    # AUTOSAR BSW service actors
    lines += [
        "",
        'participant "DEM\\n(AUTOSAR BSW)" as DEM <<BSW>>',
        'participant "FIM\\n(AUTOSAR BSW)" as FIM <<BSW>>',
        'participant "Csm / NvM\\n(AUTOSAR BSW)" as CSM <<BSW>>',
        "",
    ]

    # ── Stage 1: Intra-component ──────────────────────────────────────────────
    lines.append("== Stage 1: Intra-Component Unit Integration ==")
    lines.append("")

    if app_pair:
        _, ua, ub = app_pair
        uaa, uba = _alias(ua.name), _alias(ub.name)
        primary_op = ub.interface.provided[0] if ub.interface.provided else None
        op = primary_op.name if primary_op else "process"
        ret = primary_op.return_type if primary_op else "Std_ReturnType"
        lines += [
            f"group Application — Interface Contract + Data Flow",
            f"  {uaa} -> {uba} : {op}(signal, timeout)",
            f"  note right",
            f"    Direct function call (intra-component)",
            f"    MISRA C:2012 Rule 17.7 — return value used",
            f"  end note",
            f"  {uba} --> {uaa} : {ret} (E_OK)",
            f"  {uaa} -> {uaa} : process result; update internal state",
            f"end",
            "",
        ]

    if safety_pair:
        _, us, usr = safety_pair
        usa, usra = _alias(us.name), _alias(usr.name)
        lines += [
            f"group Safety — FDTI/FTTI Timing Chain",
            f"  {usa} -> {usa} : monitor() [10 ms periodic]",
            f"  note right: Fault detection within FDTI (ISO 26262 Part 3)",
            f"  {usa} -> {usra} : executeSafeState(reason: FaultReason_t)",
            f"  {usra} --> {usa} : E_OK [within FTTI]",
            f"  {usa} -> DEM : Dem_SetEventStatus(FAULT_ID, TEST_FAILED)",
            f"  DEM --> {usa} : [event status byte updated]",
            f"end",
            "",
        ]

    if security_pair:
        _, ucp, ual = security_pair
        ucpa, uala = _alias(ucp.name), _alias(ual.name)
        lines += [
            f"group Security — Crypto-to-Audit Chain",
            f"  {ucpa} -> CSM : Csm_MacVerify(key, token, len, &result)",
            f"  CSM --> {ucpa} : E_OK / CRYPTO_E_VER_NOT_OK",
            f"  {ucpa} -> {uala} : logEvent(PERMIT | DENY, keyId)",
            f"  note right: ISO/SAE 21434 audit log entry",
            f"  {uala} -> CSM : NvM_WriteBlock(NVM_AUDIT_BLOCK, &entry)",
            f"  CSM --> {uala} : E_OK",
            f"  {uala} --> {ucpa} : E_OK",
            f"end",
            "",
        ]

    # ── Stage 2: Cross-component safety ──────────────────────────────────────
    if any(s.integration_level == "cross_component" and
           any("safety" in step.title.lower() for step in s.steps)
           for s in stages):
        lines.append("== Stage 2: Cross-Component Safety Supervision ==")
        lines.append("")

        if app_pair and safety_pair:
            _, ua, ub   = app_pair
            _, us, usr  = safety_pair
            uaa  = _alias(ua.name)
            usa  = _alias(us.name)
            usra = _alias(usr.name)
            lines += [
                f"group DEM/FIM Safety Supervision Chain",
                f"  {uaa} -> DEM : Dem_SetEventStatus(APP_FAULT_ID, TEST_FAILED)",
                f"  DEM -> FIM  : FIM inhibit signal update (FID mapping)",
                f"  FIM --> {uaa} : FimFunctionAvailability → FUNCTION_INHIBITED",
                f"  {usa} -> {usa} : monitor() detects DEM confirmed DTC",
                f"  {usa} -> {usra} : executeSafeState(APP_FAULT_ID)",
                f"  {usra} -> {usra} : drive ASIL-safe output",
                f"  note over {uaa}, {usra}",
                f"    End-to-end: fault → DEM → FIM inhibit → safe state",
                f"    must complete within FTTI (ISO 26262 Part 3)",
                f"  end note",
                f"end",
                "",
            ]

    # ── Stage 3: Cross-component security ────────────────────────────────────
    if any(s.integration_level == "cross_component" and
           any("security" in step.title.lower() for step in s.steps)
           for s in stages):
        lines.append("== Stage 3: Cross-Component Security Audit ==")
        lines.append("")

        if app_pair and security_pair:
            _, ua, _     = app_pair
            _, ucp, ual  = security_pair
            uaa  = _alias(ua.name)
            ucpa = _alias(ucp.name)
            uala = _alias(ual.name)
            lines += [
                f"group Csm/NvM Security Audit Chain",
                f"  {uaa} -> {ucpa} : Rte_Call_Security_Authenticate(token, len)",
                f"  {ucpa} -> CSM   : Csm_MacVerify(key, token, len, &result)",
                f"  CSM --> {ucpa}  : E_OK (PERMIT) or CRYPTO_E_VER_NOT_OK (DENY)",
                f"  {ucpa} -> {uala} : logEvent(PERMIT | DENY, keyId)",
                f"  {uala} -> CSM   : NvM_WriteBlock(NVM_AUDIT_BLOCK, &entry)",
                f"  CSM --> {uala}  : E_OK",
                f"  {ucpa} --> {uaa} : AUTH_OK or AUTH_FAILED",
                f"  note over {uaa}, {uala}",
                f"    No key material in AUTH_FAILED response (no info leakage)",
                f"    ISO/SAE 21434 audit log persisted to NvM",
                f"  end note",
                f"end",
                "",
            ]

    # ── Stage 4: Full integration ─────────────────────────────────────────────
    lines += [
        "== Stage 4: Full Software Integration ==",
        "",
        f"note over {_alias(units[0].name) if units else 'DEM'}, CSM",
        f"  All {len(components)} components integrated — no BSW stubs.",
        f"  All {sum(1 for s in stages if s.integration_level in ('intra_component','cross_component'))} "
        f"staged ITCs must PASS before full integration begins.",
        f"  Exit: integration test report filed as ASPICE SWE.5 evidence.",
        "end note",
        "",
        "@enduml",
    ]

    return "\n".join(lines)
