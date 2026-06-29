# AUTOSAR Classic Platform Knowledge Base

Sources: AUTOSAR Classic Platform R4.4 / R23-11 specification documents, AUTOSAR methodology specification, Vector DaVinci documentation, ETAS ISOLAR documentation, Infineon TRAVEO T2G AUTOSAR MCAL product brief.

---

## 1. What is AUTOSAR Classic Platform?

**AUTOSAR (AUTomotive Open System ARchitecture)** is a global development partnership of OEMs, Tier-1 suppliers, tool vendors, and semiconductor companies that defines an open and standardized software architecture for automotive ECUs.

**Two platforms:**
| Platform | Abbreviation | Target | OS | Key Strength |
|---|---|---|---|---|
| **Classic Platform** | CP | Deeply embedded, resource-constrained ECUs | OSEK/AUTOSAR OS | Deterministic real-time, ASIL-D capable |
| **Adaptive Platform** | AP | High-compute, service-oriented ECUs | POSIX (QNX, Linux RT) | SOA, C++14, OTA-friendly |

**AUTOSAR CP** is the dominant standard for safety-critical ECUs: instrument clusters, powertrain controllers, chassis ECUs, BCMs, gateway ECUs. It defines every interface from hardware register access to application-level service calls.

**Why it exists:** Without AUTOSAR, each OEM-Tier-1 pair invented proprietary middleware, making ECU software non-portable, non-reusable, and expensive to integrate. AUTOSAR defines a common interface contract so SWCs can be reused across ECUs and programs without modification.

**Consortium releases:**
- R3.x (2007-2010): foundation; R4.0/4.1/4.2 (2010-2014): matured BSW; R4.3/4.4 (2016-2019): safety extensions
- R21-11, R22-11, R23-11, R24-11: annual releases (Foundation + CP + AP); current mainstream is R22-11 / R23-11

---

## 2. Architecture Layers

AUTOSAR CP defines a strict layered architecture. Each layer communicates only with adjacent layers through defined interfaces.

```
+-----------------------------------------------------+
|              APPLICATION LAYER                      |
|   SWC A      SWC B      SWC C      Service SWC      |
+-----------------------------------------------------+
|              RUNTIME ENVIRONMENT (RTE)              |
|  (generated per ECU -- realizes VFB at runtime)     |
+----------------+------------------------------------+
|  BSW --        |  BSW -- ECU Abstraction Layer       |
|  Services      |  (CanIf, LinIf, EthIf, IoHwAb)     |
|  Layer         +------------------------------------+
|  (OS, COM,     |  BSW -- MCAL                        |
|   NvM, DEM,    |  (CAN, LIN, ADC, FLS, GPT, WDG...) |
|   DCM, WdgM,   +------------------------------------+
|   EcuM, BswM)  |  Complex Device Drivers (CDD)       |
+----------------+------------------------------------+
|              MICROCONTROLLER (Hardware)              |
+-----------------------------------------------------+
```

### Layer Responsibilities

| Layer | Purpose | Portability |
|---|---|---|
| **Application (SWC)** | Vehicle function logic | Fully portable -- no HW dependency |
| **RTE** | Generated glue layer; routes SWC port communications | Per-ECU generated; SWC sees uniform API |
| **BSW Services** | OS, diagnostics, NvM, watchdog, mode management | Per-platform; configurable |
| **BSW ECU Abstraction** | Abstracts communication controllers, I/O hardware | Per-ECU |
| **MCAL** | Direct register access to MCU peripherals | Per-MCU; swappable without changing BSW above |
| **CDD** | Non-standard peripherals not covered by MCAL spec | ECU-specific |

---

## 3. Software Component (SWC) Model

### SWC Types

| Type | Description | Typical Use |
|---|---|---|
| **Atomic SWC** | Leaf-level SWC with runnables; the standard application component | Speed display, warning logic |
| **Composition SWC** | Container grouping multiple SWCs; no own runnables | System-level partitioning |
| **Service SWC** | Provides AUTOSAR services (NvM, WdgM, DEM access) | BSW service interface to application |
| **ECU-Abstracted SWC** | Access to ECU-specific I/O | Display backlight, button input |
| **Sensor/Actuator SWC** | Direct I/O interface between application and I/O hardware | Speed sensor reading |
| **Parameter SWC** | Holds calibration/parameter data accessible to other SWCs | ASIL-rated calibration values |

### Ports and Interfaces

Every SWC communicates through **ports** -- never through direct function calls.

