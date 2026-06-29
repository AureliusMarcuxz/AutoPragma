"""
SWE.3 Base Code Generator.

Generates MISRA C:2012-compliant AUTOSAR-style skeleton header (.h) and
source (.c) files from SW unit interface definitions produced by SWE.3.

Coding-standard grounding (docs/knowledge_base/):
  - Embedded C §2.1  — fixed-width types (stdint.h, no bare int/long)
  - Embedded C §15   — const-correct parameters
  - Embedded C §17   — Doxygen file/function documentation
  - Embedded C §18   — AUTOSAR MemMap section macros
  - MISRA C:2012 Dir 4.6  — typedefs indicating size and signedness
  - MISRA C:2012 Dir 4.10 — include guards (one per header)
  - MISRA C:2012 Rule 8.8 — external linkage declared once
  - MISRA C:2012 Rule 8.2 — function types in prototype form
  - MISRA C:2012 Rule 15.5 Advisory — single exit point (documented)
  - AUTOSAR MemMap pattern — {MODULE}_START/STOP_SEC_CODE
"""

from datetime import datetime, timezone

from swe1.models import ASIL
from swe3.models import SwUnit

# ── Type mapping ──────────────────────────────────────────────────────────────

_TYPE_MAP: dict[str, str] = {
    "void":           "void",
    "boolean":        "bool",
    "bool":           "bool",
    "uint8":          "uint8_t",
    "uint8_t":        "uint8_t",
    "uint16":         "uint16_t",
    "uint16_t":       "uint16_t",
    "uint32":         "uint32_t",
    "uint32_t":       "uint32_t",
    "uint64":         "uint64_t",
    "uint64_t":       "uint64_t",
    "int8":           "int8_t",
    "int8_t":         "int8_t",
    "int16":          "int16_t",
    "int16_t":        "int16_t",
    "int32":          "int32_t",
    "int32_t":        "int32_t",
    "Std_ReturnType": "Std_ReturnType",
    "float":          "float32_t",   # AUTOSAR type alias for float
    "double":         "float64_t",
}


def _map_type(raw: str) -> str:
    raw = raw.strip()
    if raw in _TYPE_MAP:
        return _TYPE_MAP[raw]
    # Heuristic: anything that looks like a signal value → uint32_t
    lower = raw.lower()
    if any(k in lower for k in ("signal", "value", "val", "data", "reading")):
        return f"uint32_t  /* {raw} */"
    if any(k in lower for k in ("state", "status", "mode", "reason", "type", "event")):
        return f"uint8_t   /* {raw} */"
    if any(k in lower for k in ("key", "id", "index", "handle")):
        return f"uint8_t   /* {raw} */"
    if any(k in lower for k in ("len", "length", "size", "count")):
        return f"uint32_t  /* {raw} */"
    if any(k in lower for k in ("token", "mac", "hash", "ptr", "buf", "buffer")):
        return f"const uint8_t *  /* {raw} */"
    # Unknown type: keep as-is but flag it
    return f"uint32_t  /* TODO: verify type — original: {raw} */"


def _map_return(raw: str) -> str:
    raw = raw.strip()
    if raw in _TYPE_MAP:
        return _TYPE_MAP[raw]
    if raw == "Std_ReturnType":
        return "Std_ReturnType"
    lower = raw.lower()
    if "void" in lower:
        return "void"
    if "bool" in lower or "boolean" in lower:
        return "bool"
    # Safe default for AUTOSAR: always return a status
    return "Std_ReturnType"


def _parse_param(param_str: str) -> tuple[str, str]:
    """Parse "name: type" → (c_name, c_type). Handles bare names too."""
    if ":" in param_str:
        name, _, type_raw = param_str.partition(":")
        return name.strip(), _map_type(type_raw)
    # No colon — treat whole string as parameter description
    return param_str.strip().replace(" ", "_"), "uint32_t  /* TODO */"


def _guard_name(unit_name: str) -> str:
    return f"{unit_name.upper()}_H"


def _module_prefix(unit_name: str) -> str:
    return unit_name.upper()


# ── Layer-specific required service stubs ─────────────────────────────────────

