# MISRA C Knowledge Base

Sources: MISRA C:2012 Third Edition (with 2016 and 2020 amendments), MISRA Compliance:2020, MISRA C:2023, AUTOSAR C++14 Coding Guidelines cross-reference, Polyspace documentation, LDRA documentation, PC-lint Plus documentation, Motor Industry Software Reliability Association.

---

## 1. What is MISRA C?

**MISRA C** (Motor Industry Software Reliability Association — C) is a set of software development guidelines for the C programming language, developed by a consortium of automotive OEMs, Tier-1 suppliers, and tool vendors. The guidelines restrict the use of unsafe or ambiguous C language features to improve **portability**, **reliability**, **safety**, and **security** of embedded software.

**Practical mandate:** Not legally binding, but effectively required by:
- ISO 26262 Part 6 (references MISRA C as an established coding standard)
- AUTOSAR methodology (mandates MISRA C:2012 for all BSW and RTE code)
- OEM supplier requirements (most Tier-1 contracts mandate MISRA compliance)
- Tool qualification: static analysis tools used for tool qualification (ISO 26262 Part 8) are configured against MISRA rule sets

**Scope:** The C programming language as defined by ISO/IEC 9899:1990 (C90), ISO/IEC 9899:1999 (C99), and ISO/IEC 9899:2011 (C11). MISRA C:2012 targets C99 primarily.

---

## 2. Edition History

| Edition | Year | Rules | Notes |
|---|---|---|---|
| **MISRA C:1998** | 1998 | 127 rules | First edition; automotive focus; C90 only |
| **MISRA C:2004** | 2004 | 141 rules | Refined rule categories; widely adopted |
| **MISRA C:2012** | 2012 | 143 rules + 16 directives | Current mainstream; C99/C11 support; directives introduced; CERT-C alignment |
| **MISRA C:2012 AMD1** | 2016 | +14 rules | Security focus; overlapping storage, flexible array members |
| **MISRA C:2012 AMD2** | 2020 | Revised | C11 support; static assertions; _Generic; deprecations |
| **MISRA C:2023** | 2023 | Major revision | Merged AMD1+AMD2; new security rules; C17 alignment |

**Current mainstream in automotive production:** MISRA C:2012 with AMD1 (2016). MISRA C:2023 adoption is in progress as of 2025.

---

## 3. Rule Classification

### 3.1 Category

| Category | Obligation | Meaning | Can Be Deviated? |
|---|---|---|---|
| **Mandatory** | Absolute | Violation cannot be justified under any circumstance | No |
| **Required** | Default on | Rule must be followed unless a formal deviation is approved | Yes, with documented justification |
| **Advisory** | Default on | Best practice; deviation with brief justification | Yes, more easily |

**Mandatory rules (examples):** Rule 13.6 (side effects in sizeof), Rule 17.3 (no implicit function declarations), Rule 17.4 (all exit paths must have a return value in non-void functions).

### 3.2 Decidability

| Type | Meaning | Tool Implication |
|---|---|---|
| **Decidable** | A tool can always determine compliance with 100% certainty | Fully automatable |
| **Undecidable** | Depends on runtime behaviour or program-wide analysis | Requires manual review or heuristic |

### 3.3 Directive vs. Rule

| Item | Target | Example |
|---|---|---|
| **Directive** | Development process or environment (cannot always be checked by tool alone) | Dir 4.1: Run-time failures shall be minimised |
| **Rule** | Source code text (checkable by static analysis tool) | Rule 8.7: Functions with internal linkage shall be declared static |

---

## 4. The 16 Directives (MISRA C:2012)

