"""
SWE.2 allocation engine: derive SW components from SwRS items and allocate
each requirement to exactly one component.

Decomposition strategy:
  - derives_safety_mechanism items  → cross-cutting SafetyMonitor (safety layer)
  - derives_cybersec_impl items     → cross-cutting SecManager (security layer)
  - derives_functional items        → domain-specific component (application layer)
    Domain extracted from the parent SyRS ID (e.g. SYS-IC-CAN-001 → CAN → ComStack)
"""

import json
from pathlib import Path

from swe1.derive import DERIV_CYBERSEC, DERIV_FUNCTIONAL, DERIV_SAFETY_MECH
from swe1.models import ASIL, SwRSItem, VerificationMethod

from .models import AllocationLink, SwComponent

# Domain code → (component name, description suffix)
_DOMAIN_MAP: dict[str, tuple[str, str]] = {
    "PWR": ("PwrMgr",    "power supply and voltage monitoring"),
    "CAN": ("ComStack",  "CAN/CAN-FD communication stack"),
    "SAF": ("SafetyMon", "safety mechanism orchestration"),
    "OTA": ("OtaMgr",    "OTA update and integrity management"),
    "VSC": ("VscDisplay","vehicle signal display and rendering"),
    "ETH": ("EthStack",  "Ethernet/DoIP communication stack"),
    "NM":  ("NmMgr",     "network management"),
    "DIAG":("DiagMgr",   "diagnostics and DTC management"),
}

_ASIL_ORDER = [ASIL.D, ASIL.C, ASIL.B, ASIL.A, ASIL.QM]


def _highest_asil(asils: list[ASIL]) -> ASIL:
    for level in _ASIL_ORDER:
        if level in asils:
            return level
    return ASIL.QM


def _extract_domain(swrs_item: SwRSItem) -> str:
    # derived_from format: SYS-<PROJECT>-<DOMAIN>-<NNN>
    parts = swrs_item.derived_from.split("-")
    return parts[2].upper() if len(parts) >= 3 else "MISC"


def allocate_swad(
    swrs_items: list[SwRSItem], project_key: str
) -> tuple[list[SwComponent], list[AllocationLink]]:
    components: dict[str, SwComponent] = {}
    links: list[AllocationLink] = []
    counter = 1

    # Track which app-domain each cross-cutting component touches
    safety_domains: set[str] = set()
    cybersec_domains: set[str] = set()

    # --- Phase 1: create components and collect allocation links ---
    for item in swrs_items:
        domain = _extract_domain(item)

        if item.derivation_type == DERIV_SAFETY_MECH:
            key = "__safety__"
            if key not in components:
                components[key] = SwComponent(
                    id=f"COMP-{project_key}-{counter:04d}",
                    name="SafetyMonitor",
                    layer="safety",
                    description=(
                        "Cross-cutting safety monitoring component. Implements SW safety "
                        "mechanisms for all ASIL-rated requirements: fault detection, "
                        "AUTOSAR DEM DTC storage, FIM fault-flag management, and "
                        "safe-state reaction execution within the FTTI derived from HARA."
                    ),
                    asil=item.asil,
                    cybersecurity_relevant=False,
                )
                counter += 1
            comp = components[key]
            comp.asil = _highest_asil([comp.asil, item.asil])
            comp.allocated_swrs.append(item.id)
            safety_domains.add(domain)
            links.append(AllocationLink(
                swrs_id=item.id,
                component_id=comp.id,
                component_name=comp.name,
                rationale=(
                    f"Safety mechanism requirement allocated to the cross-cutting "
                    f"SafetyMonitor component per ISO 26262-6 freedom-from-interference "
                    f"partitioning (OS Application boundary + SMPU/PPU enforcement)."
                ),
            ))

        elif item.derivation_type == DERIV_CYBERSEC:
            key = "__security__"
            if key not in components:
                components[key] = SwComponent(
                    id=f"COMP-{project_key}-{counter:04d}",
                    name="SecManager",
                    layer="security",
                    description=(
                        "Cross-cutting security manager component. Implements all "
                        "cryptographic operations via the AUTOSAR Crypto Service Manager "
                        "(Csm) API and maintains the SUMS tamper-evident audit trail in "
                        "NvM per ISO/SAE 21434 WP-08-06 and UNECE R156."
                    ),
                    asil=item.asil,
                    cybersecurity_relevant=True,
                )
                counter += 1
            comp = components[key]
            comp.asil = _highest_asil([comp.asil, item.asil])
            comp.allocated_swrs.append(item.id)
            cybersec_domains.add(domain)
            links.append(AllocationLink(
                swrs_id=item.id,
                component_id=comp.id,
                component_name=comp.name,
                rationale=(
                    f"Cybersecurity implementation requirement allocated to the "
                    f"cross-cutting SecManager component per ISO/SAE 21434 Clause 10 "
                    f"(WP-10-03: security implementation)."
                ),
            ))

        else:  # DERIV_FUNCTIONAL
            key = f"app::{domain}"
            if key not in components:
                comp_name, desc_suffix = _DOMAIN_MAP.get(
                    domain, (f"{domain}Mgr", f"{domain} function management")
                )
                components[key] = SwComponent(
                    id=f"COMP-{project_key}-{counter:04d}",
                    name=comp_name,
                    layer="application",
                    description=f"Application component responsible for {desc_suffix}.",
                    asil=item.asil,
                    cybersecurity_relevant=item.cybersecurity_relevant,
                )
                counter += 1
            comp = components[key]
            comp.asil = _highest_asil([comp.asil, item.asil])
            if item.cybersecurity_relevant:
                comp.cybersecurity_relevant = True
            comp.allocated_swrs.append(item.id)
            links.append(AllocationLink(
                swrs_id=item.id,
                component_id=comp.id,
                component_name=comp.name,
                rationale=(
                    f"Functional requirement for the {domain} domain allocated to the "
                    f"{comp.name} application component."
                ),
            ))

    # --- Phase 2: resolve cross-cutting relationships ---
    if "__safety__" in components:
        saf = components["__safety__"]
        for domain in sorted(safety_domains):
            app_key = f"app::{domain}"
            if app_key in components:
                app_name = components[app_key].name
                if app_name not in saf.monitors:
                    saf.monitors.append(app_name)

    if "__security__" in components:
        sec = components["__security__"]
        for domain in sorted(cybersec_domains):
            app_key = f"app::{domain}"
            if app_key in components:
                app_name = components[app_key].name
                if app_name not in sec.secures:
                    sec.secures.append(app_name)

    return list(components.values()), links


def load_swrs_from_json(path: str) -> tuple[dict, list[SwRSItem]]:
    """Parse a swrs_output.json file back into SwRSItem objects."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    metadata = raw.get("metadata", {})
    items: list[SwRSItem] = []
    for r in raw.get("requirements", []):
        items.append(SwRSItem(
            id=r["id"],
            title=r["title"],
            text=r["text"],
            type=r["type"],
            asil=ASIL(r["asil"]),
            cybersecurity_relevant=r["cybersecurity_relevant"],
            verification_method=VerificationMethod(r["verification_method"]),
            derived_from=r["derived_from"],
            rationale=r.get("rationale", ""),
            status=r.get("status", "draft"),
            tags=r.get("tags", []),
            derivation_type=r.get("derivation_type", "derives_functional"),
        ))
    return metadata, items
