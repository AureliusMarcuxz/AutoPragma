"""
SWE.3 Software Detailed Design engine.

Decomposes each SW component (from SWE.2) into SW units with defined
interfaces and responsibilities.

Decomposition rules:
  - application layer → Controller unit (state machine / orchestrator)
                       + Handler unit (signal I/O / data processing)
  - safety layer      → FaultDetector unit (monitoring / evaluation)
                       + SafeReactionExecutor unit (DTC / FIM / safe-state)
  - security layer    → CryptoProvider unit (Csm wrapper / key ops)
                       + AuditLogger unit (HMAC-chained NvM audit trail)

Each unit inherits ASIL and cybersecurity_relevant from its parent
component and receives allocation of the component's SwRS items
split proportionally between units.
"""

from swe1.models import ASIL
from swe2.models import SwComponent

from .models import SwUnit, UnitInterface, UnitLink, UnitOperation

# ── Operation builders ────────────────────────────────────────────────────────

def _op(name: str, description: str, params: list[str], ret: str) -> UnitOperation:
    return UnitOperation(name=name, description=description,
                         parameters=params, return_type=ret)


# ── Application layer units ───────────────────────────────────────────────────

def _app_controller(comp: SwComponent, uid: str, swrs_half: list[str]) -> SwUnit:
    cname = comp.name
    return SwUnit(
        id=uid,
        name=f"{cname}Controller",
        component_id=comp.id,
        component_name=comp.name,
        layer="application",
        asil=comp.asil,
        cybersecurity_relevant=comp.cybersecurity_relevant,
        responsibility=(
            f"Orchestrates the {cname} component. Manages the component lifecycle "
            f"(init / run / shutdown), owns the main state machine, drives the "
            f"periodic main function runnable, and coordinates the Handler unit."
        ),
        interface=UnitInterface(
            provided=[
                _op("Init",         f"Initialise {cname} component resources.",
                    [], "Std_ReturnType"),
                _op("MainFunction", f"Periodic runnable: evaluate state, trigger outputs.",
                    [], "void"),
                _op("Shutdown",     f"Orderly shutdown of {cname} component.",
                    [], "void"),
                _op("GetState",     f"Return current {cname} operational state.",
                    [], f"{cname}State"),
            ],
            required=[
                f"{cname}Handler.ProcessInput",
                "RTE_Send / RTE_Write (AUTOSAR RTE R-Port)",
                "SchM_Enter / SchM_Exit (exclusive area)",
            ],
        ),
        internal_data=[
            f"currentState : {cname}State",
            "cycleCounter : uint32",
            "errorFlags   : uint16",
        ],
        allocated_swrs=swrs_half,
    )


def _app_handler(comp: SwComponent, uid: str, swrs_half: list[str]) -> SwUnit:
    cname = comp.name
    return SwUnit(
        id=uid,
        name=f"{cname}Handler",
        component_id=comp.id,
        component_name=comp.name,
        layer="application",
        asil=comp.asil,
        cybersecurity_relevant=comp.cybersecurity_relevant,
        responsibility=(
            f"Handles all signal I/O and data transformations for the {cname} "
            f"component. Reads P-Port / Sender-Receiver data via the AUTOSAR RTE, "
            f"applies range checks and scaling, and provides processed values to "
            f"the Controller unit."
        ),
        interface=UnitInterface(
            provided=[
                _op("ProcessInput",   f"Ingest and validate incoming signals for {cname}.",
                    ["raw: RawSignalType"], "boolean"),
                _op("GetProcessed",   f"Return processed / scaled output data.",
                    [], f"{cname}DataType"),
                _op("ResetBuffers",   "Clear all internal I/O buffers.",
                    [], "void"),
            ],
            required=[
                "RTE_Read / RTE_Receive (AUTOSAR RTE P-Port)",
            ],
        ),
        internal_data=[
            "inputBuffer  : RawSignalType",
            "outputBuffer : " + f"{cname}DataType",
            "validFlag    : boolean",
        ],
        allocated_swrs=swrs_half,
    )


# ── Safety layer units ────────────────────────────────────────────────────────