| Interface Type | Mechanism | Typical Use |
|---|---|---|
| **Sender-Receiver (S/R)** | Queued or last-is-best buffer | Signal values, sensor data |
| **Client-Server (C/S)** | Synchronous or asynchronous call | Service requests |
| **Trigger** | Fire-and-forget event | Interrupt-driven events |
| **Mode-Switch** | Mode change notification | System mode management |
| **Parameter** | Read-only calibration access | Calibration constants |
| **NV Data** | Non-volatile access mapped to NvM | Persistent data |

**Port types:**
- **Required Port (R-Port):** SWC consumes data or calls a service
- **Provided Port (P-Port):** SWC produces data or provides a service

### Virtual Function Bus (VFB) and RTE
- **VFB** is the design-time abstraction: all SWC ports connected as if over a single virtual bus -- ECU location is transparent
- **RTE** is the compile-time realization: generated code routing intra-ECU communications via memory and inter-ECU via COM/PDUR/CAN stack
- Application code calls only `Rte_Read_*`, `Rte_Write_*`, `Rte_Call_*` -- never COM or CAN APIs directly

### Runnables and Triggers
Each SWC contains one or more **runnables** -- the executable units mapped to OS tasks:
- **Timing trigger:** Periodic runnable mapped to an alarm-driven task (e.g., 10 ms)
- **Data receive trigger:** Runnable activated on S/R data receipt
- **Server call:** Synchronous/asynchronous C/S runnable

---

## 4. AUTOSAR OS (OSEK-based)

### Task Model
| Type | Description | Use |
|---|---|---|
| **Basic Task** | Runs to completion; no waiting | Short cyclic runnables |
| **Extended Task** | Can wait on events; may block | Long sequences requiring synchronization |
| **ISR Category 1** | Minimal OS involvement; no task switch | Time-critical hardware ISR |
| **ISR Category 2** | Full OS involvement; can activate tasks | CAN receive ISR, timer ISR |

### Scheduling
- Static priority scheduling (fixed at compile time)
- Priority ceiling protocol for shared resource access (OSEK Resources)
- Non-preemptive task option for atomicity; full preemptive for real-time response

### Schedule Tables
Replaces alarm-based scheduling for synchronized multi-rate task activation:
- Expiry points define when tasks/events are activated
- Synchronization mode: implicit (periodic) or explicit (external sync signal)
- Critical for coordinated multi-ECU timing (AUTOSAR NM sync, CAN gateway)

### OS Applications (Memory Protection)
- Groups tasks, ISRs, and objects into an **OS Application**
- Each OS Application has its own memory region (enforced by MPU/SMPU)
- Trusted vs. non-trusted: non-trusted cannot access trusted memory
- Basis for ASIL/QM software partitioning: ASIL tasks in trusted OS Application, QM in non-trusted
- Termination: `TerminateApplication()` isolates faults without full system reset

### Timing Protection
- Execution time budget per task (catches runaway tasks)
- Time frame budget (monitors task activation rate -- catches unwanted activations)
- Inter-arrival time protection for ISRs
- Violation: OS Protection Hook with configurable response (kill task or shutdown)

---

## 5. BSW Module Reference (Key Modules)

### 5.1 Communication Services

| Module | Abbreviation | Function |
|---|---|---|
| Communication | **COM** | Packs/unpacks signals to/from PDUs; signal filtering, timeout, invalidation |
| PDU Router | **PduR** | Routes PDUs between communication modules (TP, IF, COM) |
| CAN Interface | **CanIf** | Abstraction over CAN controller MCAL; PDU dispatch |
| CAN Transport Protocol | **CanTp** | ISO 15765-2 segmentation/reassembly for UDS |
| CAN State Manager | **CanSM** | CAN network state machine (offline/online/bus-off recovery) |
| CAN Network Management | **CanNm** | AUTOSAR NM over CAN; bus sleep/wake coordination |
| LIN Interface | **LinIf** | LIN schedule table management, master/slave control |
| Ethernet Interface | **EthIf** | Ethernet controller abstraction |
| SoAd | **SoAd** | TCP/UDP socket routing for DoIP, SOME/IP |
| DoIP | **DoIP** | ISO 13400-2 diagnostics over IP |

### 5.2 Memory Services

