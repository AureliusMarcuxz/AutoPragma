# Infineon TRAVEO T2G MCU Knowledge Base

Sources: Infineon TRAVEO T2G datasheet family (CYT4BF/CYT4BB/CYT2B), TRAVEO T2G Body Controller Safety Manual, Infineon ModusToolbox documentation, AUTOSAR MCAL product brief, Infineon SEooC package documentation.

---

## 1. What is TRAVEO T2G?

**TRAVEO T2G (T2G = TRAVEO 2nd Generation)** is Infineon Technologies' (formerly Cypress Semiconductor) automotive-grade MCU family designed for body control, instrument cluster, gateway, and multi-domain automotive applications.

**Key differentiators vs. T1G predecessor:**
- ARM Cortex-M7 as primary application core (vs. CM4 in T1G)
- Integrated VIDEOSS display subsystem (instrument cluster-specific)
- Dual-bank flash for OTA A/B partitioning
- Richer safety mechanism set targeting ISO 26262 ASIL-B SEooC
- Integrated hardware crypto accelerator (AES/SHA/RSA/ECC/TRNG)

**Target applications by variant:**
- Instrument clusters (digital speedometer, TFT display, HMI)
- Body control modules (BCM)
- Smart junction boxes, gateway ECUs
- Domain controllers

---

## 2. Device Family and Variants

| Variant | Part Series | Cores | Flash | SRAM | Key Use Case |
|---|---|---|---|---|---|
| **Body Entry** | CYT2B | CM0+ + CM4 | Up to 2 MB | Up to 256 KB | Body control, simple gateway |
| **Body Mid** | CYT3B | CM0+ + CM4 | Up to 4 MB | Up to 512 KB | Mid-range body/cluster |
| **Body High** | CYT4BB | CM0+ + CM4 + CM7 | Up to 8 MB | Up to 1 MB | Instrument cluster, gateway |
| **Body High (Dual CM7)** | CYT4BF | CM0+ + CM4 + 2xCM7 | Up to 8 MB | Up to 1 MB | High-performance cluster, multi-display |
| **Body Ultra High** | CYT6B | CM0+ + CM4 + 2xCM7 | Up to 16 MB | Up to 2 MB | Domain controller |

**Instrument cluster primary device:** CYT4BF (dual CM7) — supports up to three display outputs and highest compute for graphics-intensive cluster HMIs.

**Common part numbers:**
- CYT4BF8CES — 8 MB Flash, 1 MB SRAM, CM0+/CM4/2xCM7, LQFP-144
- CYT4BB8CES — 8 MB Flash, 1 MB SRAM, CM0+/CM4/CM7, LQFP-144

---

## 3. CPU Architecture

### Core Configuration
| Core | Frequency | Role | Lockstep |
|---|---|---|---|
| **CM0+** | Up to 100 MHz | Supervisor/master — boots system, manages protection, fault response | No |
| **CM4** | Up to 150 MHz | Mid-level processing, AUTOSAR OS tasks | Optional lockstep with second CM4 |
| **CM7_0** | Up to 320 MHz | Primary application core | Lockstep pair with CM7_1 |
| **CM7_1** | Up to 320 MHz | Lockstep shadow of CM7_0 | Lockstep pair with CM7_0 |

**Startup sequence:** CM0+ boots first from ROM, validates flash (secure boot), configures protection units (SMPU/PPU), initializes safety mechanisms, then releases CM4 and CM7 from reset.

**TCM (Tightly Coupled Memory):** Each CM7 core has dedicated instruction TCM (ITCM) and data TCM (DTCM) for deterministic zero-wait-state access to time-critical safety code and data.

### Dual-Core Lockstep (DCLS)
- CM7_0 and CM7_1 execute identical instruction streams with a fixed pipeline delay offset
- **Compare Logic** hardware compares outputs of both cores on every clock cycle
- Mismatch → immediate FAULT unit notification → configurable reset or interrupt
- Achieves **>99% diagnostic coverage** for CPU random hardware failures per safety manual
- DCLS mode is configured during CM0+ initialization and register-locked before application starts

### Protection Context (PC)
Software partitioning mechanism — each bus transaction carries a Protection Context tag (PC0-PC7). SMPU and PPU grant or deny access based on the PC of the requesting master. Used to enforce Freedom from Interference (FFI) between QM and ASIL software partitions without hardware separation.

---

## 4. Memory Subsystem