| ID | Category | Title |
|---|---|---|
| Dir 1.1 | Required | Any implementation-defined behaviour on which the output of the program depends shall be documented |
| Dir 2.1 | Required | All source files shall compile without any compiler warnings |
| Dir 3.1 | Required | All code shall be traceable to documented requirements |
| Dir 4.1 | Required | Run-time failures shall be minimised |
| Dir 4.2 | Advisory | All usage of assembly language should be documented |
| Dir 4.3 | Required | Assembly language shall be encapsulated and isolated |
| Dir 4.4 | Advisory | Sections of code should not be "commented out" |
| Dir 4.5 | Advisory | Identifiers in the same name space with overlapping visibility should be typographically unambiguous |
| Dir 4.6 | Advisory | typedefs that indicate size and signedness should be used instead of the basic numerical types |
| Dir 4.7 | Required | If a function returns error information, then that error information shall be tested |
| Dir 4.8 | Advisory | If a pointer to a structure or union is never dereferenced within a translation unit, then the implementation of the object should be hidden |
| Dir 4.9 | Advisory | A function should be used in preference to a function-like macro where they are interchangeable |
| Dir 4.10 | Required | Precautions shall be taken in order to prevent the contents of a header file being included more than once |
| Dir 4.11 | Required | The validity of values passed to library functions shall be checked |
| Dir 4.12 | Required | Dynamic memory allocation shall not be used |
| Dir 4.13 | Advisory | Functions which are designed to provide operations on a resource should be called in an appropriate sequence |
| Dir 4.14 | Required | The validity of values received from external sources shall be checked |
| Dir 4.15 | Required | Invariants shall not be violated |

---

## 5. Key Rules by Section

### Section 1: Standard C Environment
| Rule | Cat | Description |
|---|---|---|
| 1.1 | Req | The program shall contain no violations of the standard C syntax |
| 1.2 | Adv | Language extensions should not be used |
| 1.3 | Man | There shall be no occurrence of undefined or critical unspecified behaviour |
| 1.4 | Req | Emergent language features and library functions shall not be used without documented justification |

### Section 2: Unused Code
| Rule | Cat | Description |
|---|---|---|
| 2.1 | Man | A project shall not contain unreachable code |
| 2.2 | Man | There shall be no dead code |
| 2.3 | Adv | A project should not contain unused type declarations |
| 2.4 | Adv | A project should not contain unused tag declarations |
| 2.5 | Adv | A project should not contain unused macro declarations |
| 2.6 | Adv | A function should not contain unused label declarations |
| 2.7 | Adv | There should be no unused parameters in functions |

### Section 5: Identifiers
| Rule | Cat | Description |
|---|---|---|
| 5.1 | Req | External identifiers shall be distinct (within first 31 characters) |
| 5.2 | Req | Identifiers declared in the same scope and namespace shall be distinct |
| 5.3 | Req | An identifier declared in an inner scope shall not hide an identifier in an outer scope |
| 5.4 | Req | Macro identifiers shall be distinct |
| 5.5 | Req | Identifiers shall be distinct from macro names |
| 5.6 | Req | A typedef name shall be a unique identifier |
| 5.7 | Req | A tag name shall be a unique identifier |
| 5.8 | Req | Identifiers that define objects or functions with external linkage shall be unique |
| 5.9 | Adv | Identifiers that define objects or functions with internal linkage should be unique |

### Section 6: Basic Types
| Rule | Cat | Description |
|---|---|---|
| 6.1 | Req | Bit fields shall only be declared with an explicitly signed or unsigned integer type |
| 6.2 | Req | Single-bit named bit fields shall be of an unsigned type |

### Section 7: Literals and Constants
| Rule | Cat | Description |
|---|---|---|
| 7.1 | Req | Octal constants shall not be used |
| 7.2 | Req | A u or U suffix shall be applied to all integer constants that are represented in an unsigned type |
| 7.3 | Req | The lowercase character 'l' shall not be used as a suffix |
| 7.4 | Req | A string literal shall not be assigned to an object unless the object's type is "pointer to const-qualified char" |