| Module | Abbreviation | Function |
|---|---|---|
| NVRAM Manager | **NvM** | Manages read/write of NV data blocks; background write queuing |
| Flash EEPROM Emulation | **Fee** | Emulates EEPROM wear-leveling in NOR flash |
| EEPROM Abstraction | **Ea** | Wear-leveling for true EEPROM |
| Memory Interface | **MemIf** | Uniform API over Fee/Ea |

**NvM Block types:** ROM default, RAM mirror, redundant (dual storage with CRC for safety data), dataset (indexed array).

### 5.3 Diagnostics Services

| Module | Abbreviation | Function |
|---|---|---|
| Diagnostic Event Manager | **DEM** | Stores and manages DTCs; event status, debouncing, aging, displacement |
| Diagnostic Communication Manager | **DCM** | UDS (ISO 14229) and OBD (ISO 15031) protocol handler |
| Function Inhibition Manager | **FIM** | Inhibits SWC functions based on DTC presence; FFI between diagnostics and application |

**DEM event status byte bits:** TEST_FAILED, TEST_FAILED_THIS_OPERATION_CYCLE, PENDING_DTC, CONFIRMED_DTC, TEST_NOT_COMPLETED_SINCE_LAST_CLEAR, TEST_FAILED_SINCE_LAST_CLEAR, TEST_NOT_COMPLETED_THIS_OPERATION_CYCLE, WARNING_INDICATOR_REQUESTED.

**DCM sessions:** Default (0x01), Extended Diagnostic (0x03), Programming (0x02). Security levels (0x27 SecurityAccess) guard programming session.

### 5.4 System Services

| Module | Abbreviation | Function |
|---|---|---|
| ECU Manager | **EcuM** | Controls ECU startup, shutdown, sleep, and wakeup sequences |
| BSW Mode Manager | **BswM** | Rule-based mode arbitration and action lists |
| Watchdog Manager | **WdgM** | Software supervision via alive/deadline/logical supervision; controls hardware Wdg via WdgIf |
| Watchdog Interface | **WdgIf** | Uniform API over hardware watchdog MCAL drivers |
| Schedule Manager | **SchM** | BSW module scheduling; exclusive areas (interrupt locks) for BSW |
| Default Error Tracer | **Det** | Development-mode API error reporting; disabled in production |
| Crypto Service Manager | **Csm** | Uniform crypto API over hardware accelerator (CryIf -> Crypto driver) |

---

## 6. Watchdog Manager (WdgM) -- Safety-Critical Detail

### Supervision Mechanisms

| Mechanism | What it monitors | Failure detected |
|---|---|---|
| **Alive Supervision** | Task executes exactly N times per supervision cycle | Deadlock (under-execution) or runaway (over-execution) |
| **Deadline Supervision** | Checkpoint B reached within time window after Checkpoint A | Task overrun or wrong execution order |
| **Logical Supervision** | Checkpoints visited in correct sequence (graph-based) | Program flow deviation -- wrong branch taken |

### Supervised Entities (SE)
- Each SE is a named software element (typically one runnable) that reports checkpoints to WdgM
- SE global supervision status: OK, FAILED, EXPIRED, STOPPED, DEACTIVATED
- All SEs must be OK for WdgM to service the hardware watchdog

### WdgM and TRAVEO T2G MCWDT
- WdgM -> WdgIf -> Wdg MCAL driver -> TRAVEO T2G MCWDT hardware
- MCWDT windowed watchdog: WdgM must service within the lower-upper window (e.g., 50-100% of 10 ms period)
- A failing supervised entity causes WdgM to stop servicing MCWDT, triggering hardware reset

---

## 7. E2E (End-to-End) Protection Library

### Purpose
Protects S/R port communication data against: bit errors, message loss, repetition, insertion, reordering, corruption, delay. Applied at the RTE level for inter-ECU safety signal transmission (mandatory for ASIL-B signals per ISO 26262).

### E2E Profiles

| Profile | CRC | Counter | Max Data | Primary Use |
|---|---|---|---|---|
| **P01** | CRC-8 (0x1D) | 4-bit | 240 bytes | Legacy CAN 8-byte frames |
| **P02** | CRC-8 (0x2F) | 4-bit + sequence | 240 bytes | CAN; ASIL-B; preferred for HS-CAN |
| **P04** | CRC-32 (0xF4ACFB13) | 16-bit | 4096 bytes | CAN FD, FlexRay, Ethernet; ASIL-D capable |
| **P05** | CRC-32 | 16-bit | 4096 bytes | Ethernet / large data |
| **P06** | CRC-32 | 16-bit | 4096 bytes | CAN FD; zero-byte padding variant |
| **P07** | CRC-64 (0x42F0E1EBA9EA3693) | 16-bit | 4096 bytes | Ethernet; highest integrity |
| **P11** | CRC-8H2F | 4-bit | 240 bytes | CAN; alternative poly to P01 |

