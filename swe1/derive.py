"""
Derive software requirements (SwRS) from system requirements (SyRS).

Each SyRS item produces one or more SwRS items via decomposition rules:
  - derives_functional       — always; the primary functional software obligation
  - derives_safety_mechanism — when ASIL-A/B/C/D; the SW detection + safe-reaction obligation
  - derives_cybersec_impl    — when cybersecurity_relevant; the SW security implementation + audit obligation

A single system requirement can therefore yield up to three SwRS items.
AI-assisted text refinement (FR-015) is a future extension — _derive_text() is the intended hook.
"""

from .models import ASIL, SyRSItem, SwRSItem, TraceabilityLink

DERIV_FUNCTIONAL  = "derives_functional"
DERIV_SAFETY_MECH = "derives_safety_mechanism"
DERIV_CYBERSEC    = "derives_cybersec_impl"

_ASIL_SAFETY_LEVELS = {ASIL.A, ASIL.B, ASIL.C, ASIL.D}

_FUNCTIONAL_PREFIX: dict[str, str] = {
    "functional":  "The software SHALL implement: ",
    "interface":   "The software interface SHALL conform to: ",
    "performance": "The software SHALL satisfy the following performance criterion: ",
    "constraint":  "The software implementation SHALL comply with the following constraint: ",
}


def _decompose_rules(sys_item: SyRSItem) -> list[str]:
    rules = [DERIV_FUNCTIONAL]
    if sys_item.asil in _ASIL_SAFETY_LEVELS:
        rules.append(DERIV_SAFETY_MECH)
    if sys_item.cybersecurity_relevant:
        rules.append(DERIV_CYBERSEC)
    return rules


def _derive_title(sys_item: SyRSItem, deriv_type: str) -> str:
    prefixes = {
        DERIV_FUNCTIONAL:  "[SW-FUNC]",
        DERIV_SAFETY_MECH: "[SW-SAF]",
        DERIV_CYBERSEC:    "[SW-SEC]",
    }
    suffixes = {
        DERIV_FUNCTIONAL:  "",
        DERIV_SAFETY_MECH: " — SW detection and safe reaction",
        DERIV_CYBERSEC:    " — SW security implementation and audit",
    }
    return f"{prefixes[deriv_type]} {sys_item.title}{suffixes[deriv_type]}"


def _derive_text(sys_item: SyRSItem, deriv_type: str) -> str:
    if deriv_type == DERIV_FUNCTIONAL:
        prefix = _FUNCTIONAL_PREFIX.get(sys_item.type, "The software SHALL satisfy: ")
        return f"{prefix}{sys_item.text}"

    if deriv_type == DERIV_SAFETY_MECH:
        return (
            f"The software SHALL implement a dedicated monitoring function for the "
            f"{sys_item.asil.value}-rated system requirement [{sys_item.id}]. "
            f"The monitoring function SHALL continuously evaluate compliance with the "
            f"system-level boundary conditions defined in [{sys_item.id}]. "
            f"On detection of a violation or out-of-range condition, the software SHALL "
            f"execute the defined safety reaction — safe state entry, degraded-mode "
            f"activation, or controlled shutdown — within the Fault Tolerant Time "
            f"Interval (FTTI) defined in the item HARA. Prior to executing the safety "
            f"reaction, the software SHALL store a Diagnostic Trouble Code (DTC) via "
            f"the AUTOSAR DEM interface identifying the detected fault condition, and "
            f"SHALL set the applicable fault status flag for consumption by the "
            f"Function Inhibition Manager (FIM)."
        )

    if deriv_type == DERIV_CYBERSEC:
        return (
            f"The software SHALL implement the cryptographic and access-control "
            f"mechanisms required to fulfil the cybersecurity obligations of system "
            f"requirement [{sys_item.id}]. All cryptographic operations SHALL be "
            f"performed exclusively via the AUTOSAR Crypto Service Manager (Csm) API "
            f"using algorithms and key lengths approved in the vehicle platform "
            f"cryptographic policy. Every security-relevant event arising from this "
            f"requirement — including authentication attempts, verification outcomes, "
            f"key usage, and policy enforcement decisions — SHALL be recorded in the "
            f"SUMS audit trail via the NvM manager as a tamper-evident HMAC-chained "
            f"log entry, in accordance with ISO/SAE 21434 WP-08-06 and UNECE R156 "
            f"software update audit requirements."
        )

    return sys_item.text


def _derive_rationale(sys_item: SyRSItem, deriv_type: str) -> str:
    if deriv_type == DERIV_FUNCTIONAL:
        return (
            f"Derived from system requirement {sys_item.id}. "
            f"Original rationale: {sys_item.rationale}"
        )
    if deriv_type == DERIV_SAFETY_MECH:
        return (
            f"ISO 26262 Part 6 requires that every {sys_item.asil.value}-rated functional "
            f"requirement has a corresponding software safety mechanism that detects "
            f"violations and executes the defined safety reaction within the FTTI. "
            f"This SwRS captures the SW detection and reaction obligations derived "
            f"from system requirement {sys_item.id}."
        )
    if deriv_type == DERIV_CYBERSEC:
        return (
            f"ISO/SAE 21434 Clause 10 requires that cybersecurity goals are implemented "
            f"as concrete technical security measures with audit evidence (WP-10-03). "
            f"This SwRS captures the SW security implementation and audit logging "
            f"obligations derived from cybersecurity-relevant system requirement "
            f"{sys_item.id}."
        )
    return ""


def _derive_type(sys_item: SyRSItem, deriv_type: str) -> str:
    if deriv_type == DERIV_SAFETY_MECH:
        return "safety_mechanism"
    if deriv_type == DERIV_CYBERSEC:
        return "security"
    return sys_item.type


def derive_swrs(
    syrs_items: list[SyRSItem], project_key: str
) -> tuple[list[SwRSItem], list[TraceabilityLink]]:
    swrs_items: list[SwRSItem] = []
    links: list[TraceabilityLink] = []
    counter = 1

    for sys_item in syrs_items:
        for deriv_type in _decompose_rules(sys_item):
            sw_id = f"SW-{project_key}-{counter:04d}"

            swrs_items.append(SwRSItem(
                id=sw_id,
                title=_derive_title(sys_item, deriv_type),
                text=_derive_text(sys_item, deriv_type),
                type=_derive_type(sys_item, deriv_type),
                asil=sys_item.asil,
                cybersecurity_relevant=(
                    sys_item.cybersecurity_relevant if deriv_type != DERIV_SAFETY_MECH else False
                ),
                verification_method=sys_item.verification_method,
                derived_from=sys_item.id,
                rationale=_derive_rationale(sys_item, deriv_type),
                tags=list(sys_item.tags) + [deriv_type.replace("derives_", "")],
                derivation_type=deriv_type,
            ))

            links.append(TraceabilityLink(
                source_id=sys_item.id,
                target_id=sw_id,
                link_type=deriv_type,
            ))

            counter += 1

    return swrs_items, links
