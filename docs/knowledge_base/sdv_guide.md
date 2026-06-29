# SDV Knowledge Base

Source: https://www.sdv.guide (CC BY 4.0 — Dirk Slama, Bosch/Ferdinand Steinbeis Institute et al.)
Full sitemap: https://www.sdv.guide/sitemap.md | Full corpus: https://www.sdv.guide/llms-full.txt
Query API: `GET https://www.sdv.guide/<page>.md?ask=<question>&goal=<objective>`

---

## 1. What is a Software-Defined Vehicle?

**Customer view:** Connected, personalized, ever-expanding, self-updating — a "habitat on wheels" integrated into a digital ecosystem.

**Manufacturer view:** SDVs enable vehicle experiences through advanced software; they decouple hardware and software development, use open standards, and support iterative improvement through continuous OTA updates.

**Core characteristics:**
- **Digital performance over physical specs** — industry shifting from horsepower to "gigaflops" as primary value metric
- **Always connected** — real-time navigation, remote controls, integrated services for customers; product insights and new revenue models (subscriptions, feature unlocks) for manufacturers
- **Never finished** — regular OTA updates, new on-demand features, continuous personalization throughout vehicle lifecycle (unlike traditional development that ends at production)
- **Cost optimization** — software replaces hardware functionality, reduces BOM costs, enables platform reuse across models

**Technical foundation:** hardware abstraction, APIs, containerization, DevOps practices, virtualization, continuous regulatory approval (homologation).

---

## 2. Vehicle Domains and Two-Speed Delivery

Six primary SDV domains, each with distinct ASIL vs. QM profiles:

| Domain | ASIL-rated functions | QM functions |
|---|---|---|
| AD/ADAS | Lane-keeping, adaptive cruise, parking | Traffic sign recognition (informational) |
| Motion | ABS, ESC, steering | Suspension comfort settings |
| Energy | Battery management, HV systems | Charge display |
| Body & Comfort | Airbags, seat belt tensioners | HVAC, power windows |
| Vehicle Experience | — | Personalization, navigation, entertainment |
| Infotainment | — | All functions |
| Value-Added Services | — | Subscriptions, smart home integration |

**Two-Speed Delivery Model:** QM systems enable faster iterations and agile development; ASIL systems demand rigorous validation. Separating workflows balances rapid innovation in non-safety-critical areas with stringent compliance in safety-critical domains.

---

## 3. Automotive Software Development Challenges

**Functional safety first:** "The absence of unreasonable risk caused by hazards resulting from malfunctioning electric or electronic systems." Governed by ISO 26262 / ASIL framework.

**System complexity:** Modern vehicles integrate hundreds of subsystems and ECUs communicating through specialized protocols (CAN, FlexRay, LIN, Ethernet).

**Integration difficulties:** "Integration hell" from distributed teams, legacy infrastructure, manual approval processes, insufficient CI/CD automation.

**Philosophical division:** ASIL world (V-model, safety, rigor) vs. QM world (agile, innovation, speed). Features often span both, requiring sophisticated technical and organizational bridging.

---

## 4. SDV Building Blocks

### 4.1 Service-Oriented Architecture (SOA)
Leverages vehicle hardware abstraction layers to enable agile application development. Key sub-components:
- **SOA Framework for SDVs** — modular, scalable services communicating via standardized interfaces
- **Container Runtimes** — packaging services with dependencies for environment consistency
- **Vehicle APIs** — standardized interface layer for application-hardware interaction
- **Event Chains in Vehicle SOAs** — event-driven communication patterns
- **Vehicle SOA Tech Stack** — full technology stack (POSIX, AUTOSAR Adaptive, middleware)

### 4.2 Over-the-Air (OTA) Updates
"The backbone of software-defined vehicles." Enables software enhancements, AI improvements, configuration updates, and firmware changes without physical service visits.