**Instrument cluster typical mapping:**
- **P02** -> HS-CAN 8-byte frames (vehicle speed, ABS status -- SYS-IC-CAN-003)
- **P04/P06** -> CAN FD frames (gateway-routed ASIL signals)

### E2E Receiver State Machine
States: INIT -> VALID / INVALID / NO_NEW_DATA / ERROR
- **VALID:** counter and CRC correct, no missed frames beyond MaxDeltaCounter
- **INVALID:** CRC failure or counter jump > MaxDeltaCounter
- **ERROR:** repeated INVALID -- drives signal to invalid, triggers COM signal timeout / FIM inhibition

### Key Configuration Parameters
- `MaxDeltaCounter`: maximum counter increment per cycle (tolerates missed frames)
- `MinOkStateInit`: valid frames required before leaving INIT
- `MaxErrorStateInit`: errors tolerated in INIT before ERROR state

---

## 8. Communication Stack -- CAN Full Stack

```
Application SWC
    | Rte_Write / Rte_Read
    v
  RTE (generated)
    | Com_SendSignal / Com_ReceiveSignal
    v
  COM -- signal packing/unpacking, timeout monitoring, invalidation
    | PduR_ComTransmit
    v
  PduR -- PDU routing table
    |--- CanTp (ISO 15765-2) --- for UDS/diagnostic PDUs
    |         |
    --- CanIf --- PDU dispatch to/from CAN controller
              | Can_Write / Can_MainFunction_Read
              v
          CAN (MCAL) -- register-level CAN controller
              |
           CAN bus (ISO 11898-2 physical layer)
```

**Additional stack elements:**
- **CanNm** branches off PduR for network management PDUs
- **CanSM** controls CanIf state (offline/online/bus-off) based on transceiver and error counter
- **DCM** uses CanTp for UDS request/response
- **COM signal invalidation:** Propagates INVALID status to receivers when signal timeout occurs

### CAN Bus-Off Handling (CanSM)
1. Bus-off detected (TX error counter > 255) -> CanSM enters BUS_OFF, notifies ComM
2. ComM requests network silent (stop all transmission)
3. CanSM executes L1 and L2 recovery: waits 128 x 11-bit recessive, re-enables controller
4. Configurable recovery attempt count before CanSM declares FULL_COM refused
5. Bus-off event notified to DEM -> DTC storage (SYS-IC-CAN-005)

---

## 9. Network Management (CanNm / AUTOSAR NM)

### NM States
```
Bus-Sleep -> Pre-Normal -> Normal Operation -> Ready Sleep -> Bus-Sleep
```
- **Normal Operation:** Node active, transmitting NM PDUs, voting keep-awake
- **Ready Sleep:** Node wants to sleep but waits for all nodes to vote sleep
- **Bus-Sleep:** All nodes silent; wake on CAN activity or local wake source (KL15)

### NM PDU Format
Each CanNm PDU contains:
- Source Node Identifier (sender NM ID)
- Control Bit Vector (Active/Sleep-Ready bits)
- User data (optional application payload piggybacked on NM frames)

### Key Modules
- **Nm** (generic NM interface) <-> **CanNm** (CAN-specific) <-> **ComM** (Communication Manager)
- **ComM** arbitrates network access requests from application SWCs
- **BswM** executes mode switch actions based on NM and ComM state
- **NmCoordination** coordinates sleep across multiple CAN networks (critical for gateway ECUs)

---

## 10. MCAL (Microcontroller Abstraction Layer) -- Detail

MCAL is the only layer accessing MCU hardware registers. Must be re-implemented for each MCU; all layers above are MCU-independent.

### MCAL Module Set (with TRAVEO T2G Mapping)

| Module | Function | TRAVEO T2G Peripheral |
|---|---|---|
| **ADC** | Analog-to-digital conversion | SAR ADC |
| **CAN** | CAN/CAN FD controller | CANFD controller |
| **DIO** | Digital I/O read/write | GPIO |
| **ETH** | Ethernet MAC | Ethernet controller |
| **FLS** | Flash read/write/erase | SuperFlash controller |
| **GPT** | General purpose timer | TCPWM |
| **ICU** | Input capture | TCPWM capture mode |
| **LIN** | LIN master/slave | LIN controller |
| **MCU** | Clock init, reset cause, power modes | CLK, SRSS, CPUSS |
| **OCU** | Output compare unit | TCPWM compare mode |
| **PORT** | Pin direction, drive mode | GPIO PORT/PIN |
| **PWM** | PWM output | TCPWM PWM mode |
| **SPI** | SPI master/slave | SCB (SPI mode) |
| **WDG** | Hardware watchdog service | MCWDT |
| **CRYPTO** | Crypto accelerator | CRYPTO block |