### Flash
- **Technology:** SuperFlash (NOR Flash) — high endurance (>100K erase cycles per sector)
- **Dual-bank architecture:** Two independent flash banks (Bank A / Bank B) enabling live OTA update of inactive bank while active bank executes
- **Work Flash:** Separate high-endurance region for calibration data, NVM variables, fault logs, odometer — independent erase granularity from code flash
- **ECC:** SECDED (Single Error Correction, Double Error Detection) on all flash — hardware-transparent single-bit correction, fault notification on double-bit
- **Flash partitions (typical cluster layout):**
  - Boot ROM (internal, read-only)
  - Supervisor Flash (CM0+ code, protection configuration)
  - Primary Application Flash Bank A (CM7 ASIL-B + QM code)
  - Secondary Application Flash Bank B (OTA staging target)
  - Work Flash (calibration, NVM data, fault log, SUMS audit trail)

### SRAM
- **ECC:** SECDED protection on all SRAM banks
- **Retained SRAM:** Subset of SRAM powered in Deep Sleep / Hibernate for fast wake retention
- **SRAM scrubbing:** Required by safety manual — periodic read-write to detect and correct single-bit errors before accumulation to multi-bit
- **TCM:** Per-CM7 tightly coupled memory — not ECC-protected in all variants; safety manual specifies software-based integrity check requirements for TCM content

### Memory Map Partitioning (Safety-Relevant)
| Region | Protection | Owner PC |
|---|---|---|
| CM0+ supervisor code | PPU-locked, execute-only | PC0 (boot context) |
| ASIL-B application code | SMPU read-only for QM tasks | PC1 (ASIL context) |
| QM application code | No special restriction | PC2+ (QM context) |
| Safety variable SRAM | SMPU write-restricted to PC1 | PC1 |
| OTA staging buffer | SMPU write-restricted to OTA task PC | PC3 (OTA context) |
| Work Flash (NVM) | PPU-restricted write | PC1 (calibration), PC3 (OTA log) |

---

## 5. Safety Mechanisms (Full Set)

Reference: Infineon TRAVEO T2G Body Controller Safety Manual

### 5.1 CPU Lockstep (DCLS)
- **Fault coverage:** CPU core random hardware failures (ALU error, register corruption, instruction decode fault)
- **Diagnostic coverage claim:** >=99% (per safety manual)
- **Response:** Compare Logic mismatch → FAULT unit CPU subscriber → configurable reset
- **Configuration:** CM0+ enables DCLS during init; register-locked before application start
- **ISO 26262 SM class:** HW-SM-CPU-01 (dual-channel CPU redundancy)

### 5.2 Built-In Self-Test (BIST)
Three test types, all executed at startup before normal operation:

| BIST Type | Tests | Controller |
|---|---|---|
| **CPU BIST** | CM7 register file, ALU, pipeline logic | CPU Test Controller |
| **Memory BIST (MBIST)** | SRAM cells — March-C or equivalent algorithm | MBIST Controller |
| **Flash ECC verification** | ECC integrity of code and calibration partitions | Flash Controller |

- Startup BIST must complete before CM0+ releases CM7 from reset
- **Periodic BIST** (runtime): rotating subset of SRAM + periodic CPU register test, typically 100 ms intervals
- BIST failure → prevent application start + fault indicator + DTC in Work Flash
- **Diagnostic coverage:** MBIST achieves >=99% SRAM cell fault coverage per safety manual

### 5.3 Flash ECC
- SECDED on all code and work flash partitions
- Single-bit: hardware-corrected transparently + FAULT unit correctable-ECC notification
- Double-bit: uncorrectable → FAULT unit fault notification → safe state
- Safety manual recommendation: monitor single-bit correction counter per page; accumulation beyond threshold indicates aging flash requiring maintenance DTC

### 5.4 SRAM ECC
- SECDED on all SRAM banks
- Same single-bit/double-bit response as Flash ECC
- **Scrubbing requirement:** Periodic read-write of all safety-relevant SRAM at interval < FTTI to prevent latent multi-bit accumulation
- TCM ECC: verify per safety manual revision — some T2G variants require software CRC for TCM

### 5.5 Multi-Counter Watchdog Timer (MCWDT)
- Three 16-bit cascadable counters per MCWDT instance; multiple MCWDT instances per device
- **Windowed watchdog mode:** Service write accepted only within configured lower-upper window (e.g., 50-100% of period)
  - Early service (< lower bound) → MCWDT reset — detects runaway execution
  - Late service (> upper bound / timeout) → MCWDT reset — detects deadlock / task overrun
- **Configuration lock:** Period and window bounds register-locked after initialization via PPU
- Separate MCWDT instance per CPU cluster — CM0+ and CM7 watchdogs are independent
- **Diagnostic coverage:** >=90% DC for CPU software execution faults per safety manual