### Section 8: Declarations and Definitions
| Rule | Cat | Description |
|---|---|---|
| 8.1 | Req | Types shall be explicitly specified |
| 8.2 | Req | Function types shall be in prototype form |
| 8.3 | Req | All declarations of an object or function shall use the same names and type qualifiers |
| 8.4 | Req | A compatible declaration shall be visible when an object or function with external linkage is defined |
| 8.5 | Req | An external object or function shall be declared once in one and only one file |
| 8.6 | Req | An identifier with external linkage shall have exactly one external definition |
| 8.7 | Adv | Functions and objects should not be defined with external linkage if they are referenced in only one translation unit |
| 8.8 | Req | The static storage class specifier shall be used in all declarations of objects and functions that have internal linkage |
| 8.9 | Adv | An object should be defined at block scope if its identifier only appears in a single function |
| 8.10 | Req | An inline function shall be declared with the static storage class |
| 8.11 | Adv | When an array with external linkage is declared, its size should be explicitly specified |
| 8.12 | Req | Within an enumerator list, the value of an implicitly-specified enumeration constant shall be unique |
| 8.13 | Adv | A pointer should point to a const-qualified type whenever possible |
| 8.14 | Req | The restrict type qualifier shall not be used |

### Section 9: Initialization
| Rule | Cat | Description |
|---|---|---|
| 9.1 | Man | The value of an object with automatic storage duration shall not be read before it has been set |
| 9.2 | Req | The initializer for an aggregate or union shall be enclosed in braces |
| 9.3 | Req | Arrays shall not be partially initialized |
| 9.4 | Req | An element of an object shall not be initialized more than once |
| 9.5 | Req | Where designated initializers are used to initialize an array object the size of the array shall be specified explicitly |

### Section 10: Essential Type Model
The **Essential Type Model** is a MISRA C:2012 innovation that classifies expressions into essential categories and restricts mixing them.

| Essential Type | C Types Included |
|---|---|
| Boolean | `_Bool`, results of relational/logical operators |
| Character | `char` |
| Signed | `signed char`, `short`, `int`, `long`, `long long` |
| Unsigned | `unsigned char`, `unsigned short`, `unsigned int`, `unsigned long`, `unsigned long long` |
| Floating | `float`, `double`, `long double` |
| Enum | enumeration types |

| Rule | Cat | Description |
|---|---|---|
| 10.1 | Req | Operands shall not be of an inappropriate essential type |
| 10.2 | Req | Expressions of essentially character type shall not be used inappropriately in addition and subtraction operations |
| 10.3 | Req | The value of an expression shall not be assigned to an object with a narrower essential type or different essential type category |
| 10.4 | Req | Both operands of an operator in which the usual arithmetic conversions are performed shall have the same essential type category |
| 10.5 | Adv | The value of an expression should not be cast to an inappropriate essential type |
| 10.6 | Req | The value of a composite expression shall not be assigned to an object with wider essential type |
| 10.7 | Req | If a composite expression is used as one operand of an operator in which the usual arithmetic conversions are performed then the other operand shall not have wider essential type |
| 10.8 | Req | The value of a composite expression shall not be cast to a different essential type category or a wider essential type |

### Section 11: Pointer Type Conversions
| Rule | Cat | Description |
|---|---|---|
| 11.1 | Req | Conversions shall not be performed between a pointer to a function and any other type |
| 11.2 | Req | Conversions shall not be performed between a pointer to an incomplete type and any other type |
| 11.3 | Req | A cast shall not be performed between a pointer to object type and a pointer to a different object type |
| 11.4 | Adv | A conversion should not be performed between a pointer to object and an integer type |
| 11.5 | Adv | A conversion should not be performed from pointer to void into pointer to object |
| 11.6 | Req | A cast shall not be performed between pointer to void and an arithmetic type |
| 11.7 | Req | A cast shall not be performed between pointer to object and a non-integer arithmetic type |
| 11.8 | Req | A cast shall not remove any const or volatile qualification from the type pointed to by a pointer |
| 11.9 | Req | The macro NULL shall be the only permitted form of integer null pointer constant |