- Distribution via app store-like campaign management; push or driver-initiated pull
- Onboard update agents handle security checks, identify target systems, validate installation
- **Limitation:** Traditional ECU architectures with CAN/LIN cannot support comprehensive OTA; modern zonal HPC architectures are required
- **Real-world benchmark (Rivian):** ~500 new features via 30+ OTA campaigns in 2.5 years; 96% customer adoption within two weeks

### 4.3 Vehicle App Store
"The holy grail of software-defined vehicles" — in-vehicle application distribution and management ecosystem.

### 4.4 E/E Architecture
"The bridge connecting the mechanical systems of the vehicle, its power distribution network, and connectivity infrastructure with the software layers."
- Evolution from distributed ECU networks → domain-centralized → zonal high-performance computing (HPC)
- Zonal architecture is the prerequisite for full OTA capability

---

## 5. Key Standards

| Standard | Owner | Purpose | Strengths | Limitations |
|---|---|---|---|---|
| **AUTOSAR** (Classic & Adaptive) | AUTOSAR Partnership | Decouples HW/SW; standardizes automotive software architecture | Strong interoperability, proven safety for high-ASIL | Complex, limited flexibility for rapid innovation |
| **COVESA VSS** | COVESA (ex-GENIVI) | Tree-structured vehicle signal/data model; signal-to-service transformation | Open, enables SOA data access | |
| **SOAFEE** | ARM-led | Cloud-native principles in automotive; mixed-criticality service management | Bridges cloud and embedded | |
| **Eclipse SDV** | Eclipse Foundation | Open-source SDV tools; aligns AUTOSAR + COVESA + SOAFEE | Accelerates collaboration | |

---

## 6. Implementation Strategies

### 6.1 #DigitalFirst
Shift toward software-centric development as the primary design paradigm. Software decisions made before (or in parallel with) hardware decisions.

### 6.2 SDV Software Factory
Applies Toyota Production System manufacturing principles to software development.

**Three pillars:**
1. **Design Optimization** — modular, standardized software components (like "isolated containers")
2. **Process Automation** — eliminates manual handovers, reduces development cycles
3. **Continuous Improvement** — CI/CD pipelines enabling iterative refinement

**Impact:** Traditional software builds requiring 20 hours can be optimized to minutes, enabling rapid test iterations.

**Scope evolution:** Single software stack (POSIX, AUTOSAR) today → full SDV ecosystem (ADAS, infotainment, body) tomorrow.

### 6.3 Shift Left
Moving issue identification and resolution earlier in the lifecycle. Key techniques:

- **Simulation and digital prototyping** — cloud-based prototyping and immersive UX testing for early validation
- **Virtual development and testing** — virtualization (vECU, vBUS) as digital-first foundation
- **Hardware-in-the-Loop (HiL)** — bridges virtual validation and real-world verification
- **Fleet-based testing** — real-world data collection at scale
- **Continuous testing** — embedded automated testing throughout the pipeline
- **De-coupled multi-speed system evolution** — digital mockups and simulations used to test against physical components when HW lags

### 6.4 Loosely Coupled, Automated Development Pipelines
CI/CD pipelines mapped to the V-Model, automating integration of digital, E/E, and mechanical workstreams.

- **Right-side V-Model automation** — DevOps orchestrates diverse artifacts across domains
- **Multi-speed coordination** — digital (hours–months) vs. physical (longer cycles) timelines synchronized via digital mockups and simulations
- **Key principle:** De-coupling workstreams through automation and virtual validation allows continuous integration across complex vehicle systems

---

## 7. ./pulse Framework

The ./pulse framework is the practitioner enablement layer of sdv.guide. Key components:

### 7.1 LeanRM (Lean Requirements Management)
Applies Lean principles to requirements management. Addresses the problem of managing over **1 million requirements** across mechanical, electrical, and software domains in modern vehicles.

**Six key aspects:**
1. Value-Driven Requirements — prioritize business/customer value
2. Just-in-Time Requirements — continuous refinement over upfront documentation
3. Minimized Waste — eliminate unnecessary documentation and approvals
4. Iterative & Adaptive — evolve requirements based on feedback and insights
5. **Lightweight Traceability** — "use automation and lightweight tracking to ensure compliance without excessive bureaucracy"
6. Collaboration — early cross-functional engagement