### 5.6 Clock Monitor Circuit (CMC)
- Monitors frequency of safety-relevant clock sources (ECO/IMO used as system PLL reference, CM7 core clock)
- **Reference:** WCO (Watch Crystal Oscillator, 32.768 kHz) — independent of monitored clocks
- **Detection:** Clock loss (complete stop) + frequency deviation beyond configurable threshold (typical ±10%)
- **Response:** CMC fault → FAULT unit notification → configurable reset or interrupt
- WCO must be validated at startup before use as CMC reference
- **Diagnostic coverage:** >=90% for clock-related hardware faults per safety manual

### 5.7 High Voltage Supply Supervisor (HVSS) and Brown-Out Detectors (BOD)
- Monitors internal regulated supply rails: VDDD (digital domain), VDDA (analog domain), VCCD (core voltage), VDDIO
- Configurable overvoltage and undervoltage thresholds per rail
- **BOD:** Separate Brown-Out Detector for rapid undervoltage detection with fast trip time
- Any rail exceedance → FAULT unit notification
- **Note:** HVSS monitors internal rails only; external KL30 supply monitoring is the application's responsibility via ADC or external supervisor IC

### 5.8 FAULT Collection and Control Unit (FAULT Unit)
- **Central aggregator** for all hardware fault sources:
  - CPU Compare Logic (DCLS mismatch)
  - Flash ECC (correctable + uncorrectable)
  - SRAM ECC (correctable + uncorrectable)
  - MCWDT (all counter instances)
  - CMC (frequency deviation + loss)
  - HVSS/BOD (all monitored rails)
  - SMPU/PPU access violations
  - Peripheral-specific faults (CAN bus-off, etc.)
- **Per-source fault response configuration:**
  - Reset (immediate hardware reset — for non-recoverable faults)
  - NMI/interrupt (for recoverable faults requiring software safe-state entry)
  - Ignore (informational only — safety manual restricts use)
- **Configuration lock:** FAULT unit mask and response registers protected by PPU; locked to startup Protection Context before application starts
- **Fault status registers:** Sticky fault bits — must be cleared explicitly; readable by CM0+ for root cause analysis

### 5.9 Shared Memory Protection Unit (SMPU)
- **16 protection regions** per SMPU instance; multiple instances cover different bus master sets
- Each region configures: base address, size, read/write/execute permissions per Protection Context (PC0-PC7)
- **FFI enforcement:** Safety-relevant SRAM regions configured as write-restricted to ASIL PC only
- **OTA partition protection:** Active flash bank configured as execute-only + no-write for OTA task PC
- SMPU access violation → FAULT unit notification
- **Lock:** SMPU region configuration registers protected by PPU; locked at end of CM0+ startup

### 5.10 Peripheral Protection Unit (PPU)
- Controls read/write access to peripheral configuration registers based on Protection Context
- **Safety-critical peripherals protected:** FAULT unit, MCWDT, CMC, clock configuration registers, SMPU itself
- PPU violation → FAULT unit notification
- PPU configuration itself is protected — only the startup context (PC0) can modify PPU settings

### 5.11 On-Chip Temperature Sensor
- Die junction temperature monitoring via built-in bandgap-referenced sensor
- Accessible via SAR ADC channel — software polling required
- **Rated maximum junction temperature (CYT4B family):** 125 degC
- Requires factory-calibrated trim values (stored in device eFuse) for accurate absolute reading
- Safety manual recommendation: sample at >=1 Hz; implement warning (120 degC) and shutdown (125 degC) thresholds in application

---

## 6. Display Subsystem (VIDEOSS) — Instrument Cluster Critical

### 6.1 Overview
VIDEOSS (Video Subsystem) is the integrated display controller in CYT4B/CYT6B variants, enabling instrument cluster display output without an external display controller ASIC.

**Capabilities:**
- Up to **three simultaneous independent display outputs** (CYT4BF/CYT6B)
- Hardware alpha blending of multiple graphic layers per display
- 2D graphics acceleration (rotation, scaling, color conversion)
- Pixel pipeline: fetch → transform → blend → output — no CPU involvement in final pixel output

### 6.2 Display Interfaces
| Interface | Standard | Typical Use |
|---|---|---|
| **MIPI DSI** | MIPI DSI v1.3 | TFT LCD panels, OLED displays |
| **RGB parallel** | 8/16/18/24-bit | Simpler TFT panels |
| **LVDS** | FlatLink / OpenLMDI | High-resolution remote displays |