### Section 12: Side Effects
| Rule | Cat | Description |
|---|---|---|
| 12.1 | Adv | The precedence of operators within expressions should be made explicit |
| 12.2 | Req | The right-hand operand of a shift operator shall lie in the range zero to one less than the width in bits of the essential type of the left-hand operand |
| 12.3 | Adv | The comma operator should not be used |
| 12.4 | Adv | Evaluation of constant expressions should not lead to unsigned integer wrap-around |
| 12.5 | Man | The sizeof operator shall not have an operand which is a function parameter declared as "array of type" |

### Section 13: Side Effects
| Rule | Cat | Description |
|---|---|---|
| 13.1 | Req | Initializer lists shall not contain persistent side effects |
| 13.2 | Req | The value of an expression and its persistent side effects shall be the same under all permitted evaluation orders |
| 13.3 | Adv | A full expression containing an increment (++) or decrement (--) operator should have no other potential side effects other than that caused by the operator |
| 13.4 | Adv | The result of an assignment operator should not be used |
| 13.5 | Req | The right-hand operand of a logical && or \|\| operator shall not contain persistent side effects |
| 13.6 | Man | The operand of the sizeof operator shall not contain any expression which has potential side effects |

### Section 14: Control Flow
| Rule | Cat | Description |
|---|---|---|
| 14.1 | Req | A loop counter shall not have essentially floating type |
| 14.2 | Req | A for loop shall be well-formed |
| 14.3 | Req | Controlling expressions shall not be invariant |
| 14.4 | Req | The controlling expression of an if / #if statement shall be essentially Boolean |

### Section 15: Control Flow — Branching
| Rule | Cat | Description |
|---|---|---|
| 15.1 | Adv | The goto statement should not be used |
| 15.2 | Req | The goto statement shall jump to a label declared later in the same function |
| 15.3 | Req | Any label referenced by a goto statement shall be declared in the same block as the goto or in any block enclosing the goto |
| 15.4 | Adv | There should be no more than one break or goto statement used to terminate any iteration statement |
| 15.5 | Adv | A function should have a single point of exit at the end |
| 15.6 | Req | The body of an iteration-statement or a selection-statement shall be a compound statement |
| 15.7 | Req | All if … else if constructs shall be terminated with an else statement |

### Section 16: Switch Statements
| Rule | Cat | Description |
|---|---|---|
| 16.1 | Req | All switch statements shall be well-formed |
| 16.2 | Req | A switch label shall only be used when the most closely-enclosing compound statement is the body of a switch statement |
| 16.3 | Req | An unconditional break statement shall terminate every switch-clause |
| 16.4 | Req | Every switch statement shall have a default label |
| 16.5 | Req | A default label shall appear as either the first or the last switch label of a switch statement |
| 16.6 | Req | Every switch statement shall have at least two switch-clauses |
| 16.7 | Req | A switch-expression shall not have essentially Boolean type |

### Section 17: Functions
| Rule | Cat | Description |
|---|---|---|
| 17.1 | Req | The features of <stdarg.h> shall not be used |
| 17.2 | Req | Functions shall not call themselves, either directly or indirectly |
| 17.3 | Man | A function shall not be declared implicitly |
| 17.4 | Man | All exit paths from a function with non-void return type shall have an explicit return statement with an expression |
| 17.5 | Adv | The function argument corresponding to a parameter declared to have an array type shall have an appropriate number of elements |
| 17.6 | Man | The declaration of an array parameter shall not contain the static keyword between the [ ] |
| 17.7 | Req | The value returned by a function having non-void return type shall be used |
| 17.8 | Adv | A function parameter should not be modified |

