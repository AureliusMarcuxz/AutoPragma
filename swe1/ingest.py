import json
from pathlib import Path

from .models import ASIL, RequirementStatus, SyRSItem, VerificationMethod


def load_syrs(file_path: str) -> tuple[dict, list[SyRSItem]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SyRS input file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("metadata", {})
    items = []

    for raw in data.get("requirements", []):
        try:
            item = SyRSItem(
                id=raw["id"],
                title=raw["title"],
                text=raw["text"],
                type=raw["type"],
                status=RequirementStatus(raw.get("status", "draft")),
                asil=ASIL(raw.get("asil", "QM")),
                cybersecurity_relevant=bool(raw.get("cybersecurity_relevant", False)),
                rationale=raw.get("rationale", ""),
                verification_method=VerificationMethod(raw.get("verification_method", "test")),
                parent_id=raw.get("parent_id"),
                tags=raw.get("tags", []),
            )
            items.append(item)
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"Failed to parse requirement '{raw.get('id', '<unknown>')}': {exc}"
            ) from exc

    return metadata, items
