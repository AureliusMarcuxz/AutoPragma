# AutoPragma — Tool/System Requirements Specification

**Document ID:** AUTOPRAGMA-SRS-001  
**Revision:** 1.0  
**Status:** Draft — Pending Internal Review  
**Date:** 2026-06-28  
**Classification:** Internal — Restricted  

---

## Executive Summary

Automotive software development at Tier 1 suppliers is burdened by four structural inefficiencies: strictly linear processes that compartmentalize activities and multiply handoffs; large up-front design packages that delay feedback on design confirmation; late-stage software verification concentrated at release rather than distributed across unit and integration phases; and fragmented toolchains closed by high-cost manual effort between tools with opaque, non-diffable formats.

**AutoPragma** is a custom middleware integration hub that eliminates these inefficiencies by automating the ASPICE-aligned development workflow — not as a bolt-on compliance layer applied after the fact, but as the native orchestration backbone that connects the existing toolchain (JAMA, Enterprise Architect, Git/Bitbucket, Jenkins, Polyspace) and enforces compliance with AUTOSAR, ISO 26262, ISO/SAE 21434, and MISRA as structural properties of the pipeline itself.

The platform targets **ASPICE Capability Level 3 (Established)**, meaning it must not only manage project-level artifacts and gates but support an organization-level process asset library, process tailoring, and performance data collection across projects. Safety and cybersecurity work products remain authoritative in JAMA and Enterprise Architect; AutoPragma enforces gates and traceability against those records rather than duplicating them into a separate repository.

**Key outputs of this specification:**