### Section 18: Pointers and Arrays
| Rule | Cat | Description |
|---|---|---|
| 18.1 | Req | A pointer resulting from arithmetic on a pointer operand shall address an element of the same array as that pointer operand |
| 18.2 | Req | Subtraction between pointers shall only be applied to pointers that address elements of the same array |
| 18.3 | Req | The relational operators >, >=, < and <= shall not be applied to objects of pointer type except where they point into the same object |
| 18.4 | Adv | The +, -, += and -= operators should not be applied to an expression of pointer type |
| 18.5 | Adv | Declarations should contain no more than two levels of pointer nesting |
| 18.6 | Req | The address of an object with automatic storage shall not be copied to another object that persists after the first object has ceased to exist |
| 18.7 | Req | Flexible array members shall not be declared |
| 18.8 | Req | Variable-length array types shall not be used |

### Section 20: Preprocessing Directives
| Rule | Cat | Description |
|---|---|---|
| 20.1 | Adv | #include directives should only be preceded by preprocessor directives or comments |
| 20.2 | Req | The ', " or \ characters and the /* or // character sequences shall not occur in a header file name |
| 20.3 | Req | The #include directive shall be followed by either a <filename> or "filename" sequence |
| 20.4 | Req | A macro shall not be defined with the same name as a keyword |
| 20.5 | Adv | #undef should not be used |
| 20.6 | Req | Tokens that look like a preprocessing directive shall not occur within a macro argument |
| 20.7 | Req | Expressions resulting from the expansion of macro parameters shall be enclosed in parentheses |
| 20.8 | Req | The controlling expression of a #if or #elif preprocessing directive shall evaluate to 0 or 1 |
| 20.9 | Req | All identifiers used in the controlling expression of #if or #elif preprocessing directives shall be #define'd before evaluation |
| 20.10 | Adv | The # and ## preprocessor operators should not be used |
| 20.11 | Req | A macro parameter immediately following a # operator shall not immediately be followed by a ## operator |
| 20.12 | Req | A macro parameter used as an operand to the # or ## operators, which is itself subject to further macro replacement, shall only be used as an operand to these operators |
| 20.13 | Req | A line whose first token is # shall be a valid preprocessing directive |
| 20.14 | Req | All #else, #elif and #endif preprocessor directives shall reside in the same file as the #if, #ifdef or #ifndef directive to which they are related |

### Section 21: Standard Libraries
| Rule | Cat | Description |
|---|---|---|
| 21.1 | Req | #define and #undef shall not be used on a reserved identifier or reserved macro name |
| 21.2 | Req | A reserved identifier or macro name shall not be declared |
| 21.3 | Req | The memory allocation and deallocation functions of <stdlib.h> shall not be used |
| 21.4 | Req | The standard header file <setjmp.h> shall not be used |
| 21.5 | Req | The standard header file <signal.h> shall not be used |
| 21.6 | Req | The Standard Library input/output functions shall not be used in production code |
| 21.7 | Req | The atof, atoi, atol and atoll functions of <stdlib.h> shall not be used |
| 21.8 | Req | The library functions abort, exit, getenv and system of <stdlib.h> shall not be used |
| 21.9 | Req | The library functions bsearch and qsort of <stdlib.h> shall not be used |
| 21.10 | Req | The Standard Library time and date functions shall not be used |
| 21.11 | Req | The standard header file <tgmath.h> shall not be used |
| 21.12 | Adv | The exception handling features of <fenv.h> should not be used |

### Section 22: Resources
| Rule | Cat | Description |
|---|---|---|
| 22.1 | Req | All resources obtained dynamically by means of Standard Library functions shall be explicitly released |
| 22.2 | Man | A block of memory shall only be freed if it was allocated by means of a Standard Library function |
| 22.3 | Req | The same file shall not be open for read and write access at the same time on different streams |
| 22.4 | Man | There shall be no attempt to write to a stream which has been opened as read-only |
| 22.5 | Man | A pointer to a FILE object shall not be dereferenced |
| 22.6 | Man | The value of a pointer to a FILE shall not be used after the associated stream has been closed |
| 22.7 | Req | The macro EOF shall only be compared with the unmodified return value from any function capable of returning EOF |
| 22.8 | Req | The value of errno shall be set to zero prior to a call to an errno-setting-function |
| 22.9 | Req | The value of errno shall be tested against zero after calling an errno-setting function |
| 22.10 | Req | The value of errno shall only be tested when the last function to be called was an errno-setting function |

