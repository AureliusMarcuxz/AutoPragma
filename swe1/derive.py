"""
Derive software requirements (SwRS) from system requirements (SyRS).

Each SyRS item produces at minimum one SwRS item. The derivation applies
boundary-qualification prefixes by requirement type and inherits ASIL,
cybersecurity classification, and verification method directly from the
parent SyRS item. AI-assisted refinement (FR-015) is a future extension
point — the `derive_text` function is the intended hook for that.
"""

from .models import ASIL, SyRSItem, SwRSItem, TraceabilityLink

_SW_PREFIX: dict[str, str] = {
    "functional":  "The software SHALL implement: ",
    "interface":   "The software interface SHALL conform to: ",
    "performance": "The software SHALL satisfy the following performance criterion: ",
    "constraint":  "The software implementation SHALL comply with the following constraint: ",
}


def derive_swrs(
    syrs_items: list[SyRSItem], project_key: str
) -> tuple[list[SwRSItem], list[TraceabilityLink]]:
    swrs_items: list[SwRSItem] = []
    links: list[TraceabilityLink] = []

    for counter, sys_item in enumerate(syrs_items, start=1):
        sw_id = f"SW-{project_key}-{counter:04d}"

        swrs_items.append(SwRSItem(
            id=sw_id,
            title=f"[SW] {sys_item.title}",
            text=derive_text(sys_item),
            type=sys_item.type,
            asil=sys_item.asil,
            cybersecurity_relevant=sys_item.cybersecurity_relevant,
            verification_method=sys_item.verification_method,
            derived_from=sys_item.id,
            rationale=(
                f"Derived from system requirement {sys_item.id}. "
                f"Original rationale: {sys_item.rationale}"
            ),
            tags=list(sys_item.tags),
        ))

        links.append(TraceabilityLink(
            source_id=sys_item.id,
            target_id=sw_id,
            link_type="derives",
        ))

    return swrs_items, links


def derive_text(sys_item: SyRSItem) -> str:
    """
    Extension point: replace this function body with an LLM call (FR-015)
    to produce refined, software-boundary-aware requirement text.
    For now applies a deterministic type-prefix transformation.
    """
    prefix = _SW_PREFIX.get(sys_item.type, "The software SHALL satisfy: ")
    return f"{prefix}{sys_item.text}"