def _required_includes(unit: SwUnit) -> str:
    if not unit.interface.required:
        return ""
    lines = [
        "/* ── Required services (include the appropriate generated headers) ─── */",
        "/* MISRA C:2012 Dir 4.10: every header protected by include guard      */",
    ]
    for svc in unit.interface.required:
        # Guess the header from the service name
        if svc.startswith("Rte_"):
            lines.append(f'#include "Rte_{unit.component_name}.h"  /* RTE-generated — {svc} */')
        elif svc.startswith("Dem_"):
            lines.append(f'#include "Dem.h"  /* AUTOSAR DEM — {svc} */')
        elif svc.startswith("FIM") or "FIM" in svc:
            lines.append(f'#include "FIM.h"  /* AUTOSAR FIM — {svc} */')
        elif svc.startswith("Csm") or "Csm" in svc:
            lines.append(f'#include "Csm.h"  /* AUTOSAR Csm — {svc} */')
        elif svc.startswith("NvM") or "NvM" in svc:
            lines.append(f'#include "NvM.h"  /* AUTOSAR NvM — {svc} */')
        elif svc.startswith("WdgM"):
            lines.append(f'#include "WdgM.h"  /* AUTOSAR WdgM — {svc} */')
        elif svc.startswith("SchM"):
            lines.append(f'#include "SchM_{unit.component_name}.h"  /* RTE SchM — {svc} */')
        else:
            lines.append(f'/* TODO: include header for service: {svc} */')
    return "\n".join(lines)


def _layer_body_comment(unit: SwUnit, op_name: str) -> str:
    if unit.layer == "safety":
        return (
            f"    /* TODO: Implement {op_name}                                           */\n"
            f"    /* Safety layer — requirements (ISO 26262 Part 6):                    */\n"
            f"    /*   1. Detect fault within FDTI (Fault Detection Time Interval)      */\n"
            f"    /*   2. Report to DEM: Dem_SetEventStatus(FAULT_ID, TEST_FAILED)      */\n"
            f"    /*   3. Drive safe state within FTTI (Fault Tolerant Time Interval)   */\n"
            f"    /*   4. Update WdgM alive counter: WdgM_UpdateAliveCounter(SE_ID)     */"
        )
    if unit.layer == "security":
        return (
            f"    /* TODO: Implement {op_name}                                           */\n"
            f"    /* Security layer — requirements (ISO/SAE 21434):                     */\n"
            f"    /*   1. Invoke Csm_MacVerify / Csm_Encrypt for authentication         */\n"
            f"    /*   2. On PERMIT: AuditLogger NvM_WriteBlock(NVM_AUDIT_BLOCK, &log)  */\n"
            f"    /*   3. On DENY:   AuditLogger logs DENY; no key material in output   */\n"
            f"    /*   4. Return AUTH_OK or AUTH_FAILED — never silent failure           */"
        )
    return (
        f"    /* TODO: Implement {op_name}                                               */\n"
        f"    /* Application layer — implementation notes:                               */\n"
        f"    /*   1. Validate all input parameters (MISRA Dir 4.1, Dir 4.14)           */\n"
        f"    /*   2. Use Rte_Read_*/Rte_Write_* for inter-component data exchange      */\n"
        f"    /*   3. Return E_OK on success, E_NOT_OK on error (never silent failure)  */\n"
        f"    /*      MISRA Rule 17.7: caller must check return value                   */"
    )


def _internal_data_vars(unit: SwUnit) -> str:
    if not unit.internal_data:
        return ""
    lines = [
        "/* ── Internal state data ──────────────────────────────────────────────── */",
        "/* MISRA C:2012 Rule 8.9 Advisory: declare at narrowest scope possible     */",
        "/* Embedded C §6.2: initialise all variables before use                   */",
    ]
    prefix = f"{unit.name}"
    for datum in unit.internal_data:
        # Parse "name: type" or use raw as description
        if ":" in datum:
            var_name, _, var_type_raw = datum.partition(":")
            var_name = var_name.strip().replace(" ", "_")
            c_type   = _map_type(var_type_raw)
        else:
            var_name = datum.strip().replace(" ", "_")
            c_type   = "uint32_t  /* TODO: verify type */"

        init = "false" if "bool" in c_type else "0u"
        lines.append(
            f"static {c_type:<30} {prefix}_{var_name} = {init};"
        )
    return "\n".join(lines)


# ── Header file generator ─────────────────────────────────────────────────────