---

## 6. Mandatory Rules — Complete List

Rules that can NEVER be deviated from under any circumstance:

| Rule | Description |
|---|---|
| 1.3 | No undefined or critical unspecified behaviour |
| 2.1 | No unreachable code |
| 2.2 | No dead code |
| 9.1 | Object with automatic storage shall be set before read |
| 12.5 | sizeof shall not have a function parameter array as operand |
| 13.6 | sizeof operand shall have no side effects |
| 17.3 | No implicit function declarations |
| 17.4 | Non-void functions must have explicit return with expression |
| 17.6 | Array parameter declaration shall not use static between [] |
| 22.2 | Free only memory allocated by Standard Library |
| 22.4 | No write to read-only stream |
| 22.5 | No dereferencing FILE pointer |
| 22.6 | No use of FILE pointer after stream close |

---

## 7. Deviation Process

A **deviation** is the formal approval to violate a Required or Advisory rule in a specific location, with documented justification.

### Deviation Record Contents (MISRA Compliance:2020)

| Field | Content |
|---|---|
| **Rule** | Identifier (e.g., Rule 11.4) |
| **Deviation reference** | Unique ID traceable to the source code location |
| **Category of deviation** | Project / File / Function |
| **Rationale** | Why the rule is violated here; why it is safe |
| **Risk assessment** | What could go wrong; mitigations in place |
| **Reviewer** | Name and role of safety/technical reviewer |
| **Approval** | Authorised by (project lead, safety manager) |

### Annotation in Code (common practice)

```c
/* MISRA C:2012 Rule 11.4 deviation:
   Converting from uint32_t to pointer is required for hardware
   register access. The address is a constant defined in the MCU
   memory map and is guaranteed valid. Safety review ref: DEV-0042. */
volatile uint32_t *const pReg = (volatile uint32_t *)0x40021000u;  /* NOLINT(11.4) */
```

### Tool Suppression Keywords

| Tool | Suppression syntax |
|---|---|
| PC-lint Plus | `//lint -e{9016}` |
| LDRA | `/* LDRA_INSPECTED 11 4 */` |
| Polyspace | `/*polyspace<MISRA-C3:11.4:Not a defect:Justified>*/` |
| PRQA/Helix QAC | `/* PRQA S 0306 */` |

---

## 8. ASIL and Coverage Expectations

ISO 26262 Part 6 Table 1 lists coding guidelines as a method at all ASIL levels, but mandates **all** applicable rules at ASIL-C/D.

| ASIL | Expectation |
|---|---|
| QM | MISRA compliance recommended; few hard requirements |
| ASIL-A | MISRA C Mandatory + most Required rules |
| ASIL-B | MISRA C Mandatory + Required; deviations require documented justification |
| ASIL-C | Mandatory + Required; formal deviation process; all tool findings reviewed |
| ASIL-D | Mandatory + Required + high fraction of Advisory; zero unresolved tool warnings; independent review of all deviations |

---

## 9. MISRA C and AUTOSAR

AUTOSAR mandates MISRA C:2012 for all Basic Software (BSW) and RTE code. Deviations from Required rules require a deviation permit in the AUTOSAR Software Specification (SWS) documents. AUTOSAR publishes its own **AUTOSAR C++14 Coding Guidelines** for Adaptive Platform code; Classic Platform uses MISRA C.

Key AUTOSAR-specific additions on top of MISRA:
- Memory section macros (`MEMMAP_CODE`, `MEMMAP_DATA`) must be used — not raw `#pragma`
- Prefixed naming conventions: `<ModuleName>_<FunctionName>` for all public APIs
- Return type `Std_ReturnType` for all service functions returning success/failure

---

## 10. Tool Ecosystem