### Safety MCAL
- ASIL-B qualified MCAL for TRAVEO T2G available from Infineon and certified AUTOSAR partners
- Adds: error detection return values, production error codes to DEM, self-test APIs
- Required for ASIL-B software stack -- non-safety MCAL under ASIL-B SWCs requires FFI justification

### MCAL Configuration
Generated from ARXML ECU configuration using AUTOSAR tools (DaVinci Configurator, EB tresos, ModusToolbox AUTOSAR Configurator). Direct register access outside MCAL API is prohibited.

---

## 11. ARXML and AUTOSAR Methodology

### ARXML
**Automotive XML (ARXML)** is the AUTOSAR data exchange format -- every artefact is ARXML conforming to the AUTOSAR meta-model schema.

**Key ARXML document types:**
| Document | Content | Owner |
|---|---|---|
| **SWC Description** | Port interfaces, runnables, internal behaviour | Application team / Tier-1 |
| **System Description** | Complete topology: SWCs, ECUs, bus signals, PDUs, frames | OEM / system architect |
| **ECU Extract** | Per-ECU view of system description | Generated by toolchain |
| **ECU Configuration** | BSW module configuration parameter values | BSW integrator |
| **Implementation Description** | Maps AUTOSAR elements to generated code | Generated by tool |

### AUTOSAR Methodology Steps
1. **System Design (OEM):** Define SWC types, port interfaces, system topology, bus signals, PDU/frame mapping. Produce System Description ARXML.
2. **ECU Allocation:** Allocate SWCs to ECUs; generate ECU Extracts.
3. **BSW Configuration (Tier-1):** Configure BSW modules (COM signals, DEM events, NvM blocks, OS tasks). Produce ECU Configuration ARXML.
4. **RTE Generation:** AUTOSAR tool generates RTE source from ECU Extract + ECU Configuration.
5. **Code Integration:** SWC source + RTE + BSW + MCAL compiled and linked.

### ARXML in AutoPragma (SWE.2 Gate)
- EA exports ARXML from architectural model
- AutoPragma ingests via EA Connector (FR-003)
- Gate check: ARXML diff between baselines detects architectural changes requiring review
- Traceability: ARXML SWC port interface <-> SwRS requirement maintained via FR-001

---

## 12. Safety Extensions -- ASIL Decomposition in AUTOSAR CP

### ASIL Decomposition at BSW Level
ISO 26262 permits ASIL-D requirements decomposed into two ASIL-B elements on the same ECU, provided sufficient FFI. AUTOSAR CP supports this through:

| Mechanism | How it provides FFI |
|---|---|
| **OS Applications + MPU** | Separate OS Applications for ASIL-B(D) and QM; MPU enforces memory boundaries |
| **OS Timing Protection** | Bounds execution time and activation rate per task; prevents ASIL task starvation by QM |
| **SMPU/PPU (TRAVEO T2G)** | Hardware-enforced memory and peripheral access restriction per Protection Context |
| **E2E protection** | Detects data corruption on inter-partition S/R communication |
| **WdgM** | Detects execution supervision failure in each partition independently |

### Safe BSW
AUTOSAR defines a **Safe BSW** concept -- BSW modules used in ASIL-B contexts must themselves be developed/qualified to the corresponding ASIL level.

**Safety-critical BSW modules for instrument cluster:**
- OS, SchM, WdgM, COM (for safety signals), DEM: typically need ASIL-B qualification or documented SEooC usage
- QM BSW (NvM for odometer, DCM for UDS): do not require ASIL qualification but must not interfere with ASIL modules (enforced by OS Applications + SMPU)