def _generate_header(unit: SwUnit, project_key: str, now: str) -> str:
    guard  = _guard_name(unit.name)
    prefix = unit.name
    req_ids = " ".join(unit.allocated_swrs) if unit.allocated_swrs else "—"

    lines: list[str] = [
        f"/**",
        f" * @file    {unit.name}.h",
        f" * @brief   SW Unit provided interface — {unit.name}",
        f" *",
        f" * Component:  {unit.component_name}  ({unit.layer})",
        f" * ASIL:       {unit.asil.value}",
        f" * Project:    {project_key}",
        f" * Generated:  {now}  (AutoPragma SWE.3 — DRAFT, requires engineering review)",
        f" *",
        f" * This file is a skeleton generated from the SWE.3 detailed design.",
        f" * All function bodies must be implemented and reviewed before use.",
        f" * MISRA C:2012 (AMD1) compliance is the implementation target.",
        f" *",
        f" * @req {req_ids}",
        f" */",
        f"",
        f"#ifndef {guard}",
        f"#define {guard}",
        f"/* MISRA C:2012 Dir 4.10: include guard prevents multiple inclusion */",
        f"",
        f"/* ── Standard includes ────────────────────────────────────────────────── */",
        f'#include "Std_Types.h"       /* AUTOSAR: Std_ReturnType, E_OK, E_NOT_OK  */',
        f"#include <stdint.h>          /* MISRA Dir 4.6: fixed-width types          */",
        f"#include <stdbool.h>         /* bool, true, false                         */",
        f"",
    ]

    # Provided operations
    lines += [
        f"/* ── Provided operations ──────────────────────────────────────────────── */",
        f"/* MISRA C:2012 Rule 8.2: function types in prototype form               */",
        f"/* MISRA C:2012 Rule 8.4: compatible declaration visible at definition   */",
        f"",
    ]

    for op in unit.interface.provided:
        ret_c = _map_return(op.return_type)
        params_parsed = [_parse_param(p) for p in op.parameters] if op.parameters else []

        # Build param string for prototype
        if params_parsed:
            param_parts = [f"{c_type} {c_name}" for c_name, c_type in params_parsed]
            param_str = ",\n    ".join(param_parts)
        else:
            param_str = "void"  # MISRA Rule 8.2: no empty parameter list

        # Doxygen header (Embedded C §17.2)
        lines += [
            f"/**",
            f" * @brief   {op.description}",
        ]
        for c_name, c_type in params_parsed:
            lines.append(f" * @param[in]  {c_name:<20} {c_type.split('/*')[0].strip()}")
        if ret_c != "void":
            lines.append(f" * @return  {ret_c} — E_OK on success, E_NOT_OK on error")
        lines += [
            f" * @pre     {unit.name} is initialised.",
            f" * @post    Internal state updated per specification.",
            f" * @asil    {unit.asil.value}",
            f" * @req     {req_ids}",
            f" */",
        ]

        if len(params_parsed) > 1:
            lines += [
                f"extern {ret_c} {prefix}_{op.name}(",
                f"    {param_str}",
                f");",
                f"",
            ]
        else:
            lines += [
                f"extern {ret_c} {prefix}_{op.name}({param_str});",
                f"",
            ]

    lines += [
        f"#endif /* {guard} */",
    ]

    return "\n".join(lines)


# ── Source file generator ─────────────────────────────────────────────────────