**SDV tension:** Code-first approach can create traceability gaps when balancing rapid iteration with systems engineering rigor. AutoPragma directly addresses this gap.

### 7.2 LeanSE (Lean Systems Engineering)
Applies Lean principles to Systems Engineering, bridging traditional SE practices with agile development.

- SE = broader discipline; MBSE = specific approach within SE that replaces document-based processes with model-driven practices
- **Benefits:** Faster cycles aligned with iterative releases, enhanced cross-functional collaboration through shared models, automated traceability and compliance tracking, scalability across mechanical/electrical/software domains
- **BEV start-ups** (Tesla, NIO, Rivian): adopted LeanSE from inception, software-first pipelines
- **Incumbent OEMs:** gradually adopting to modernize document-heavy processes

### 7.3 Continuous Homologation (CoHo)
Integrates regulatory compliance checks throughout the development process rather than as final-stage activities.

- Works with LeanRM (requirements → regulations linkage)
- Coordinates with LeanSE (design validation against compliance standards)
- Uses **freeze points** to secure safety-critical decisions without hindering agile progress
- Employs APIs for traceability and automated compliance verification in CI/CD/CT pipelines
- Leverages Engineering Intelligence for data-driven risk identification

### 7.4 CI/CD/CT Automation
Three pillars:
- **CI** — automates integration of changes, catches conflicts early
- **CD** — automated, seamless deployment to production
- **CT** — continuous testing embedded throughout the pipeline

Capabilities: virtual validation via digital twins, modular testing of subsystems, regulatory compliance automation (CoHo), real-time metrics feedback (test coverage, defect trends).

### 7.5 Engineering Intelligence
Data-driven AI and analytics for decision-making across the development lifecycle: predictive defect detection, requirements tracing, simulation optimization.

---

## 8. Glossary (Key SDV Terms)

| Term | Definition |
|---|---|
| ASIL | Risk classification scheme in ISO 26262 (A–D + QM) |
| AUTOSAR | Standardized automotive SW architecture for ECU interoperability |
| CAN | Controller Area Network — vehicle bus for ECU communication |
| Chaos Monkey | Netflix tool for randomly disrupting services to test resilience |
| CI/CD | Practices automating code integration, testing, and deployment |
| Containerization | Packaging apps with dependencies for environment consistency |
| Continuous Homologation | Ensuring vehicle updates comply with regulatory/safety requirements throughout development |
| COVESA | Connected Vehicle Systems Alliance — develops open vehicle data standards |
| COVESA VSS | Standardized tree-structured description of vehicle data signals |
| DevOps | Combining development and operations for faster service delivery |
| Eclipse SDV | Open-source initiative for SDV tools and frameworks |
| E/E Architecture | Integrated electrical and electronic vehicle systems |
| HAL | Hardware Abstraction Layer — uniform hardware interaction interface |
| Homologation | Certifying vehicle/component compliance with regulatory standards |
| LIN | Low-cost automotive protocol for sensors and actuators |
| Loose Coupling | Design principle minimizing component dependencies for modularity |
| MBSE | Model-Based Systems Engineering — model-driven system design/validation |
| Microservices | Architectural style structuring applications as independent services |
| QM | Quality Management — ISO 26262 classification for non-safety-critical systems |
| SOA | Service-Oriented Architecture — modular functionality via standardized interfaces |
| SOAFEE | Framework for cloud-native automotive application development |
| SUSM | System managing and distributing vehicle software updates |
| Two-Speed Delivery | Development model separating rapid-update (QM) and slower-update (ASIL) systems |
| UNECE | Organization developing automotive and industrial regulations |
| V-Model | Development model emphasizing validation and verification throughout lifecycle |
| vBUS | Simulation model for testing vehicle communication networks |
| vECU | Software-based ECU simulation for development and testing |
| Virtualization | Creating virtual hardware/platforms for flexible testing |
| VHAL | Vehicle Hardware Abstraction Layer — standardized SW-HW communication |