| Tool | Vendor | Notes |
|---|---|---|
| **PC-lint Plus** | Gimpel Software | Industry classic; fast; CI-friendly; MISRA C:2012 + AMD1 |
| **LDRA** | LDRA | Full lifecycle: MISRA, coverage, requirements traceability, ISO 26262 qualified |
| **Polyspace Bug Finder / Code Prover** | MathWorks | Formal-methods-based; proves absence of certain run-time errors; ISO 26262 qualified |
| **PRQA / Helix QAC** | Perforce | Deep MISRA support; AUTOSAR preferred by many OEMs |
| **Klocwork** | Perforce | SAST + MISRA; CI integration |
| **CodeSonar** | GrammaTech | Interprocedural; good for complex pointer analysis |
| **CppCheck** | Open source | Free; partial MISRA support; useful in development, not for formal qualification |

---

## 11. Common MISRA Violations and Fixes

| Violation | Rule | Non-compliant | Compliant |
|---|---|---|---|
| Implicit function declaration | 17.3 | `result = my_func(x);` (no prototype visible) | Add `#include "my_module.h"` or add prototype |
| Missing return in non-void | 17.4 | `int get_val() { if (x) return 1; }` | Add `return 0;` in all paths or restructure |
| Dynamic allocation | Dir 4.12 / 21.3 | `p = malloc(sizeof(T));` | Use static pool or stack allocation |
| Mixed integer types | 10.4 | `uint8_t x = u8 + s16;` | Cast explicitly: `uint8_t x = (uint8_t)((uint16_t)u8 + (uint16_t)s16);` |
| Non-boolean controlling expr | 14.4 | `if (flags)` | `if (flags != 0u)` |
| Missing default in switch | 16.4 | `switch (s) { case A: ... case B: ... }` | Add `default: break;` |
| Pointer-to-integer cast | 11.4 | `uint32_t addr = (uint32_t)ptr;` | Add deviation record; use `uintptr_t` |
| sizeof with side effects | 13.6 | `sizeof(buf[i++])` | `sizeof(buf[0])` |
| Recursive function | 17.2 | `int fact(int n) { return n * fact(n-1); }` | Rewrite iteratively |
| Variable-length array | 18.8 | `uint8_t buf[n];` | Use fixed-size array or static pool |
| Octal literal | 7.1 | `uint8_t x = 010;` | `uint8_t x = 8u;` |
| Commented-out code | Dir 4.4 | `/* result = old_func(x); */` | Remove or use `#if 0` with justification comment |
| Unsigned suffix missing | 7.2 | `uint32_t x = 4294967295;` | `uint32_t x = 4294967295u;` |

---

## 12. MISRA C:2023 — Key Changes from C:2012 AMD1

MISRA C:2023 is a full rewrite incorporating both amendments and new rules:

| Area | Change |
|---|---|
| Merged amendments | AMD1 (security) and AMD2 (C11) rules now in base document |
| New rules | Flexible array members, atomic types (_Atomic), static assertion |
| C17 alignment | Deprecated C11 features clarified |
| Security focus | Stronger rules on tainted data, format strings, and integer overflow |
| Rule numbering | Rules renumbered; toolchain updates required |

**Industry adoption timeline:** Most automotive programs targeting SOP after 2027 are expected to migrate to MISRA C:2023.

---

## 13. AutoPragma Integration Map

| AutoPragma Process | MISRA C Application |
|---|---|
| SWE.1 (SwRS derivation) | Verification method for coding-standard compliance items set to INSPECTION |
| SWE.3 (Detailed design) | Unit interface documentation checks aligned with Dir 4.6, 8.2 |
| SWE.4 (Unit verification) | Static analysis items reference MISRA C:2012 rules; tool: Polyspace / LDRA / PC-lint Plus |
| SWE.6 (Qualification test) | Static analysis test type maps to MISRA compliance check procedure |
| Tool qualification | Static analysis tool used for MISRA checking requires TCL-2 or TCL-3 qualification per ISO 26262 Part 8 |