### 6.3 Graphics Layers
- Multiple independent layers per display output (background, UI, overlay, video)
- Per-layer: source format (ARGB8888, RGB565, YUV etc.), position, size, alpha
- Hardware composer merges layers before output
- **Safety-relevant:** Telltale/warning overlay layer can be configured as highest-priority layer with CPU-write protection, ensuring safety warning symbols cannot be obscured by QM graphic content

### 6.4 Capture Unit
- Camera input capture for rear-view / surround-view display in cluster
- Supports MIPI CSI-2 input; feeds directly into VIDEOSS compositor pipeline

### 6.5 Safety Considerations for VIDEOSS
- VIDEOSS output correctness is **not** covered by CPU lockstep — the display pipeline is a separate hardware block
- Safety manual requires application-level display integrity checks (frame CRC, pixel checksum) as a software safety mechanism for ASIL-rated telltale display
- Recommended: hardware-generated test pattern at startup to verify display path before normal operation

---

## 7. Communication Peripherals

| Peripheral | Protocol | Instances (CYT4BF) | Notes |
|---|---|---|---|
| **CAN FD** | ISO 11898-1:2015 | Up to 4 | 500 kbps arb / up to 8 Mbps data; external ISO 11898-2 PHY required |
| **LIN** | ISO 17987 | Up to 8 | UART-based LIN controller |
| **Ethernet** | 10/100 Mbps (IEEE 802.3) | 1 | Some variants: TSN; requires external PHY |
| **USB** | Full-Speed (12 Mbps) | 1 | Device/host; typically used for manufacturing test |
| **SCB (SPI/I2C/UART)** | — | Multiple | Configurable serial communication blocks |
| **AUDIOSS** | I2S, TDM, PDM | — | Audio for chime/voice cluster functions |

**CAN FD safety note:** CAN error counter (warning/error-passive/bus-off per ISO 11898-1) can be routed to FAULT unit via peripheral fault subscriber. E2E protection is a software layer — not in CAN hardware.

---

## 8. Security Features

### 8.1 Hardware Crypto Accelerator
| Algorithm | Purpose |
|---|---|
| AES-128/256 (ECB, CBC, CTR, GCM, CMAC) | Symmetric encryption + SecOC MAC computation |
| SHA-1/224/256/384/512 | Hash and integrity verification |
| RSA up to 4096-bit | Asymmetric key operations |
| ECC (P-256, P-384) | ECDSA signature verify/sign for secure boot and OTA |
| TRNG | True Random Number Generator — hardware entropy for nonce/seed generation |

### 8.2 Key Storage
- **eFuse / OTP:** Root keys, anti-rollback counters, device identity — written once at manufacturing, read-only thereafter
- **Key Management Store:** On-chip storage accessible only to crypto accelerator; private keys not directly readable by CPU
- Enables secure boot key, OTA signing key, and SecOC session key derivation without key material exposure

### 8.3 Secure Boot Chain
1. ROM-resident bootloader verifies CM0+ supervisor flash signature (using OEM root key from eFuse)
2. CM0+ supervisor verifies CM7 application flash signature (using same or secondary OEM key)
3. CM7 application executes only after both verification steps pass
4. Failure at any step: refuse CPU release from reset; log to Work Flash OTP counter; minimal fault display via CM0+

### 8.4 Debug Security
- SWD/JTAG debug access protected by debug certificate mechanism
- Debug access levels: non-secure (no sensitive data access), secure (full access) — controlled by eFuse debug permission field
- Production vehicles: debug should be locked to non-secure or fully closed to prevent firmware extraction

---

## 9. Power Modes

| Mode | CM7 State | SRAM | Active Peripherals | Typical Wake Sources |
|---|---|---|---|---|
| **Active** | Running | Fully powered | All | — |
| **Sleep** | WFI | Fully powered | CM0+, peripherals | Any interrupt |
| **Deep Sleep** | Off | Retained SRAM only | CM0+, WCO, MCWDT, GPIO | GPIO, RTC, MCWDT, CAN wake |
| **Hibernate** | Off | Not retained | WCO only | GPIO (limited), external reset |
| **XRes** | Off | Not retained | None | KL30 power cycle |

**OTA-relevant:** Deep Sleep is the typical sleep state while awaiting CAN wake-up (SYS-IC-CAN-008). Retained SRAM enables fast resume without full re-initialization.

---

## 10. Software Ecosystem

### 10.1 ModusToolbox
Infineon's primary IDE and SDK for T2G development:
- Eclipse-based IDE with ARM GCC / Arm Compiler 6 support
- **PDL (Peripheral Driver Library):** Low-level register-access drivers for all T2G peripherals
- **HAL (Hardware Abstraction Layer):** Higher-level portable API
- **Configurators:** Graphical device and peripheral configuration tools generating initialization code
- **Board Support Packages (BSP):** Evaluation kit configurations