### Mixed-ASIL ECU Design Pattern (Instrument Cluster)
```
+-----------------------------------------------------+
|  OS Application: ASIL-B Trusted                     |
|  Tasks: SWC_SafetyMonitor (10 ms), SWC_Telltale     |
|  BSW: OS (safety partition), WdgM, E2E Library      |
|  Memory: SMPU PC1 -- inaccessible to QM partition   |
+-----------------------------------------------------+
|  OS Application: QM Non-Trusted                     |
|  Tasks: SWC_Display, SWC_Navigation, SWC_Media      |
|  BSW: COM (QM signals), NvM, DCM                    |
|  Memory: SMPU PC2 -- no write to ASIL-B region      |
+-----------------------------------------------------+
        |                         |
   ASIL-B MCAL               QM MCAL (or shared with FFI justification)
```

---

## 13. AUTOSAR CP vs. Adaptive Platform (AP)

| Dimension | Classic Platform (CP) | Adaptive Platform (AP) |
|---|---|---|
| **OS** | OSEK / AUTOSAR OS (static, deterministic) | POSIX (QNX, Integrity, Linux RT) |
| **Language** | C (primarily) | C++14 |
| **Configuration** | Static at compile-time (ARXML -> generated code) | Dynamic at runtime (manifests, service discovery) |
| **Communication** | COM + PDU signals (static routing) | SOME/IP (service-oriented, dynamic) |
| **ASIL capability** | ASIL-D (with dual-core + Safe BSW) | ASIL-B practical maximum today |
| **Memory footprint** | Low (KB-level RAM) | High (MB-level, needs MMU) |
| **OTA** | Possible but constrained | Native (rolling updates) |
| **Primary use** | Powertrain, chassis, BCM, cluster, gateway | ADAS compute, gateway, IVI, digital cockpit |

**Instrument cluster reality:** Most production clusters use AUTOSAR CP for the safety-critical telltale and speed display functions, combined with a high-compute SoC (Renesas R-Car, NXP i.MX 8, Qualcomm SA) running Linux or Android for the graphical HMI layer.

---

## 14. Key AUTOSAR Tools Ecosystem

| Tool | Vendor | Function |
|---|---|---|
| **DaVinci Developer** | Vector | SWC design, port interface definition, system description, ARXML authoring |
| **DaVinci Configurator Pro** | Vector | BSW module configuration, RTE generation, OS configuration |
| **MICROSAR** | Vector | AUTOSAR CP BSW stack (OS, COM, NM, DEM, DCM, NvM, WdgM, EcuM...) |
| **ISOLAR-A** | ETAS | AUTOSAR system design and configuration |
| **ISOLAR-EVE** | ETAS | Virtual ECU simulation (vECU) for early integration test |
| **RTA-CAR** | ETAS | AUTOSAR CP BSW stack |
| **tresos Studio** | EB (Elektrobit) | BSW configuration and integration |
| **ASCET** | ETAS | Model-based SWC development |
| **TargetLink** | dSPACE | Simulink-to-AUTOSAR-SWC production code generation |
| **Embedded Coder + AUTOSAR Blockset** | MathWorks | AUTOSAR SWC generation from Simulink models |
| **SystemDesk** | dSPACE | System architecture design, ARXML authoring |

---

## 15. AutoPragma Integration Map

| AutoPragma Requirement | AUTOSAR CP Element | Relevance |
|---|---|---|
| Traceability: SwRS -> design (FR-001) | ARXML SWC port interfaces <-> SwRS items | SWE.2 traceability gate |
| EA Connector / ARXML ingestion (FR-003) | ARXML export from EA -> AutoPragma ARXML diff | SWE.2 baseline gate |
| MISRA gate via Polyspace (FR-006) | AUTOSAR C coding guidelines + MISRA C:2012 | Safety MCAL + SWC code |
| WdgM configuration review (FR-008) | WdgM supervised entities, alive periods, deadline windows | Safety review checklist |
| E2E profile traceability (FR-001) | E2E profile on S/R interface <-> safety signal SwRS | SYS-IC-CAN-003 |
| DEM event list review (FR-007) | DEM event ID <-> SyRS fault detection requirement | IC-CAN / IC-PWR DTC requirements |
| BSW tool qualification (NFR-005, FR-016) | DaVinci Configurator / MICROSAR -> TI2 tools -> TCL2/3 assessment | MCAL and RTE code generation |
| NvM block configuration review (FR-008) | NvM block type (redundant vs. standard) for safety NVM | IC-PWR-006, IC-OTA-012 |
| Baseline of ARXML configuration (FR-009) | ECU Configuration ARXML baseline in EA/CM | SWE.2 configuration management |
| ASIL decomposition verification (G-01 gap) | OS Application + SMPU/PPU FFI evidence | Human-gated review; not automatable |