def _safety_detector(comp: SwComponent, uid: str, swrs_half: list[str]) -> SwUnit:
    return SwUnit(
        id=uid,
        name="FaultDetector",
        component_id=comp.id,
        component_name=comp.name,
        layer="safety",
        asil=comp.asil,
        cybersecurity_relevant=False,
        responsibility=(
            "Continuously evaluates monitored application signals against "
            "system-level safety boundaries derived from the HARA. Detects "
            "out-of-range values, signal timeouts, and logical consistency "
            "violations. Raises fault events to the SafeReactionExecutor "
            "within the Fault Detection Time Interval (FDTI)."
        ),
        interface=UnitInterface(
            provided=[
                _op("Monitor",          "Periodic monitoring runnable (maps to OS alarm).",
                    [], "void"),
                _op("EvaluateBoundary", "Check one signal against its safety boundary.",
                    ["signalId: SignalId_t", "value: uint32"], "FaultResult_t"),
                _op("ReportFault",      "Raise a fault event to the reaction unit.",
                    ["fault: FaultId_t"], "void"),
            ],
            required=[
                "RTE_Read (monitored application signal ports)",
                "SafeReactionExecutor.HandleFault",
            ],
        ),
        internal_data=[
            "faultTable      : FaultTableEntry_t[FAULT_MAX]",
            "timeoutCounters : uint32[SIGNAL_MAX]",
            "monitoringActive: boolean",
        ],
        allocated_swrs=swrs_half,
    )


def _safety_reactor(comp: SwComponent, uid: str, swrs_half: list[str]) -> SwUnit:
    return SwUnit(
        id=uid,
        name="SafeReactionExecutor",
        component_id=comp.id,
        component_name=comp.name,
        layer="safety",
        asil=comp.asil,
        cybersecurity_relevant=False,
        responsibility=(
            "Executes the defined safe reaction upon receipt of a fault event "
            "from FaultDetector. Stores a Diagnostic Trouble Code (DTC) via the "
            "AUTOSAR DEM API, sets the Function Inhibition Manager (FIM) fault "
            "flag to inhibit dependent functions, and transitions the system to "
            "safe state or degraded mode within the Fault Tolerant Time Interval "
            "(FTTI). Triggers the AUTOSAR WdgM supervised entity timeout on "
            "unrecoverable faults."
        ),
        interface=UnitInterface(
            provided=[
                _op("HandleFault",      "Receive fault event and execute reaction.",
                    ["fault: FaultId_t"], "void"),
                _op("EnterSafeState",   "Command system into safe state.",
                    [], "Std_ReturnType"),
                _op("GetReactionStatus","Return current safe-reaction execution status.",
                    [], "ReactionStatus_t"),
            ],
            required=[
                "Dem_SetEventStatus (AUTOSAR DEM)",
                "FiM_DemTriggerOnEventStatus (AUTOSAR FIM)",
                "WdgM_SetMode (AUTOSAR WdgM)",
                "RTE_Write (safe-state output ports)",
            ],
        ),
        internal_data=[
            "reactionStatus  : ReactionStatus_t",
            "ftti_deadline_ms: uint32",
            "safeStateActive : boolean",
        ],
        allocated_swrs=swrs_half,
    )


# ── Security layer units ──────────────────────────────────────────────────────

def _security_crypto(comp: SwComponent, uid: str, swrs_half: list[str]) -> SwUnit:
    return SwUnit(
        id=uid,
        name="CryptoProvider",
        component_id=comp.id,
        component_name=comp.name,
        layer="security",
        asil=comp.asil,
        cybersecurity_relevant=True,
        responsibility=(
            "Wraps the AUTOSAR Crypto Service Manager (Csm) API to provide "
            "symmetric and asymmetric cryptographic operations (encrypt, decrypt, "
            "MAC generate/verify, signature verify) using algorithms and key "
            "lengths approved in the vehicle platform cryptographic policy. "
            "Manages key provisioning and enforces key-usage-counter limits."
        ),
        interface=UnitInterface(
            provided=[
                _op("Encrypt",       "Encrypt data using the configured algorithm.",
                    ["keyId: KeyId_t", "plain: uint8*", "len: uint32",
                     "cipher: uint8*"], "Csm_ReturnType"),
                _op("Decrypt",       "Decrypt data using the configured algorithm.",
                    ["keyId: KeyId_t", "cipher: uint8*", "len: uint32",
                     "plain: uint8*"], "Csm_ReturnType"),
                _op("MacVerify",     "Verify a MAC tag over a data block.",
                    ["keyId: KeyId_t", "data: uint8*", "mac: uint8*"], "boolean"),
                _op("GetKeyStatus",  "Return current key validity and usage counter.",
                    ["keyId: KeyId_t"], "KeyStatus_t"),
            ],
            required=[
                "Csm_Encrypt / Csm_Decrypt / Csm_MacGenerate / Csm_MacVerify",
                "KeyM_GetKey (AUTOSAR Key Manager)",
            ],
        ),
        internal_data=[
            "activeKeyIds     : KeyId_t[KEY_MAX]",
            "usageCounters    : uint32[KEY_MAX]",
            "policyViolations : uint16",
        ],
        allocated_swrs=swrs_half,
    )