### 10.2 AUTOSAR Classic MCAL
- MCAL available for T2G from Infineon and certified AUTOSAR partners (Vector, ETAS, etc.)
- Covers: ADC, CAN, DIO, FLS (Flash), GPT, ICU, MCU, OCU, PORT, PWM, SPI, WDG
- **Safety MCAL:** ASIL-B qualified MCAL available — required for ASIL-B cluster software stacks
- Integration with AUTOSAR OS (e.g., MICROSAR OS) for task scheduling and resource management

### 10.3 Third-Party Toolchain Support
- Arm Keil MDK (uVision + Arm Compiler 6)
- IAR Embedded Workbench for Arm
- SEGGER J-Link for debug and flash programming
- Lauterbach TRACE32 for advanced trace and structural coverage measurement

---

## 11. ISO 26262 ASIL Capability

### 11.1 Device ASIL Classification
- TRAVEO T2G is documented as a **Safety Element out of Context (SEooC)** per ISO 26262 Part 10
- **Maximum achievable ASIL: ASIL-B** at system level when all required safety mechanisms are correctly configured per the safety manual
- ASIL-D applications require external redundancy (second MCU or safety companion IC)

### 11.2 Safety Mechanism Diagnostic Coverage Summary

| Safety Mechanism | Primary Metric | Coverage Claim |
|---|---|---|
| DCLS (CPU Lockstep) | SPFM (CPU faults) | >=99% DC |
| Flash ECC (SECDED) | SPFM + LFM (flash faults) | >=99% DC |
| SRAM ECC + Scrubbing | LFM (SRAM latent faults) | >=99% DC |
| MBIST at startup | LFM (SRAM faults at startup) | >=99% DC |
| MCWDT (windowed) | SPFM (SW execution faults) | >=90% DC |
| CMC | SPFM (clock faults) | >=90% DC |
| HVSS/BOD | SPFM (supply faults) | >=60% DC |
| SMPU/PPU | FFI (inter-partition corruption) | Architectural measure |

*All DC values per Infineon TRAVEO T2G Safety Manual. Must be verified against the applicable device variant and safety manual revision before safety case submission.*

### 11.3 SEooC Safety Assumptions (Integrator Must Validate)
- Supply voltage within VDDD/VDDA/VCCD rated range (→ SYS-IC-PWR-001)
- Operating temperature within rated junction temperature range (→ SYS-IC-SAF-010)
- External crystal oscillator (ECO) meets specified frequency stability and startup time
- PCB layout meets EMC and signal integrity guidelines per T2G hardware design guide
- Safety manual configuration requirements followed exactly for all safety mechanisms (→ SYS-IC-SAF-001 through SYS-IC-SAF-012)

### 11.4 What the T2G Safety Manual Does NOT Cover (Application Responsibility)
- VIDEOSS display output pixel correctness — software safety mechanism required
- CAN bus E2E protection — AUTOSAR software layer (→ SYS-IC-CAN-003)
- Application software logical correctness — ASPICE SWE.4/SWE.5
- Safe state definition and transition logic (→ SYS-IC-SAF-012)
- External KL30 supply voltage monitoring (→ SYS-IC-PWR-001, SYS-IC-PWR-012)

---

## 12. AutoPragma Integration Map

| AutoPragma Requirement | T2G Mechanism | IC-SAF / IC-OTA Reference |
|---|---|---|
| ASIL-B gate on safety software (FR-007) | DCLS + FAULT unit configuration lock | SYS-IC-SAF-001, SYS-IC-SAF-008 |
| Startup BIST evidence collection (FR-005) | BIST pass/fail status registers | SYS-IC-SAF-002 |
| MISRA/Polyspace gate on safety code (FR-006) | ASIL-B MCAL + application code in safety partition | SYS-IC-SAF-009 |
| Traceability: safety goal → SW requirement (FR-001) | SEooC safety assumptions → IC-SAF SyRS items | SYS-IC-SAF-001 through 012 |
| Tool qualification (NFR-005, FR-016) | ModusToolbox + safety MCAL require TCL classification | Applies to PDL + MCAL in safety partition |
| OTA safety partition protection (FR-007, FR-009) | SMPU/PPU configuration | SYS-IC-SAF-009, SYS-IC-OTA-009 |
| Baseline lock of safety configuration (FR-009) | PPU-locked registers after CM0+ init | SYS-IC-SAF-008 |
| Secure boot evidence for OTA (FR-012 audit trail) | Secure boot failure counter in OTP | SYS-IC-OTA-008, SYS-IC-OTA-012 |