def _generate_source(unit: SwUnit, project_key: str, now: str) -> str:
    prefix      = unit.name
    mod_upper   = _module_prefix(unit.name)
    req_ids     = " ".join(unit.allocated_swrs) if unit.allocated_swrs else "—"
    req_inc_str = _required_includes(unit)
    int_data_str = _internal_data_vars(unit)

    lines: list[str] = [
        f"/**",
        f" * @file    {unit.name}.c",
        f" * @brief   SW Unit implementation stub — {unit.name}",
        f" *",
        f" * Component:  {unit.component_name}  ({unit.layer})",
        f" * ASIL:       {unit.asil.value}",
        f" * Project:    {project_key}",
        f" * Generated:  {now}  (AutoPragma SWE.3 — DRAFT, requires engineering review)",
        f" *",
        f" * MISRA C:2012 (AMD1) compliance is the implementation target.",
        f" * All rule violations require a documented deviation record.",
        f" * Complexity target: McCabe ≤ {_complexity_limit(unit.asil)} per function (ASIL: {unit.asil.value})",
        f" *",
        f" * @req {req_ids}",
        f" */",
        f"",
        f"/* ── Memory section — code ───────────────────────────────────────────── */",
        f"/* Embedded C §18: AUTOSAR MemMap section macros for linker placement    */",
        f"#define {mod_upper}_START_SEC_CODE",
        f'#include "MemMap.h"',
        f"",
        f"/* ── Own header ─────────────────────────────────────────────────────── */",
        f'#include "{unit.name}.h"',
        f"",
        f"/* ── Standard / AUTOSAR includes ────────────────────────────────────── */",
        f'#include "Std_Types.h"',
        f"#include <stdint.h>",
        f"#include <stdbool.h>",
        f"",
    ]

    if req_inc_str:
        lines += [req_inc_str, ""]

    if int_data_str:
        lines += [int_data_str, ""]

    # Initialisation flag
    lines += [
        f"static bool {prefix}_Initialised = false;",
        f"",
        f"/* ── Provided operation implementations ─────────────────────────────── */",
        f"",
    ]

    for op in unit.interface.provided:
        ret_c = _map_return(op.return_type)
        is_void = (ret_c == "void")
        params_parsed = [_parse_param(p) for p in op.parameters] if op.parameters else []

        if params_parsed:
            param_parts = [f"{c_type} {c_name}" for c_name, c_type in params_parsed]
            param_str = ",\n    ".join(param_parts)
        else:
            param_str = "void"

        # Doxygen function header
        lines += [
            f"/**",
            f" * @brief  {op.description}",
            f" * @asil   {unit.asil.value}",
            f" */",
        ]

        # Function signature
        if len(params_parsed) > 1:
            lines += [
                f"{ret_c} {prefix}_{op.name}(",
                f"    {param_str}",
                f")",
                f"{{",
            ]
        else:
            lines += [
                f"{ret_c} {prefix}_{op.name}({param_str})",
                f"{{",
            ]

        # Body
        if not is_void:
            lines.append(f"    {ret_c} retVal = E_NOT_OK;")
            lines.append(f"")

        # Input validation (MISRA Dir 4.1 / Dir 4.14)
        lines += [
            f"    /* Input validation — MISRA Dir 4.1 / Dir 4.14                       */",
            f"    if (!{prefix}_Initialised)",
            f"    {{",
            f"        /* TODO: report via Dem_SetEventStatus or Det_ReportError        */",
        ]
        if not is_void:
            lines.append(f"        return E_NOT_OK;")
        else:
            lines.append(f"        return;")
        lines += [
            f"    }}",
            f"",
        ]

        # Layer-specific body
        lines.append(_layer_body_comment(unit, f"{prefix}_{op.name}"))
        lines.append(f"")

        if not is_void:
            lines += [
                f"    retVal = E_OK;",
                f"",
                f"    return retVal;",
                f"    /* MISRA Rule 15.5 Advisory: single point of exit               */",
            ]

        lines += [
            f"}}",
            f"",
        ]

    # MemMap close
    lines += [
        f"#define {mod_upper}_STOP_SEC_CODE",
        f'#include "MemMap.h"',
    ]

    return "\n".join(lines)


def _complexity_limit(asil: ASIL) -> int:
    return {ASIL.D: 5, ASIL.C: 5, ASIL.B: 10, ASIL.A: 15, ASIL.QM: 20}[asil]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_unit_code(units: list[SwUnit], project_key: str) -> list[dict]:
    """
    Generate skeleton C header + source for each SW unit.

    Returns a list of dicts, one per unit:
        unit_name, component_name, layer, asil,
        header_filename, source_filename,
        header_content, source_content
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    result = []

    for unit in units:
        header = _generate_header(unit, project_key, now)
        source = _generate_source(unit, project_key, now)
        result.append({
            "unit_name":        unit.name,
            "component_name":   unit.component_name,
            "layer":            unit.layer,
            "asil":             unit.asil.value,
            "header_filename":  f"{unit.name}.h",
            "source_filename":  f"{unit.name}.c",
            "header_content":   header,
            "source_content":   source,
        })

    return result