def _security_audit(comp: SwComponent, uid: str, swrs_half: list[str]) -> SwUnit:
    return SwUnit(
        id=uid,
        name="AuditLogger",
        component_id=comp.id,
        component_name=comp.name,
        layer="security",
        asil=comp.asil,
        cybersecurity_relevant=True,
        responsibility=(
            "Records all security-relevant events (authentication outcomes, key "
            "usage, policy decisions, cybersecurity alerts) as HMAC-chained "
            "audit-log entries persisted in the NvM SUMS partition. Maintains "
            "a monotonically increasing sequence number and verifies chain "
            "integrity on startup per ISO/SAE 21434 WP-08-06 and UNECE R156 "
            "software update audit requirements."
        ),
        interface=UnitInterface(
            provided=[
                _op("LogEvent",       "Append a security event to the audit trail.",
                    ["eventType: AuditEvent_t", "callerId: uint16",
                     "outcome: boolean"], "Std_ReturnType"),
                _op("VerifyChain",    "Verify HMAC chain integrity of the audit log.",
                    [], "boolean"),
                _op("GetEntryCount",  "Return number of stored audit entries.",
                    [], "uint32"),
            ],
            required=[
                "CryptoProvider.MacVerify (HMAC generation)",
                "NvM_WriteBlock / NvM_ReadBlock (AUTOSAR NvM)",
            ],
        ),
        internal_data=[
            "sequenceNumber : uint32",
            "lastHmac       : uint8[32]",
            "entryCount     : uint32",
            "chainBroken    : boolean",
        ],
        allocated_swrs=swrs_half,
    )


# ── Main decomposition entry point ────────────────────────────────────────────

def design_units(
    components: list[SwComponent], project_key: str
) -> tuple[list[SwUnit], list[UnitLink]]:
    units: list[SwUnit] = []
    links: list[UnitLink] = []
    counter = 1

    for comp in components:
        n = len(comp.allocated_swrs)
        mid = n // 2
        first_half  = comp.allocated_swrs[:mid or n]   # at least all if only 1
        second_half = comp.allocated_swrs[mid:] or comp.allocated_swrs

        if comp.layer == "application":
            uid_a = f"UT-{project_key}-{counter:04d}"; counter += 1
            uid_b = f"UT-{project_key}-{counter:04d}"; counter += 1
            u_ctrl    = _app_controller(comp, uid_a, first_half)
            u_handler = _app_handler(comp, uid_b, second_half)
            units += [u_ctrl, u_handler]
            links += [
                UnitLink(comp.id, uid_a, "decomposes"),
                UnitLink(comp.id, uid_b, "decomposes"),
                UnitLink(uid_a, uid_b, "depends"),
            ]

        elif comp.layer == "safety":
            uid_a = f"UT-{project_key}-{counter:04d}"; counter += 1
            uid_b = f"UT-{project_key}-{counter:04d}"; counter += 1
            u_det  = _safety_detector(comp, uid_a, first_half)
            u_react = _safety_reactor(comp, uid_b, second_half)
            units += [u_det, u_react]
            links += [
                UnitLink(comp.id, uid_a, "decomposes"),
                UnitLink(comp.id, uid_b, "decomposes"),
                UnitLink(uid_a, uid_b, "depends"),
            ]

        elif comp.layer == "security":
            uid_a = f"UT-{project_key}-{counter:04d}"; counter += 1
            uid_b = f"UT-{project_key}-{counter:04d}"; counter += 1
            u_crypto = _security_crypto(comp, uid_a, first_half)
            u_audit  = _security_audit(comp, uid_b, second_half)
            units += [u_crypto, u_audit]
            links += [
                UnitLink(comp.id, uid_a, "decomposes"),
                UnitLink(comp.id, uid_b, "decomposes"),
                UnitLink(uid_b, uid_a, "depends"),  # AuditLogger → CryptoProvider
            ]

    return units, links