- 16 functional requirements (FR-001–FR-016) covering the traceability engine, five tool connectors, gate automation, review orchestration, baseline management, process asset library, audit trail, dashboard, and AI-assisted drafting
- 7 non-functional requirements (NFR-001–NFR-007) covering auditability, data integrity, access control, performance, tool qualification, availability, and extensibility
- Interface specifications for all five integration points
- 8 identified gaps and risks with explicit human-in-the-loop gates where automation is insufficient
- A full traceability table mapping each ASPICE process area and applicable standard to requirement IDs

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)  
2. [Assumptions, Constraints, and Conflict Surfaces](#2-assumptions-constraints-and-conflict-surfaces)  
3. [ASPICE Process Mapping](#3-aspice-process-mapping)  
4. [Standards Integration Points](#4-standards-integration-points)  
5. [Functional Requirements](#5-functional-requirements)  
6. [Non-Functional Requirements](#6-non-functional-requirements)  
7. [Interface Specifications](#7-interface-specifications)  
8. [Gaps and Risks](#8-gaps-and-risks)  
9. [Traceability Table](#9-traceability-table)  

---

## 1. Purpose and Scope

### 1.1 Purpose

This document specifies the system requirements for the AutoPragma automation platform. It defines what the platform must do (functional requirements), how well it must do it (non-functional requirements), how it integrates with the existing toolchain (interface specifications), and where human judgment cannot be replaced by automation (gaps and human-in-the-loop gates).

This specification is intended to serve:

- Development teams building the AutoPragma platform
- ASPICE CL3 assessors evaluating process institutionalization
- ISO 26262 and ISO/SAE 21434 assessors evaluating tool use and safety/cybersecurity artifact traceability
- Internal auditors reviewing gate evidence and audit trails

### 1.2 In Scope

The following ASPICE process areas are primary scope for AutoPragma orchestration:

| Process Area | Description |
|---|---|
| SWE.1 | Software Requirements Analysis |
| SWE.2 | Software Architectural Design |
| SWE.3 | Software Detailed Design and Unit Construction |
| SWE.4 | Software Unit Verification |
| SWE.5 | Software Integration and Integration Test |
| SWE.6 | Software Qualification Test |
| SYS.2 | System Requirements Analysis (traceability hooks) |
| SYS.3 | System Architectural Design (traceability hooks) |
| SUP.1 | Quality Assurance |
| SUP.8 | Configuration Management |
| SUP.9 | Problem Resolution Management |
| SUP.10 | Change Request Management |
| MAN.3 | Project Management (milestone and gate visibility) |

The platform targets ASPICE CL3 (Established), which requires institutionalized standard processes, a process asset library, tailoring guidelines, and cross-project process performance data — not just managed project artifacts.

### 1.3 Out of Scope

The following are explicitly out of scope for the AutoPragma platform:

- Replacement of JAMA, Enterprise Architect, Jenkins, Git/Bitbucket, or Polyspace
- HARA (Hazard Analysis and Risk Assessment) computation or automated ASIL assignment
- FTA (Fault Tree Analysis) or FMEA (Failure Mode and Effects Analysis) analysis
- TARA (Threat Analysis and Risk Assessment) computation or automated threat modeling
- Requirements authoring (JAMA remains the authoring tool)
- Architecture modeling (Enterprise Architect remains the modeling tool)
- Build compilation or test execution (Jenkins remains the build orchestrator)
- Static code analysis (Polyspace remains the analysis tool)
- Managing safety or cybersecurity artifacts in a separate repository distinct from JAMA and EA

---

## 2. Assumptions, Constraints, and Conflict Surfaces

### 2.1 Explicit Assumptions

**A-01:** ASPICE CL3 is the target capability level for all software projects managed on this platform. Requirements for process institutionalization (process asset library, tailoring, performance data) apply organization-wide, not per-project.

**A-02:** JAMA is the authoritative upstream source for all requirements — system requirements (SyRS), software requirements (SwRS), safety requirements, and cybersecurity requirements. No requirement record is normative unless it exists in JAMA.

**A-03:** Enterprise Architect holds the authoritative architecture baselines, including AUTOSAR-relevant component modeling and ARXML exports. EA is the system of record for design traceability.

**A-04:** Polyspace is the sole MISRA C/C++ enforcement tool. No other static analysis tool contributes to MISRA gate decisions. Third-party analysis results from other tools may be ingested as informational only.

**A-05:** The platform must survive ISO 26262 Part 8 tool qualification assessment at a minimum Tool Confidence Level of TCL2. This classification must be determined early in platform development based on the failure modes the platform could introduce into the safety lifecycle.

**A-06:** Git/Bitbucket branch naming conventions encode work item references (e.g., `feature/PROJ-1234-short-description`). This convention is required for automated traceability linkage from code changes to requirements. Projects not following this convention will produce incomplete traceability and must be flagged.

**A-07:** Jenkins pipelines are the sole CI/CD execution environment. No other pipeline tool is integrated in scope v1.

**A-08:** JAMA and EA are accessible via network API from the AutoPragma middleware host. EA requires either a licensed REST API endpoint or a dedicated EA server instance accessible to the middleware.

**A-09:** The platform is developed following its own documented software development process, which itself must be consistent with ASPICE and relevant ISO 26262 Part 8 requirements for tool development.

### 2.2 Constraints

**C-01:** The platform is a custom middleware integration hub. It does not embed or host JAMA, EA, Jenkins, Polyspace, or Bitbucket.

**C-02:** Safety and cybersecurity artifacts (safety goals, ASIL assignments, safety requirements, TARA outputs) remain authoritative in JAMA and EA. AutoPragma reads these records and enforces gates against them; it does not maintain a separate safety case repository.

**C-03:** The platform must support concurrent assessments by ASPICE assessors and functional safety / cybersecurity assessors. Audit export must not require platform source code access.

**C-04:** All gate decisions must be explainable: the evidence, rule, evaluator (automated or human), and timestamp must be logged and retrievable without interrogating the platform's internal state.

### 2.3 Conflict Surfaces

The following conflicts between standards or between standards and toolchain expectations are surfaced explicitly. They are not silently resolved; resolution approach is documented and must be accepted by the organization before implementation.

**CONFLICT-01: ASPICE SUP.1 QA Record vs. ISO 26262 §8.4 Software Verification Report**

ASPICE SUP.1 requires quality assurance records demonstrating that work products conform to defined standards and that non-conformances are resolved. ISO 26262 §8.4 requires a software verification report demonstrating that verification measures have been applied and criteria met. These are overlapping but not identical evidence structures.

*Resolution approach:* AutoPragma generates a unified evidence record with fields satisfying both. An explicit cross-reference field maps to both the ASPICE work product ID and the ISO 26262 §8.4 report requirement. Assessors can filter for their relevant view. This approach must be accepted by both the ASPICE assessor and the safety assessor before the record format is frozen.

**CONFLICT-02: TARA Asset List vs. SYS.2 Security Requirements**

ISO/SAE 21434 TARA outputs (asset list, threat scenarios, risk values) inform cybersecurity goals, which in turn drive cybersecurity requirements at SYS.2. ASPICE SYS.2 treats security requirements as a subset of system requirements without distinguishing the TARA derivation chain. If TARA is updated post-baseline, the SYS.2 baseline must be revised — but ASPICE CM (SUP.8) and 21434 §9 may impose different re-baselining procedures.

*Resolution approach:* Changes to TARA-derived requirements trigger the SUP.10 change request process, which applies both the ASPICE CM and the 21434 change management procedure. The platform enforces this dual trigger but does not automatically determine which TARA changes are material enough to require SYS.2 revision — that judgment is human-gated (see G-02).

**CONFLICT-03: AUTOSAR ARXML Baseline vs. ASPICE Configuration Management**

ARXML files exported from EA represent architecture configuration items. ASPICE SUP.8 requires these to be under configuration management with baseline identification. AUTOSAR toolchains may generate or modify ARXML automatically during build, potentially creating divergence between the CM-controlled baseline and the tool-generated artifact.

*Resolution approach:* ARXML artifacts exported from EA at baseline lock are stored in the Git repository under CM control. Tool-generated ARXML modifications during build are permitted only in designated generated-file directories and must not modify the CM-controlled interface definition files. The platform detects divergence and raises a gate failure if CM-controlled ARXML differs from the EA-exported baseline.

---

## 3. ASPICE Process Mapping

This section maps each in-scope ASPICE process area to its key work products, the automation steps AutoPragma performs, and the platform capability IDs (FR-xxx) that implement those steps.

### 3.1 SWE Process Area Mapping

| Process Area | Key Work Products | Automatable Steps | Platform Capabilities |
|---|---|---|---|
| **SWE.1** Software Requirements Analysis | Software requirements specification (SwRS); bidirectional traceability to SyRS; consistency and completeness records | Sync SwRS from JAMA on change event; check completeness (no orphan requirements, no untraceable items); check ASIL/cybersecurity attribute population; trigger review gate at entry and exit; lock baseline on approval | FR-001, FR-002, FR-007, FR-008, FR-009 |
| **SWE.2** Software Architectural Design | Software architectural design (SwAD); AUTOSAR SWC definitions; ASIL decomposition records; interface definitions | Pull EA baseline on design change; ingest ARXML export; validate SWC interface consistency against SwRS; detect uncommitted design changes against locked baseline; trigger design review gate; log ASIL allocation per component | FR-001, FR-003, FR-007, FR-008 |
| **SWE.3** Software Detailed Design | Software detailed design (SwDD); unit test plan; static design verification records | Detect EA detailed design delta; link unit test plan items to SwRS and SwDD elements; trigger detailed design review gate; check test plan coverage vs. design elements | FR-001, FR-003, FR-007 |
| **SWE.4** Software Unit Verification | Unit test results; MISRA compliance report; unit verification records | On branch push: trigger Polyspace analysis via Jenkins; parse results XML; classify by MISRA category; gate PR on required-rule violations; link findings to SwRS items and code commit; log verification record | FR-001, FR-004, FR-005, FR-006, FR-007 |
| **SWE.5** Software Integration and Test | Integration test specification; integration test results; integration verification records | On integration branch merge: trigger integration test pipeline; ingest test results; check test coverage against SwAD interface list; verify all integration test items trace to SwRS; gate integration baseline promotion | FR-001, FR-004, FR-005, FR-007 |
| **SWE.6** Software Qualification Test | Qualification test specification; qualification test results; release baseline manifest | On release trigger: gate on all SWE.1–SWE.5 gates passed; generate release baseline manifest; atomically lock baseline in JAMA, EA, and Git; produce qualification test evidence record | FR-001, FR-007, FR-009, FR-013 |

### 3.2 SYS Process Area Mapping (Traceability Hooks)

| Process Area | Key Work Products | Automatable Steps | Platform Capabilities |
|---|---|---|---|
| **SYS.2** System Requirements Analysis | System requirements specification (SyRS); TARA artifact references; cybersecurity requirement linkage | Sync SyRS items from JAMA; establish traceability root from SyRS to SwRS; link TARA artifact IDs (stored in JAMA/EA) to SyRS items; alert on SyRS change that propagates to SwRS baseline | FR-001, FR-002, FR-007 |
| **SYS.3** System Architectural Design | System architectural design; ASIL allocation at system level | Pull system architecture elements from EA; propagate ASIL allocation from system to software level in traceability graph | FR-001, FR-003, FR-007 |

### 3.3 SUP and MAN Process Area Mapping

| Process Area | Key Work Products | Automatable Steps | Platform Capabilities |
|---|---|---|---|
| **SUP.1** Quality Assurance | QA records; non-conformance reports; verification that work products conform to standards | Generate unified evidence records at each gate; flag non-conformances; link QA records to work product versions; export QA summary for assessors | FR-007, FR-008, FR-012 |
| **SUP.8** Configuration Management | CM plan; baseline manifests; change records | Enforce branch naming convention; create Git tags at baseline promotion; lock JAMA baseline; record EA model version in baseline manifest; prevent retroactive modification of locked baselines | FR-009, FR-012 |
| **SUP.9** Problem Resolution | Problem reports; resolution records; impact analysis | Receive problem reports from Bitbucket or JAMA; link problem records to affected work product versions; trigger impact analysis notification; track resolution to closure | FR-012, FR-014 |
| **SUP.10** Change Request Management | Change requests; impact analyses; change records | Receive CR from JAMA; identify affected work products in traceability graph; assess which pipeline stages require re-execution; log change record; re-trigger relevant gates post-implementation | FR-002, FR-007, FR-012 |
| **MAN.3** Project Management | Project plan; milestone records; work product status | Dashboard showing work product status per process area per project; gate pass/fail history; milestone completion evidence; blocked-item escalation | FR-013, FR-014 |

### 3.4 CL3-Specific Capabilities

ASPICE CL3 (Established) requires capabilities beyond project-level process management. These are additive to the CL1/CL2 capabilities above:

| CL3 Requirement | AutoPragma Implementation | Platform Capabilities |
|---|---|---|
| Standard process definition exists and is deployed across projects | Platform hosts the process asset library (PAL): versioned standard templates, checklists, and gate definitions | FR-010 |
| Projects tailor the standard process with documented rationale | Platform records project-level tailoring decisions (which templates used, which gates modified, rationale) | FR-010 |
| Process performance data is collected and analyzed | Platform logs cycle time per gate, gate pass/fail rates, finding density (MISRA findings per KLOC), review cycle time, and baseline promotion frequency per project and across projects | FR-013, NFR-001 |
| Process improvements are fed back to the standard process | Dashboard surfaces cross-project performance trends; improvement proposals link to PAL version updates | FR-010, FR-013 |

---

## 4. Standards Integration Points

### 4.1 AUTOSAR (Classic and Adaptive)

**ASPICE intersection:** SWE.2 (software architectural design), SWE.3 (software detailed design)

**Artifact type:** ARXML files (SWC descriptions, port interfaces, composition), exported from Enterprise Architect

**What AutoPragma must do:**

1. On EA baseline event: invoke EA headless export to produce ARXML snapshot; store snapshot in Git under CM control with commit tagged to baseline ID
2. Compare current ARXML against prior baseline ARXML; generate a structured diff report identifying changed SWC interfaces, new/removed ports, and composition changes
3. Validate that ARXML interface definitions are consistent with SwRS interface requirements (cross-reference by element ID); flag mismatches as traceability gaps
4. Gate architectural design baseline lock on: zero unresolved ARXML/SwRS mismatches AND review record approved

**Human-in-the-loop:** AUTOSAR SWC behavioral correctness (timing, memory, OS configuration) is not validated by the platform — only structural consistency of interface definitions. Full AUTOSAR configuration validation requires dedicated AUTOSAR tooling (e.g., Davinci Configurator, SystemDesk); if present, results may be ingested as informational artifacts. This is out of scope for v1.

**Assumption on tooling:** EA is the AUTOSAR modeling tool; no separate AUTOSAR toolchain integration is required in v1 beyond ARXML export from EA.

### 4.2 ISO 26262 (Functional Safety)

**ASPICE intersection:** SWE.1 (SW safety requirements), SWE.2 (SafetyAD, ASIL decomposition allocation), SWE.4 and SWE.5 (safety verification measures and evidence)

**Artifact type:** Safety requirements in JAMA (tagged with ASIL level attribute); ASIL allocation in EA architecture model; safety verification records in JAMA/Jenkins

**What AutoPragma must do:**

1. **Traceability chain enforcement:** maintain and verify the chain: Safety Goal (JAMA) → SW Safety Requirements (JAMA, ASIL-tagged) → Design Elements (EA, ASIL-allocated) → Test Cases (JAMA/test management) → Test Results (Jenkins). Flag any break in this chain as a safety traceability gap.
2. **ASIL coverage reporting:** for each ASIL-tagged SwRS item, report: design element allocated, verification measures applied (unit test, integration test, code review, static analysis), and whether results exist and are approved. Present as a safety coverage matrix — not a pass/fail gate, but a visibility artifact for the safety assessor.
3. **Safety gate at SWE.4/SWE.5:** ASIL C/D items MUST have Polyspace analysis results with zero unacknowledged required-rule violations. ASIL A/B items SHOULD have Polyspace results (configurable). Gate result is logged with evidence reference.
4. **Unified evidence record (see CONFLICT-01):** generate a record that satisfies both ASPICE SUP.1 QA record and ISO 26262 §8.4 software verification report. Cross-reference field maps to both.

**Human-in-the-loop gates (mandatory — cannot be automated):**

- ASIL decomposition correctness: the platform does not validate that an ASIL decomposition is formally correct or sufficient. It verifies that decomposition records exist in JAMA/EA and are linked. A human safety assessor MUST approve ASIL decomposition before the SWE.2 baseline is locked. This gate is enforced as a mandatory human approval step.
- Safety case argument completeness: the platform does not evaluate whether the safety case argument is sufficient. It surfaces coverage data. A human safety manager MUST approve the safety case before the SWE.6 release gate passes.

### 4.3 ISO/SAE 21434 (Cybersecurity Engineering)

**ASPICE intersection:** SYS.2/SYS.3 (cybersecurity goals and TARA outputs feeding system requirements), SWE.1 (cybersecurity requirements derived from TARA)

**Artifact type:** TARA outputs (asset list, threat scenarios, risk values) stored in JAMA and/or EA; cybersecurity requirements in JAMA; vulnerability findings in JAMA or Bitbucket

**What AutoPragma must do:**

1. **TARA artifact linkage:** link TARA output artifact IDs (stored in JAMA/EA) to the SyRS/SwRS items they derive. Flag any cybersecurity-tagged SwRS item with no TARA artifact reference as a traceability gap.
2. **Cybersecurity review gate at SWE.1 entry:** before any new cybersecurity requirement is baselined, a designated cybersecurity reviewer MUST approve it. The platform enforces this as a mandatory human approval role on cybersecurity-tagged JAMA items.
3. **Vulnerability tracking:** receive vulnerability findings (from Bitbucket security scan plugins, JAMA problem reports, or manual entry); link to affected component in traceability graph; track status to closure; escalate unresolved findings past defined age threshold.
4. **Re-baselining trigger (see CONFLICT-02):** on TARA update event, identify all SwRS items linked to affected TARA outputs; create a pre-populated change request in the CR workflow; require human triage to determine materiality before forcing re-baseline.

**Human-in-the-loop gates (mandatory):**

- TARA threat analysis: the platform does not compute threat scenarios, likelihood, or risk values. These require cybersecurity engineering judgment. Platform enforces that TARA artifacts exist, are linked, and have been reviewed — not that they are correct.
- Cybersecurity goal acceptance: cybersecurity goals must be approved by a designated cybersecurity manager before driving SwRS items.

### 4.4 MISRA C/C++ (via Polyspace)

**ASPICE intersection:** SWE.4 (software unit construction and verification), SWE.5 (integration verification)

**Artifact type:** Polyspace analysis results (XML or SARIF), published as Jenkins artifacts after each build

**What AutoPragma must do:**

1. **Results ingestion:** on Jenkins build completion, retrieve the Polyspace results file from the build artifact store; parse finding records (rule ID, severity category, file, line number, finding status: new/reviewed/justified/unreviewed).
2. **Finding classification:** classify findings into MISRA C:2012 / MISRA C++ 2008 categories: Required rules (blocking), Advisory rules (non-blocking by default, configurable to blocking), Decidable vs. Undecidable violations.
3. **Gate evaluation:** block PR merge if: unreviewed Required-rule violations > 0. Platform SHOULD allow project-level configuration to also gate on Advisory-rule violations above a defined threshold.
4. **Finding–requirement linkage:** map each finding to: (a) the code file and commit via Git metadata; (b) the SwRS item linked to that component via traceability graph; (c) the PR that introduced the code. Store this linkage in the traceability graph.
5. **Trend dashboard:** display finding density (findings per KLOC) per component per build, rule category breakdown, and justified/reviewed ratio. Flag components with increasing finding density across builds.
6. **Justified finding records:** findings marked "justified" in Polyspace require an accompanying rationale record. The platform MUST store and surface this rationale for assessor review; it does not validate the rationale's adequacy — that is human-assessed.

---

## 5. Functional Requirements

Requirements use RFC 2119 language: **MUST** (mandatory), **SHOULD** (strongly recommended, deviation requires documented rationale), **MAY** (optional).

---

### FR-001 — Traceability Engine

**Priority:** MUST  
**Process Areas:** All SWE, SYS.2/SYS.3, all standards

The platform **MUST** maintain a bidirectional link graph connecting work products across all tool boundaries. The graph **MUST** support the following link types at minimum:

- SyRS item → SwRS item (JAMA to JAMA, cross-project-key linkage)
- SwRS item → SwAD element (JAMA to EA)
- SwAD element → SwDD element (EA to EA)
- SwRS item → Test Case (JAMA to JAMA or test management)
- Test Case → Test Result (test management to Jenkins)
- SwRS item → Code Component (JAMA to Bitbucket, via branch naming)
- Code Component → Polyspace Finding (Bitbucket to Polyspace results)
- SwRS item → TARA Artifact (JAMA to JAMA/EA artifact ID)
- Safety Goal → SW Safety Requirement → Design Element → Test Case (ASIL chain)

The graph **MUST** be queryable in both directions (what does this requirement trace to? what does this code component satisfy?). Broken links (missing target, deleted source item) **MUST** be surfaced as traceability gaps with severity classification.

The traceability graph **MUST** be updated within 60 seconds of a change event from any connected tool.

---

### FR-002 — JAMA Connector

**Priority:** MUST  
**Process Areas:** SWE.1, SYS.2, SUP.10

The platform **MUST** integrate with JAMA via the JAMA REST API v2. The connector **MUST**:

- Subscribe to JAMA webhook events for item creation, modification, relationship change, and baseline creation
- On event: retrieve the changed item with all attributes, relationships, and status fields
- Perform nightly full reconciliation to detect any changes missed by webhooks
- Maintain a local cache of JAMA item state to reduce API call volume during gate evaluation
- Support JAMA baseline promotion: on platform-initiated baseline lock, invoke JAMA API to create and lock a named baseline; record baseline ID in the platform's baseline manifest
- Detect and surface broken JAMA relationships (items referenced in relationships that no longer exist or have changed project keys)

The connector **MUST** handle JAMA API rate limits gracefully: queue requests, apply exponential backoff on 429 responses, and never silently drop a change event.

---

### FR-003 — Enterprise Architect Connector

**Priority:** MUST  
**Process Areas:** SWE.2, SWE.3, SYS.3

The platform **MUST** integrate with Enterprise Architect to extract architecture baselines and design artifacts. The connector **MUST**:

- Trigger EA headless export (command-line) to produce ARXML snapshots and HTML/XMI design reports on baseline promotion events
- Ingest exported ARXML and parse SWC definitions, port interfaces, and composition structures into the traceability graph
- Extract EA element IDs and their relationships (realize, trace, associate) for population of the traceability graph
- Detect uncommitted design changes: compare current EA model state (via API or export) against the last locked baseline; flag divergence as a configuration management finding
- On baseline lock: record EA project GUID, model version, and export timestamp in the baseline manifest

The connector **MUST** abstract the EA integration behind a versioned connector interface so that EA major version upgrades can be addressed by updating the connector without changing core platform logic (see NFR-007).

The connector **SHOULD** support EA REST API if a licensed endpoint is available; it **MUST** fall back to COM automation or headless export if REST API is not licensed.

---

### FR-004 — Bitbucket Connector

**Priority:** MUST  
**Process Areas:** SWE.3, SWE.4, SWE.5, SUP.8

The platform **MUST** integrate with Bitbucket Server via REST API and webhooks. The connector **MUST**:

- Register as a webhook consumer for: push events, PR opened, PR updated, PR merged, tag created
- On push/PR event: parse branch name to extract work item reference; link commit metadata (SHA, author, timestamp, changed files) to the referenced SwRS item in the traceability graph
- Post gate evaluation results back to Bitbucket as PR status checks (pass/fail with link to evidence record)
- Post automated PR comments containing: traceability coverage summary (which requirements this PR affects and their current test coverage), MISRA finding summary (new findings introduced by this PR)
- On tag creation: treat as baseline candidate; initiate baseline promotion workflow
- Flag PRs whose branch names do not conform to the naming convention as a traceability gap (non-blocking warning in v1; configurable to blocking)

---

### FR-005 — Jenkins Connector

**Priority:** MUST  
**Process Areas:** SWE.4, SWE.5, SWE.6

The platform **MUST** integrate with Jenkins via the Jenkins REST API and a shared pipeline library (Groovy). The connector **MUST**:

- Receive pipeline stage completion events from Jenkins (via REST callbacks from the shared library, not polling)
- Ingest published build artifacts: test result XML (JUnit format), code coverage reports, and Polyspace results files
- Write gate evaluation results back to Jenkins as environment variables or build parameters available to downstream stages
- Register each successfully completed pipeline run (with all artifact references) as an evidence record in the audit trail
- Expose a platform API endpoint that the Jenkins shared library calls at the start and end of each defined pipeline stage to: (a) check for blocking gate failures before the stage begins, (b) register completion artifacts after the stage ends

---

### FR-006 — Polyspace Connector

**Priority:** MUST  
**Process Areas:** SWE.4, ISO 26262, MISRA

The platform **MUST** integrate with Polyspace by ingesting Polyspace results files published by Jenkins. No direct Polyspace API integration is assumed. The connector **MUST**:

- Parse Polyspace results in XML or SARIF format; extract: rule ID, MISRA category (Required/Advisory), finding status (new/justified/unreviewed/reviewed), file path, line number, finding message
- Store findings with full metadata in the platform database; associate findings with the pipeline run, Git commit, and branch that produced them
- Evaluate gate logic: count unreviewed Required-rule violations; compare against configured threshold (default: 0 Required violations permitted)
- Provide a finding trend store: persist finding counts per component per build; compute delta (new findings introduced, findings resolved, net change) for each build
- Surface justified-finding rationale records: for each finding with status "justified," require a rationale text field before the gate passes; store rationale linked to finding ID and JAMA item ID

---

### FR-007 — Gate Automation

**Priority:** MUST  
**Process Areas:** All

The platform **MUST** implement a configurable quality gate engine. Each gate **MUST**:

- Be defined in the process asset library (FR-010) with: gate ID, process area, triggering event, evaluation criteria (one or more conditions), and gate type (automated / human-approval / mixed)
- Be evaluated at the defined trigger event; produce a gate result of PASS, FAIL, or PENDING-HUMAN
- Log the gate result with: gate ID, timestamp (UTC), triggering event reference, evaluator identity (automated system or human approver user ID), evaluation criteria used, evidence references (links to artifacts that satisfied or failed each criterion), and override record if a human overrode an automated FAIL
- Block the downstream workflow step (pipeline stage, baseline promotion, PR merge) until the gate result is PASS
- Support gate override by an authorized role (see NFR-003) with mandatory rationale; overrides are logged and surfaced in the dashboard as exceptions requiring assessor attention
- Never silently skip a gate; if a gate cannot be evaluated (connector unavailable, artifact missing), the gate result MUST be FAIL with a diagnostic message identifying the blocking condition

---

### FR-008 — Review Orchestration

**Priority:** MUST  
**Process Areas:** SWE.1–SWE.6, SUP.1, ISO 26262, ISO/SAE 21434

The platform **MUST** support structured review workflows for work product reviews. Review orchestration **MUST**:

- Generate a review checklist from the process asset library template for the relevant work product type; pre-populate checklist items with live data (e.g., traceability coverage percentage, ASIL tag, open findings count)
- Create a review record linked to the work product version being reviewed; the review record is a versioned artifact in the platform and cannot be retroactively modified after the review is closed
- Assign reviewers based on role (configurable per work product type and ASIL level; ASIL C/D reviews MUST include a designated safety reviewer)
- Track reviewer approval status; gate does not pass until all required reviewers have approved
- Allow reviewers to raise review findings; track each finding to closure before the review can be closed
- Export completed review records in a format suitable for assessor presentation (PDF or structured HTML)

---

### FR-009 — Baseline Management

**Priority:** MUST  
**Process Areas:** SUP.8, SWE.6

The platform **MUST** manage atomic baseline promotion across all connected tools. Baseline management **MUST**:

- Initiate baseline promotion only when all predecessor gates for the target process area have passed
- Perform the following atomically (or roll back all on failure): create JAMA baseline, create EA export snapshot committed to Git with baseline tag, create Git release tag, record baseline manifest
- The baseline manifest **MUST** include: baseline ID, timestamp, JAMA baseline ID and URL, EA model version and export SHA, Git commit SHA and tag, pipeline run ID that produced the artifacts, list of all work product versions included, gate evidence references
- Lock the baseline: post-lock, no modifications may be made to baseline artifacts without creating a new baseline via the change request process. The platform **MUST** enforce this lock by refusing to overwrite or delete versioned artifacts referenced by a locked baseline
- Support baseline comparison: given two baseline IDs, produce a structured diff of work product versions, traceability links, gate results, and artifact SHAs that changed between them

---

### FR-010 — Process Asset Library

**Priority:** MUST (required for CL3)  
**Process Areas:** CL3 institutionalization (all process areas)

The platform **MUST** host and manage a process asset library (PAL). The PAL **MUST**:

- Store standard process templates for each in-scope process area: review checklists, gate definitions, work product templates (test plan, review record, release note), and tailoring guidelines
- Version all PAL assets; changes to PAL assets produce new versions without deleting history; each project references a specific PAL version
- Support project-level tailoring: a project may deviate from a standard template by selecting an alternate configuration or removing a non-mandatory element; all tailoring decisions **MUST** be recorded with rationale and approved by the process owner before becoming active
- Collect and expose process performance data: for each project using a given PAL version, collect cycle time per gate, gate pass/fail rates, finding density, review cycle time, and baseline promotion frequency; aggregate across projects for process performance reporting
- Restrict PAL modification to users with the process-owner role; all modifications are logged

---

### FR-011 — Artifact Templating

**Priority:** SHOULD  
**Process Areas:** SWE.1–SWE.6, SUP.1

The platform **SHOULD** generate draft work product artifacts from PAL templates populated with live data. Templating **SHOULD**:

- Accept a work product type and project context as inputs
- Query JAMA, EA, and Jenkins for current data relevant to the template (requirement counts, coverage percentages, open findings, last gate results)
- Produce a structured draft document (Markdown or structured JSON exportable to PDF) with fields pre-populated from live data; unfilled fields clearly marked as requiring human completion
- All generated drafts **MUST** be marked as AI-generated or system-generated drafts; they are non-normative until reviewed and approved by an authorized human; the audit trail distinguishes draft state from approved state

---

### FR-012 — Audit Trail

**Priority:** MUST  
**Process Areas:** All, ISO 26262 Part 8, ASPICE assessors

The platform **MUST** maintain an immutable, append-only audit trail of all platform actions. The audit trail **MUST**:

- Record: every gate evaluation (inputs, result, evidence), every human approval or rejection, every baseline promotion or lock event, every connector sync event (source, timestamp, items changed), every gate override, every PAL modification, and every user access event involving modification or approval
- Be append-only: records cannot be modified or deleted after creation (technical enforcement, not just policy)
- Support query by: date range, user ID, work product ID, project, gate ID, and event type
- Export filtered audit trail data in a structured format (CSV or JSON) for presentation to assessors without requiring database access or platform source code review
- Retain audit records for a minimum of 10 years or as required by organizational records retention policy (whichever is longer); archival mechanism must be defined before platform deployment

---

### FR-013 — Dashboard and Reporting

**Priority:** MUST  
**Process Areas:** MAN.3, CL3, all standards

The platform **MUST** provide a real-time dashboard accessible via web browser. The dashboard **MUST** include:

- **Project status view:** for each active project, current gate pass/fail status per process area, open traceability gaps, overdue reviews, blocked items, and baseline promotion history
- **Traceability coverage view:** for a selected project and process area, percentage of requirements with full downstream trace to test results; percentage of ASIL-tagged requirements with complete safety traceability chain; gaps listed with severity
- **MISRA finding trend view:** per component and per project, finding counts per MISRA category per build, trend over time, justified finding ratio, components exceeding finding density thresholds
- **Gate history view:** list of all gate evaluations with result, evaluator, timestamp, and evidence links; exceptions (overrides) highlighted
- **CL3 process performance view:** cross-project KPIs: average cycle time per process area gate, gate first-pass rate, review cycle time, baseline frequency, finding density trend across projects and PAL versions
- **Assessor export:** one-click export of any dashboard view as a PDF or structured data file for audit presentation

The dashboard **SHOULD** support configurable alerting thresholds (e.g., alert when traceability coverage drops below 95%, alert when MISRA finding density exceeds 5 findings/KLOC).

---

### FR-014 — Notification and Escalation

**Priority:** SHOULD  
**Process Areas:** SUP.9, MAN.3

The platform **SHOULD** send configurable notifications. Notification triggers **SHOULD** include:

- Gate failure on a PR or pipeline stage (to the PR author and project lead)
- Review request assigned (to the assigned reviewer)
- Review overdue (configurable age threshold; to reviewer and project lead)
- Traceability gap detected above severity threshold
- MISRA finding density threshold exceeded for a component
- Baseline promotion blocked (to the release manager)
- Vulnerability finding open past age threshold (to the cybersecurity lead)

Notification channels **SHOULD** be configurable per project: email, Bitbucket PR comment, or webhook to a configured endpoint (e.g., Teams or Slack integration).

---

### FR-015 — AI Work Product Assistance

**Priority:** SHOULD (aligns with AutoPragma AI Maturity Level 3 — Process Step Automation)  
**Process Areas:** SWE.1, SWE.2, SWE.3

The platform **SHOULD** provide LLM-assisted drafting of work product content. AI assistance **SHOULD** support:

- Draft generation for software requirements based on system requirements and project context
- Suggested review checklist items for a work product, based on its type, ASIL level, and content
- Test case suggestion for a SwRS item, based on requirement text and ASIL level

**Mandatory constraints on AI-generated content:**

- All AI-generated content **MUST** be explicitly labeled as AI-generated draft; this label **MUST** persist until a human reviewer approves the content
- The audit trail **MUST** distinguish AI-generated content from human-authored content at the field level, not just document level
- AI-generated content **MUST NOT** be used as normative evidence in any gate evaluation until it has been reviewed and approved by a human with appropriate role
- The AI model configuration (model ID, version, system prompt) used to generate content **MUST** be logged with the draft artifact for reproducibility and qualification records

---

### FR-016 — Tool Qualification Support

**Priority:** MUST  
**Process Areas:** ISO 26262 Part 8 §8.4.6

The platform **MUST** support its own ISO 26262 Part 8 tool qualification at minimum TCL2. To support this:

- The platform's own source code **MUST** be version-controlled in Git with the same CM practices it enforces for other projects
- The platform **MUST** log its own operational behavior: startup/shutdown events, connector health checks (success/failure per tool per time period), error conditions, software version in operation at each point in time
- The platform's configuration (gate definitions, connector endpoints, PAL version in use) **MUST** be version-controlled and must not be modifiable at runtime without a logged configuration change event
- The platform development process **MUST** be documented and followed; the platform itself is subject to at minimum ASPICE SWE.1–SWE.4 work products for its own development
- Tool use documentation (purpose of use, potential errors introduced or detected, tool version) **MUST** be maintained for each project that uses the platform, in a format suitable for ISO 26262 Part 8 tool use records

---

## 6. Non-Functional Requirements

---

### NFR-001 — Auditability

The platform **MUST** make all gate decisions and artifact state changes traceable to their initiating event. Any gate result **MUST** be retrievable — including the full evidence set used to evaluate it — within 30 seconds of an audit query, without requiring database administrator access or platform source code inspection.

---

### NFR-002 — Data Integrity

The platform **MUST** use ACID-compliant storage for all traceability links, gate results, and baseline manifests. Connector failures **MUST NOT** result in silent data loss: the platform **MUST** implement at-least-once delivery semantics for inbound change events, with idempotent write operations to prevent duplicate record creation on re-delivery. All write operations to the traceability graph **MUST** be logged before acknowledgment.

---

### NFR-003 — Access Control

The platform **MUST** implement role-based access control with the following minimum roles:

| Role | Permissions |
|---|---|
| Reader | View dashboards, traceability views, audit trail (read-only) |
| Contributor | Reader permissions + create draft artifacts, submit items for review |
| Approver | Contributor permissions + approve reviews, approve gates (human-approval type) |
| Safety Approver | Approver permissions on safety-tagged items (ASIL A–D) and safety gates specifically |
| Cybersecurity Approver | Approver permissions on cybersecurity-tagged items and cybersecurity gates |
| Process Owner | Modify PAL assets (with approval workflow); view cross-project performance data |
| Admin | All permissions + user management, connector configuration, gate definition management |

Safety-relevant gate approvals (ASIL decomposition gate, safety case completeness gate) **MUST** require the Safety Approver role. Cybersecurity review gates **MUST** require the Cybersecurity Approver role. No role substitution is permitted for these gates.

All role assignments **MUST** be logged in the audit trail.

---

### NFR-004 — Performance

| Operation | Target |
|---|---|
| Traceability query (10,000 linked items, full chain) | < 3 seconds |
| Gate evaluation (automated, no external tool call) | < 60 seconds |
| Dashboard page load (project status view) | < 5 seconds |
| Audit trail export (12-month date range, single project) | < 120 seconds |
| Connector sync latency (from tool event to graph update) | < 60 seconds |

Performance targets are measured under nominal load: up to 50 concurrent users, up to 20 active projects, up to 500 pipeline events per day.

---

### NFR-005 — Tool Qualification (ISO 26262 §8.4.6)

The platform **MUST** be classified for tool confidence level before deployment on any safety-relevant project. The tool confidence level determination **MUST** be documented, considering:

- Tool impact: what errors could the platform introduce into the safety lifecycle that would not be detected? (TCL increases with higher impact)
- Tool error detection: what independent measures exist to detect platform errors? (TCL decreases with better detection coverage)

The platform development process **MUST** satisfy a software development process consistent with the determined TCL. This specification is one artifact of that process; additional artifacts (software architecture document, test specification, verification report) **MUST** be produced before the platform is deployed on projects requiring ISO 26262 compliance.

---

### NFR-006 — Availability

The platform **MUST** target 99.5% uptime during defined business hours (configurable per organization). Planned maintenance windows **MUST** be announced at minimum 48 hours in advance and scheduled outside business hours.

In the event of platform unavailability, the platform **MUST** support a degraded mode: all connected tools continue to operate normally; the platform's gate decisions are not enforced (pipelines run without gate blocking), and the platform catches up on missed events after recovery. Degraded-mode intervals **MUST** be logged and surfaced in the audit trail as exceptions.

The platform **MUST NOT** become a single point of failure that prevents code commits, JAMA updates, or Jenkins builds from proceeding during platform downtime.

---

### NFR-007 — Extensibility

The platform **MUST** define a versioned connector plugin interface. The interface specification **MUST** document: event types the connector can produce (inbound), commands the connector can receive (outbound), authentication mechanisms, and error handling contract. New tool connectors **MUST** be addable without modifying platform core logic — only a new connector module conforming to the interface is required.

The gate definition schema **MUST** be data-driven (stored in the PAL, not hard-coded in platform logic). New gate types **MUST** be addable by creating gate definitions, not by modifying platform code.

---

## 7. Interface Specifications

### 7.1 JAMA Connector Interface

| Attribute | Detail |
|---|---|
| **Protocol** | JAMA REST API v2 (HTTPS, OAuth 2.0 client credentials) |
| **Base URL** | Configurable per deployment (JAMA on-premise or cloud) |
| **Authentication** | OAuth 2.0 client credentials flow; credentials stored in platform secrets management (not in PAL or configuration files) |

**Data flowing in to AutoPragma from JAMA:**

| Data | JAMA API Endpoint | Trigger |
|---|---|---|
| Requirement items (ID, text, attributes, ASIL tag, status, project) | `GET /items/{id}`, `GET /projects/{id}/items` | Webhook event or scheduled reconciliation |
| Relationships (traceability links, derivation links) | `GET /relationships` | Webhook event or scheduled reconciliation |
| Baseline metadata (ID, name, status, items) | `GET /baselines/{id}` | Webhook event or scheduled reconciliation |
| Review records | `GET /reviews/{id}` | On review status change |

**Data flowing out from AutoPragma to JAMA:**

| Data | JAMA API Endpoint | Trigger |
|---|---|---|
| Gate result annotation on item | `PUT /items/{id}/attachments` or custom field update | Gate evaluation complete |
| Traceability links created by platform | `POST /relationships` | Traceability graph update |
| Baseline promotion request | `POST /baselines` | Baseline promotion workflow |
| Baseline lock | `PUT /baselines/{id}` | Post-promotion lock |

**Sync cadence:** Event-driven via JAMA webhook (real-time, <60s target); full reconciliation nightly at configurable time to recover missed events.

**Rate limit handling:** Apply token bucket rate limiting aligned with JAMA API rate limits; queue events during burst; log rate-limit events in audit trail.

---

### 7.2 Enterprise Architect Connector Interface

| Attribute | Detail |
|---|---|
| **Protocol (primary)** | EA REST API (if licensed EA Cloud or EA on-premise with API server enabled) |
| **Protocol (fallback)** | EA Automation COM interface (Windows host) or EA command-line headless export |
| **Authentication** | API key or OAuth per EA server configuration; COM requires local Windows session |

**Data flowing in to AutoPragma from EA:**

| Data | Method | Trigger |
|---|---|---|
| Architecture model baseline (design elements, relationships) | EA REST `GET /models/{id}/elements` or XMI export | Baseline promotion event or scheduled snapshot |
| ARXML export (SWC definitions, port interfaces) | EA headless export command; output stored in Git | Baseline promotion event |
| Design element IDs and relationship matrix | EA REST or XMI parse | On model change event (if webhook available) or nightly |

**Data flowing out from AutoPragma to EA:**

| Data | Method | Trigger |
|---|---|---|
| Review record linked to EA element | EA REST `POST /elements/{id}/notes` or tag update | Review record created |
| Baseline lock notification | EA REST (status field update) or logged as annotation | Baseline locked |

**Connector version pinning:** The connector **MUST** record the EA version it was tested against; connector major version increments on EA major version changes. The integration test suite **MUST** include EA API contract tests.

---

### 7.3 Git / Bitbucket Connector Interface

| Attribute | Detail |
|---|---|
| **Protocol** | Bitbucket Server REST API v1 (HTTPS, HTTP Bearer token or App password) |
| **Webhook events** | `repo:push`, `pullrequest:created`, `pullrequest:updated`, `pullrequest:fulfilled` (merged), `repo:refs_changed` (tag created) |

**Data flowing in to AutoPragma from Bitbucket:**

| Data | Source | Trigger |
|---|---|---|
| Push event: commit SHA, author, timestamp, branch name, changed file list | Webhook payload | On every push |
| PR event: PR ID, title, source/target branch, author, reviewers | Webhook payload | On PR open/update/merge |
| Tag event: tag name, commit SHA, tagger | Webhook payload | On tag creation |

**Branch naming convention (required for traceability):** `<type>/<JAMA-item-key>-<short-description>` (e.g., `feature/PROJ-1234-add-safety-check`). The connector extracts the JAMA item key from the branch name to link the commit to the requirement.

**Data flowing out from AutoPragma to Bitbucket:**

| Data | Bitbucket API Endpoint | Trigger |
|---|---|---|
| PR build status (gate result) | `POST /rest/build-status/1.0/commits/{commitId}` | Gate evaluation complete |
| PR comment (traceability summary, MISRA summary) | `POST /rest/api/1.0/projects/{p}/repos/{r}/pull-requests/{id}/comments` | Gate evaluation complete |

---

### 7.4 Jenkins Connector Interface

| Attribute | Detail |
|---|---|
| **Protocol** | Jenkins REST API (HTTPS, API token authentication) + shared Groovy pipeline library |
| **Integration pattern** | Shared library provides wrapper functions that call AutoPragma REST API at stage boundaries; no Jenkins plugin required |

**Data flowing in to AutoPragma from Jenkins:**

| Data | Source | Trigger |
|---|---|---|
| Pipeline stage start: job name, build number, stage name, branch | Shared library API call | Stage entry |
| Pipeline stage end: stage name, status (SUCCESS/FAILURE/ABORTED), artifact URLs | Shared library API call | Stage exit |
| Test result artifact: JUnit XML file content | AutoPragma fetches from Jenkins artifact URL | Post-stage artifact registration |
| Polyspace results artifact: XML or SARIF file content | AutoPragma fetches from Jenkins artifact URL | Post-SWE.4 stage |
| Build log excerpt (on failure): relevant failure lines | Shared library API call | On stage failure |

**Data flowing out from AutoPragma to Jenkins:**

| Data | Method | Trigger |
|---|---|---|
| Gate evaluation result (PASS/FAIL) | REST response to shared library call | Gate evaluation complete |
| Block/proceed decision | HTTP response code (200 PASS / 403 FAIL) to shared library | Gate evaluation complete |
| Artifact registration confirmation | REST response | Artifact ingested |

**Shared library interface:** AutoPragma provides a versioned Groovy shared library. Pipeline authors use `autopragma.stageBegin(stageName)` and `autopragma.stageEnd(stageName, status)` calls. The library handles authentication and error handling; platform failures return a safe default (fail-safe: FAIL, not pass).

---

### 7.5 Polyspace Connector Interface

| Attribute | Detail |
|---|---|
| **Integration pattern** | File-based: Polyspace produces results file published as Jenkins build artifact; AutoPragma fetches and parses the file. No direct Polyspace network API assumed. |
| **Results format** | Polyspace XML results export (`ResultSummary.xml`) or SARIF 2.1.0 export (if Polyspace version supports SARIF) |

**Data flowing in to AutoPragma from Polyspace (via Jenkins artifact):**

| Data | Source field | Notes |
|---|---|---|
| Rule ID | `<CheckId>` or SARIF `ruleId` | Maps to MISRA rule; platform maintains MISRA rule registry |
| Severity / Category | `<Family>` or SARIF `level` | Required / Advisory classification |
| Finding status | `<Status>` | New / Justified / Reviewed / Unreviewed |
| File path and line number | `<File>`, `<Line>` | Used for Git blame linkage to commit |
| Justification text | `<Comment>` | Stored as rationale record |
| Analysis timestamp | Build metadata | Linked to pipeline run ID |

**Gate logic:**

| Condition | Gate result |
|---|---|
| Required-rule violations with status Unreviewed = 0 | PASS |
| Required-rule violations with status Unreviewed > 0 | FAIL |
| Advisory-rule violations > configured threshold (default: no threshold) | Configurable; default non-blocking |
| Polyspace artifact absent from Jenkins build | FAIL (missing evidence; see FR-007) |

**Traceability chain:** Polyspace finding → code file/line → Git blame → commit SHA → PR → branch → JAMA item key (from branch name) → SwRS item.

---

## 8. Gaps and Risks

The following items are either limitations of full automation (human judgment is irreplaceable) or technical risks requiring mitigation. They are surfaced here rather than silently resolved.

| ID | Gap / Risk | Impact | Human Gate Required? | Mitigation |
|---|---|---|---|---|
| **G-01** | **ASIL decomposition correctness cannot be automated.** The platform can verify that ASIL decomposition records exist and are linked, but cannot verify that the decomposition is formally sufficient or mathematically correct. | If incorrect decomposition is undetected, downstream safety properties are void. | **YES — mandatory human gate.** A designated Safety Approver MUST approve ASIL decomposition before SWE.2 baseline is locked. This gate cannot be overridden without escalation. | Platform surfaces decomposition coverage and flags missing records; all evaluation stops here and waits for human approval. |
| **G-02** | **TARA threat analysis is engineering judgment.** TARA computation (threat scenarios, likelihood estimation, risk values) requires domain knowledge of vehicle attack surfaces that cannot be automated with current LLM accuracy guarantees. | If TARA is incomplete or incorrect, cybersecurity requirements are unsound. | **YES — mandatory human gate.** Cybersecurity Approver must approve TARA artifact review before cybersecurity requirements are baselined. | Platform enforces that TARA artifact references exist and are reviewed; does not evaluate correctness of the TARA content itself. |
| **G-03** | **EA COM/API interface fragility across EA versions.** The EA Automation COM interface has historically changed behavior across major EA versions, creating connector breakage on EA upgrades. | EA connector failure blocks SWE.2/SWE.3 gates on all projects. | No (technical risk). | Abstract EA integration behind a versioned connector interface (NFR-007). Maintain a dedicated EA integration test suite that runs against a pinned EA version in a CI environment. Define connector upgrade procedure for EA major version changes. |
| **G-04** | **JAMA API rate limits under heavy CI load.** During high-frequency CI runs (many PRs open simultaneously), JAMA webhook and API call volume may exceed JAMA rate limits, causing delayed traceability updates. | Traceability gaps appear transiently; gate evaluations may use stale JAMA data. | No (technical risk). | Implement local JAMA cache with change-event invalidation. Use bulk export API for baseline operations instead of item-by-item queries. Monitor rate-limit events in audit trail and alert if frequency exceeds threshold. |
| **G-05** | **Platform tool qualification effort likely underestimated.** ISO 26262 Part 8 tool qualification requires producing work products for the platform itself (requirements, architecture, test plan, verification report). This is a substantial engineering effort that may be scoped as a separate project track. | TCL determination may require platform changes before deployment on ASIL C/D projects. | No (planning risk). | Begin tool qualification activities in parallel with platform development from day 1. Produce this SRS as the first tool qualification artifact. Assign a dedicated tool qualification owner. Consider phased deployment: non-safety projects first, safety projects after qualification evidence is complete. |
| **G-06** | **CL3 process performance data requires upfront schema design.** Retrofitting KPI collection onto a deployed platform is expensive; metrics that were not instrumented at build time cannot be reconstructed from audit trail entries alone. | Process performance reporting (CL3 requirement) is incomplete if collection was deferred. | No (planning risk). | Define the KPI schema (what data, at what granularity, from what events) before the first sprint of platform development. Treat performance data collection as a first-class architectural concern, not a reporting afterthought. |
| **G-07** | **AI-generated work products (FR-015) may introduce unreviewed errors into safety-relevant artifacts.** LLM output can be plausible but incorrect; if AI-generated content is mistakenly treated as normative before human review, safety properties may be compromised. | Safety artifact integrity risk. | **YES — mandatory review gate on all AI-generated content.** AI output MUST NOT be used as gate evidence until human-approved. | Audit trail distinguishes AI-draft state from approved state at the field level. Gate evaluation logic excludes AI-draft content from evidence consideration. Label is technically enforced, not just a UI indicator. |
| **G-08** | **Overlap between ASPICE SUP.1 QA records and ISO 26262 §8.4 software verification reports creates dual evidence burden.** If the two records are maintained separately, assessors from each domain may request artifacts that the other domain's tool generated, creating friction and potential gaps. | Assessment friction; risk of inconsistent evidence. | No (architecture decision). | Implement the unified evidence record format described in CONFLICT-01. Pilot the format with both an ASPICE assessor and a safety assessor before freezing the schema. This requires explicit organizational buy-in; record the decision and the approvers in the PAL as a process governance decision. |

---

## 9. Traceability Table

This table maps each ASPICE process area and applicable standard to the requirement IDs in this specification. Use this table to verify that every process area and standard has at least one implementing requirement, and to navigate from a compliance obligation to the platform capability that addresses it.

| Process Area / Standard / CL Requirement | Requirement IDs |
|---|---|
| **SWE.1** — Software Requirements Analysis | FR-001, FR-002, FR-007, FR-008, FR-009 |
| **SWE.2** — Software Architectural Design | FR-001, FR-003, FR-007, FR-008 |
| **SWE.3** — Software Detailed Design | FR-001, FR-003, FR-007 |
| **SWE.4** — Software Unit Verification | FR-001, FR-004, FR-005, FR-006, FR-007 |
| **SWE.5** — Software Integration and Test | FR-001, FR-004, FR-005, FR-007 |
| **SWE.6** — Software Qualification Test | FR-001, FR-007, FR-009, FR-013 |
| **SYS.2** — System Requirements Analysis | FR-001, FR-002, FR-007 |
| **SYS.3** — System Architectural Design | FR-001, FR-003, FR-007 |
| **SUP.1** — Quality Assurance | FR-007, FR-008, FR-012 |
| **SUP.8** — Configuration Management | FR-009, FR-012 |
| **SUP.9** — Problem Resolution Management | FR-012, FR-014 |
| **SUP.10** — Change Request Management | FR-002, FR-007, FR-012 |
| **MAN.3** — Project Management | FR-013, FR-014 |
| **CL3** — Process institutionalization (standard process, PAL, tailoring) | FR-010, FR-013, NFR-006 |
| **CL3** — Process performance data collection | FR-010, FR-013, NFR-001 |
| **AUTOSAR** — Interface consistency, ARXML baseline | FR-003, FR-007 |
| **ISO 26262** — Functional safety traceability chain | FR-001, FR-002, FR-007, FR-008, FR-009, FR-012 |
| **ISO 26262** — Tool qualification (Part 8) | FR-016, NFR-005 |
| **ISO 26262** — Access control on safety artifacts | NFR-003 |
| **ISO 26262** — ASIL-differentiated gate behavior | FR-006, FR-007, FR-008 |
| **ISO/SAE 21434** — Cybersecurity traceability (TARA linkage) | FR-001, FR-002, FR-007 |
| **ISO/SAE 21434** — Cybersecurity review gate | FR-007, FR-008, NFR-003 |
| **ISO/SAE 21434** — Vulnerability tracking | FR-012, FR-014 |
| **MISRA C/C++ (via Polyspace)** — Finding ingestion and gate | FR-006, FR-007 |
| **MISRA C/C++ (via Polyspace)** — Finding trend and dashboard | FR-013 |
| **MISRA C/C++ (via Polyspace)** — Finding–requirement traceability | FR-001, FR-006 |

---

## Appendix A — Requirement Index

| ID | Title | Priority | Section |
|---|---|---|---|
| FR-001 | Traceability Engine | MUST | 5.1 |
| FR-002 | JAMA Connector | MUST | 5.2 |
| FR-003 | Enterprise Architect Connector | MUST | 5.3 |
| FR-004 | Bitbucket Connector | MUST | 5.4 |
| FR-005 | Jenkins Connector | MUST | 5.5 |
| FR-006 | Polyspace Connector | MUST | 5.6 |
| FR-007 | Gate Automation | MUST | 5.7 |
| FR-008 | Review Orchestration | MUST | 5.8 |
| FR-009 | Baseline Management | MUST | 5.9 |
| FR-010 | Process Asset Library | MUST | 5.10 |
| FR-011 | Artifact Templating | SHOULD | 5.11 |
| FR-012 | Audit Trail | MUST | 5.12 |
| FR-013 | Dashboard and Reporting | MUST | 5.13 |
| FR-014 | Notification and Escalation | SHOULD | 5.14 |
| FR-015 | AI Work Product Assistance | SHOULD | 5.15 |
| FR-016 | Tool Qualification Support | MUST | 5.16 |
| NFR-001 | Auditability | MUST | 6.1 |
| NFR-002 | Data Integrity | MUST | 6.2 |
| NFR-003 | Access Control | MUST | 6.3 |
| NFR-004 | Performance | MUST | 6.4 |
| NFR-005 | Tool Qualification | MUST | 6.5 |
| NFR-006 | Availability | MUST | 6.6 |
| NFR-007 | Extensibility | MUST | 6.7 |

---

## Appendix B — Glossary

| Term | Definition |
|---|---|
| ARXML | AUTOSAR XML — the file format for AUTOSAR software component descriptions |
| ASIL | Automotive Safety Integrity Level (A–D, D being highest) as defined in ISO 26262 |
| CL | Capability Level in Automotive SPICE (0–5) |
| EA | Enterprise Architect (Sparx Systems modeling tool) |
| FMEA | Failure Mode and Effects Analysis |
| FTA | Fault Tree Analysis |
| HARA | Hazard Analysis and Risk Assessment (ISO 26262) |
| JAMA | JAMA Connect — requirements management tool |
| MISRA | Motor Industry Software Reliability Association — C/C++ coding standard |
| PAL | Process Asset Library |
| PR | Pull Request |
| SwAD | Software Architectural Design (ASPICE work product) |
| SwDD | Software Detailed Design (ASPICE work product) |
| SwRS | Software Requirements Specification (ASPICE work product) |
| SyRS | System Requirements Specification (ASPICE work product) |
| TARA | Threat Analysis and Risk Assessment (ISO/SAE 21434) |
| TCL | Tool Confidence Level (ISO 26262 Part 8) |

---

*End of AutoPragma Tool/System Requirements Specification v1.0*
