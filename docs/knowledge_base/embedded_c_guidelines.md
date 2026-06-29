# Embedded C Coding Guidelines Knowledge Base

Sources: BARR-C:2018 Embedded C Coding Standard, CERT C Coding Standard (SEI), NASA JPL C Coding Standard, AUTOSAR C Coding Guidelines, Jack Ganssle "The Art of Designing Embedded Systems", Michael Barr "Programming Embedded Systems", Elecia White "Making Embedded Systems", Dan Saks (Embedded Systems Programming columns), Phillip Laplante "Real-Time Systems Design and Analysis", Arm Cortex-M application note AN298.

---

## 1. Why Embedded C Is Different from Desktop C

Embedded C targets resource-constrained, safety-critical, and real-time environments with constraints that do not exist in desktop/server software.

| Constraint | Embedded Reality | Implication |
|---|---|---|
| **Memory** | KB to MB of RAM/Flash; no virtual memory; no MMU (typically) | No dynamic allocation; fixed-size buffers; ROM-able code |
| **CPU** | MHz range; 8/16/32-bit; no FPU (often) | No floating-point in ISRs; integer arithmetic preferred; cycle-budget management |
| **Real-time** | Hard deadlines; preemption; shared interrupts | Volatile, atomic access, ISR-safe code patterns |
| **Compiler** | Cross-compilers; vendor-specific extensions; C90/C99 subset | Portability of type sizes, alignment, calling conventions |
| **No OS / RTOS** | Bare metal or RTOS; no stdlib full support | No printf in production; no malloc; no system calls |
| **Long field life** | 10–15 year automotive field life | Defensive programming; no silent failures; watchdog |
| **Safety** | Functional safety (ISO 26262) | Deterministic behaviour; no undefined behaviour |
| **Security** | Cybersecurity (ISO/SAE 21434) | Input validation; cryptographic correctness; no information leakage |

---

## 2. Data Types and Portability

### 2.1 Use Fixed-Width Integer Types

Never use `int`, `long`, `short` directly — their width is implementation-defined.

```c
/* Non-portable — BAD */
int counter;
unsigned long timestamp;

/* Portable — GOOD */
#include <stdint.h>
int32_t  counter;
uint32_t timestamp;
uint8_t  byte_val;
uint16_t word_val;
```

| Type | Width | Use |
|---|---|---|
| `uint8_t` | 8-bit unsigned | Byte buffers, status flags, small counters |
| `int8_t`  | 8-bit signed   | Signed temperature offsets, corrections |
| `uint16_t`| 16-bit unsigned | ADC values, CAN IDs, 16-bit registers |
| `int16_t` | 16-bit signed  | Signed sensor values |
| `uint32_t`| 32-bit unsigned | Timestamps, 32-bit registers, bitmasks |
| `int32_t` | 32-bit signed  | Signed calculations, accumulators |
| `uint64_t`| 64-bit unsigned | Use sparingly; alignment/atomicity issues on 32-bit MCUs |
| `bool`    | Boolean (via `<stdbool.h>`) | Use only for true/false conditions |
| `uintptr_t` | Pointer-width | Only when converting pointer to integer (MISRA deviation required) |

### 2.2 Avoid `char` for Numeric Values

`char` signedness is implementation-defined. Use `int8_t` for signed bytes and `uint8_t` for unsigned bytes. Use `char` only for string characters.

### 2.3 Struct Packing and Alignment

```c
/* Unpadded for hardware register maps */
#pragma pack(push, 1)
typedef struct {
    uint8_t  status;
    uint16_t data;
    uint8_t  checksum;
} CAN_Frame_t;
#pragma pack(pop)

/* Preferred: use compiler attributes for portability */
typedef struct __attribute__((packed)) {
    uint8_t  status;
    uint16_t data;
    uint8_t  checksum;
} CAN_Frame_t;
```

**Rule:** Never assume struct member order or padding. Always use explicit packing when mapping structs to hardware registers or communication frames.

---

## 3. Volatile — When and Why

`volatile` tells the compiler that a variable may change at any time, outside the normal program flow — from an ISR, DMA engine, or hardware register.

### 3.1 Hardware Register Access

```c
/* Always use volatile for hardware registers */
#define GPIOA_ODR  (*((volatile uint32_t *)0x40020014u))

/* Or via struct (preferred for register maps) */
typedef struct {
    volatile uint32_t MODER;
    volatile uint32_t OTYPER;
    volatile uint32_t OSPEEDR;
    volatile uint32_t PUPDR;
    volatile uint32_t IDR;
    volatile uint32_t ODR;
} GPIO_Registers_t;

static GPIO_Registers_t * const GPIOA = (GPIO_Registers_t *)0x40020000u;
```

### 3.2 Variables Shared with ISRs

```c
static volatile uint32_t g_tickCount = 0u;   /* Written by SysTick ISR */

void SysTick_Handler(void) {
    g_tickCount++;                             /* Volatile ensures no caching */
}

uint32_t GetTick(void) {
    return g_tickCount;                        /* Compiler will not optimise away */
}
```

### 3.3 Common Volatile Mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Missing `volatile` on shared variable | Compiler caches value in register; ISR update invisible | Add `volatile` |
| `volatile` on entire array | Entire array re-read on every access; performance cost | `volatile uint8_t array[N]` — each element is volatile |
| Casting away `volatile` | Undefined behaviour; compiler may cache | Never remove `volatile` qualifier |
| Using `volatile` as a synchronisation mechanism | Not an atomic guarantee on multi-core | Use also memory barriers or atomic operations |

---

## 4. Interrupt Service Routines (ISRs)

### 4.1 ISR Design Rules

1. **Keep ISRs short.** An ISR should only acknowledge the interrupt, set a flag or push data to a ring buffer, and return. Heavy processing belongs in the task/main loop.
2. **No blocking calls** in ISRs (no mutexes, no sleep, no RTOS blocking API).
3. **No printf or standard I/O** in ISRs (uses heap, non-reentrant).
4. **Variables shared with ISRs must be `volatile`.**
5. **Critical sections** protect shared data modified in both ISR and task context.
6. **Re-entrant functions** only — ISR must not call non-reentrant library functions.

### 4.2 ISR-Safe Data Exchange Patterns

```c
/* Flag pattern: ISR sets, task reads and clears */
static volatile bool g_uart_rx_ready = false;
static volatile uint8_t g_uart_rx_byte = 0u;

void UART1_IRQHandler(void) {
    g_uart_rx_byte  = UART1->DR;
    g_uart_rx_ready = true;
}

void Task_ProcessUART(void) {
    if (g_uart_rx_ready) {
        uint8_t byte;
        /* Critical section: disable interrupt to ensure atomic read+clear */
        __disable_irq();
        byte            = g_uart_rx_byte;
        g_uart_rx_ready = false;
        __enable_irq();
        ProcessByte(byte);
    }
}
```

### 4.3 Ring Buffer for ISR→Task Communication

A lock-free single-producer / single-consumer ring buffer is the canonical embedded pattern for ISR-to-task communication when the ISR is the sole producer.

```c
#define RING_BUF_SIZE  (64u)  /* Must be power of two */

typedef struct {
    volatile uint8_t  data[RING_BUF_SIZE];
    volatile uint32_t head;  /* Written by ISR */
    volatile uint32_t tail;  /* Written by task */
} RingBuffer_t;

static RingBuffer_t g_rx_buf = {0};

/* ISR side — no locking needed (single producer) */
void UART_IRQHandler(void) {
    uint32_t next_head = (g_rx_buf.head + 1u) & (RING_BUF_SIZE - 1u);
    if (next_head != g_rx_buf.tail) {
        g_rx_buf.data[g_rx_buf.head] = UART1->DR;
        g_rx_buf.head = next_head;
    }
}

/* Task side */
bool RingBuffer_Pop(uint8_t *out) {
    if (g_rx_buf.tail == g_rx_buf.head) { return false; }
    *out = g_rx_buf.data[g_rx_buf.tail];
    g_rx_buf.tail = (g_rx_buf.tail + 1u) & (RING_BUF_SIZE - 1u);
    return true;
}
```

---

## 5. No Dynamic Memory Allocation

**Rule (absolute in safety-critical embedded):** Never use `malloc`, `calloc`, `realloc`, or `free` in production embedded software.

**Why:**
- Heap fragmentation causes non-deterministic allocation failure after extended runtime
- Allocation time is non-deterministic — violates real-time constraints
- `free` to wrong address or double-free causes undefined behaviour
- ISO 26262 and MISRA C:2012 Dir 4.12 / Rule 21.3 prohibit dynamic allocation

### 5.1 Alternatives

| Need | Static Alternative |
|---|---|
| Variable-size buffer | Fixed maximum-size array; carry length separately |
| Object pool | Statically declared array of structs; manage free-list with a bitmap |
| String formatting | `snprintf` to a fixed-size buffer on the stack |
| Growable list | Circular buffer with fixed capacity; return error on overflow |

```c
/* Object pool pattern */
#define MAX_TIMERS  (16u)

typedef struct {
    bool     active;
    uint32_t expiry_ms;
    void   (*callback)(void);
} Timer_t;

static Timer_t g_timer_pool[MAX_TIMERS];

Timer_t *Timer_Alloc(void) {
    for (uint8_t i = 0u; i < MAX_TIMERS; i++) {
        if (!g_timer_pool[i].active) {
            g_timer_pool[i].active = true;
            return &g_timer_pool[i];
        }
    }
    return NULL;  /* Pool exhausted — caller must handle */
}
```

---

## 6. Defensive Programming and Error Handling

### 6.1 Validate All Inputs at System Boundaries

```c
Std_ReturnType Motor_SetSpeed(int16_t speed_rpm) {
    if ((speed_rpm < MOTOR_MIN_RPM) || (speed_rpm > MOTOR_MAX_RPM)) {
        Dem_SetEventStatus(DEM_EVENT_MOTOR_PARAM_OUT_OF_RANGE, DEM_EVENT_STATUS_FAILED);
        return E_NOT_OK;
    }
    /* ... proceed safely */
    return E_OK;
}
```

### 6.2 Never Silently Discard Errors

```c
/* BAD: error ignored */
NvM_ReadBlock(NVM_BLOCK_CALIBRATION, &g_cal);

/* GOOD: error handled */
Std_ReturnType ret = NvM_ReadBlock(NVM_BLOCK_CALIBRATION, &g_cal);
if (ret != E_OK) {
    /* Fall back to ROM defaults; log DTC */
    g_cal = g_cal_defaults;
    Dem_SetEventStatus(DEM_EVENT_NVM_READ_FAIL, DEM_EVENT_STATUS_FAILED);
}
```

### 6.3 Assertions in Development; Diagnostics in Production

```c
/* Development: halt immediately on contract violation */
#ifdef DEBUG
  #define ASSERT(cond)  do { if (!(cond)) { __BKPT(0); } } while (0)
#else
/* Production: log DTC; take safe reaction */
  #define ASSERT(cond)  do { \
    if (!(cond)) { \
        Dem_SetEventStatus(DEM_EVENT_INTERNAL_ASSERT, DEM_EVENT_STATUS_FAILED); \
        SafeState_Enter(); \
    } \
  } while (0)
#endif
```

---

## 7. Integer Arithmetic and Overflow

### 7.1 Unsigned Overflow (Wrap-Around)

Unsigned arithmetic wraps around by definition (ISO C). This can be deliberate (ring buffer index) or a bug (counter overflow).

```c
/* DELIBERATE wrap-around: ring buffer index modulo power of two */
head = (head + 1u) & (BUF_SIZE - 1u);

/* ACCIDENTAL overflow: unguarded addition */
uint8_t x = 255u;
uint8_t y = x + 1u;   /* y = 0 — silent wrap; check for this! */

/* GUARD: check before operation */
if (x < UINT8_MAX) { y = x + 1u; }
```

### 7.2 Signed Overflow — Undefined Behaviour

Signed integer overflow is **undefined behaviour** in C. Never rely on it.

```c
/* UB: signed overflow */
int32_t a = INT32_MAX;
int32_t b = a + 1;   /* UB — compiler may do anything */

/* SAFE: check before operation */
if (a < INT32_MAX) { b = a + 1; }
```

### 7.3 Integer Promotions and Implicit Conversions

```c
uint8_t a = 200u;
uint8_t b = 100u;
uint8_t result;

/* BUG: both promote to int (signed); subtraction is -100; assigned to uint8_t = 156 */
result = a - b;

/* CORRECT: explicit cast */
result = (uint8_t)(a - b);   /* Clear intent; MISRA Rule 10.3 compliant */
```

### 7.4 Bit Shifts

```c
/* MISRA Rule 12.2: shift amount must be < width of type */
uint32_t val = 1u << 31u;    /* OK: 31 < 32 */
uint32_t bad = 1u << 32u;    /* UB: shift by width of type */

/* Shift of signed type — avoid entirely */
int32_t x = -1;
x >> 1;   /* Implementation-defined; use unsigned */
```

---

## 8. Fixed-Point Arithmetic

When hardware lacks an FPU, use fixed-point arithmetic to represent fractional values.

```c
/* Q15 fixed-point: value = raw_val / 2^15 */
typedef int16_t q15_t;   /* Range: [-1.0, +1.0) */

/* Q16.16 fixed-point: integer part + 16-bit fractional */
typedef int32_t q16_16_t;  /* Multiply two Q16.16: shift right by 16 */

#define FLOAT_TO_Q15(x)   ((q15_t)((x) * 32768.0f))
#define Q15_TO_FLOAT(x)   ((float)(x) / 32768.0f)

/* Safe Q15 multiply: (a * b) >> 15 with saturation */
q15_t Q15_Mul(q15_t a, q15_t b) {
    int32_t result = ((int32_t)a * (int32_t)b) >> 15;
    /* Saturate to Q15 range */
    if (result >  32767) { return  32767; }
    if (result < -32768) { return -32768; }
    return (q15_t)result;
}
```

---

## 9. Bit Manipulation

### 9.1 Named Bit Masks — No Magic Numbers

```c
/* BAD: magic number */
status_reg |= 0x04u;

/* GOOD: named mask */
#define STATUS_TX_READY_BIT   (0x04u)
#define STATUS_RX_READY_BIT   (0x08u)
#define STATUS_ERROR_BIT      (0x01u)

status_reg |= STATUS_TX_READY_BIT;
```

### 9.2 Standard Bit Manipulation Patterns

```c
/* Set bit n */
reg |=  (1u << n);

/* Clear bit n */
reg &= ~(1u << n);

/* Toggle bit n */
reg ^=  (1u << n);

/* Test bit n */
if ((reg & (1u << n)) != 0u) { /* bit is set */ }

/* Read field (bits 7:4) */
uint8_t field = (uint8_t)((reg >> 4u) & 0x0Fu);

/* Write field (bits 7:4) without disturbing other bits */
reg = (uint8_t)((reg & ~0xF0u) | ((value & 0x0Fu) << 4u));
```

### 9.3 Struct Bit Fields — Use with Caution

Bit field layout is implementation-defined. Use **only** for human-readable code, never to map hardware registers.

```c
/* SAFE: internal use only; never mapped to hardware */
typedef struct {
    uint8_t fault_detected : 1;
    uint8_t safe_state     : 1;
    uint8_t degraded_mode  : 1;
    uint8_t reserved       : 5;
} SafetyFlags_t;

/* UNSAFE: do NOT use struct bit fields to map hardware registers */
/* Use explicit masking and shifting instead (see 9.2 above) */
```

---

## 10. Watchdog Service

The watchdog timer (WDT/IWDG/WWDG) is a hardware timer that resets the MCU if not periodically "kicked" — proving the software is alive. Failure to service it within the window triggers a reset.

### 10.1 Rules

1. The watchdog shall be enabled on power-up and never disabled in production firmware.
2. The watchdog shall be serviced from a well-defined location that proves the main loop has executed.
3. In AUTOSAR, use `WdgM_MainFunction()` and alive/deadline supervision — **never** call the watchdog driver directly from application code.
4. Do not service the watchdog inside an ISR or inside a while-forever loop that bypasses the main task scheduler.
5. In safety-critical applications (ASIL-B+), use a two-stage watchdog: internal MCU WDT + external hardware watchdog IC.

```c
/* RTOS-less bare-metal watchdog service */
void MainLoop(void) {
    while (1) {
        Task_100ms();
        Task_10ms();
        Task_1ms();
        Wdg_Service();   /* Kick WDT only after all tasks complete */
    }
}

/* AUTOSAR pattern: supervise via WdgM alive supervision */
void MyRunnable_10ms(void) {
    /* ... runnable body ... */
    WdgM_UpdateAliveCounter(WDGM_SUPERVISED_ENTITY_MY_RUNNABLE);
}
```

---

## 11. Endianness

Embedded systems may be little-endian (Arm Cortex-M, x86) or big-endian (some PowerPC, network byte order). Mixed-endian data exists in some protocols.

```c
/* Portable multi-byte construction — never assume byte order */
/* Convert 4 bytes from big-endian buffer to uint32_t */
static inline uint32_t ReadBE32(const uint8_t *buf) {
    return ((uint32_t)buf[0] << 24u) |
           ((uint32_t)buf[1] << 16u) |
           ((uint32_t)buf[2] <<  8u) |
           ((uint32_t)buf[3]);
}

/* Detect at compile time (GCC/Clang) */
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  #define HOST_TO_BE32(x)  __builtin_bswap32(x)
#else
  #define HOST_TO_BE32(x)  (x)
#endif
```

**Never use pointer punning to detect endianness at run time in safety-critical code** — it involves aliasing and is undefined behaviour in strict-aliasing C.

---

## 12. Compiler-Specific Attributes and Pragmas

| Attribute | GCC/Clang | IAR | Arm Compiler 6 | Purpose |
|---|---|---|---|---|
| Pack struct | `__attribute__((packed))` | `__packed` | `__attribute__((packed))` | Remove padding from struct |
| Align variable | `__attribute__((aligned(N)))` | `__attribute__((aligned(N)))` | `__attribute__((aligned(N)))` | Force N-byte alignment |
| Inline | `__attribute__((always_inline))` | `__attribute__((always_inline))` | `__attribute__((always_inline))` | Force inlining |
| Weak symbol | `__attribute__((weak))` | `__weak` | `__attribute__((weak))` | Default stub overridable by linker |
| ISR entry | `__attribute__((interrupt))` | Toolchain-specific | Not needed on Cortex-M | ISR prologue/epilogue |
| No return | `__attribute__((noreturn))` | `__noreturn` | `__attribute__((noreturn))` | Functions that never return |
| Section | `__attribute__((section(".mySection")))` | `@ ".mySection"` | `__attribute__((section(".mySection")))` | Place in specific linker section |

**Guideline:** Isolate all compiler-specific attributes in a single `compiler_cfg.h` header behind macros, so the application code remains portable.

```c
/* compiler_cfg.h */
#if defined(__GNUC__)
  #define ATTR_PACKED      __attribute__((packed))
  #define ATTR_ALIGNED(n)  __attribute__((aligned(n)))
  #define ATTR_NORETURN    __attribute__((noreturn))
#elif defined(__IAR_SYSTEMS_ICC__)
  #define ATTR_PACKED      __packed
  #define ATTR_ALIGNED(n)  __attribute__((aligned(n)))
  #define ATTR_NORETURN    __noreturn
#else
  #error "Unsupported compiler — extend compiler_cfg.h"
#endif
```

---

## 13. Function Pointers and Callbacks

Function pointers are common in embedded for table-driven state machines, callback registration, and plugin architectures.

### 13.1 Typedef Function Pointer Types

```c
/* Define a type for the callback signature */
typedef void (*EventCallback_t)(uint32_t event_id, void *context);

/* Register callback */
static EventCallback_t g_callbacks[MAX_EVENTS];

void Event_Register(uint32_t event_id, EventCallback_t cb) {
    if ((event_id < MAX_EVENTS) && (cb != NULL)) {
        g_callbacks[event_id] = cb;
    }
}

/* Invoke safely */
void Event_Dispatch(uint32_t event_id) {
    if ((event_id < MAX_EVENTS) && (g_callbacks[event_id] != NULL)) {
        g_callbacks[event_id](event_id, NULL);
    }
}
```

### 13.2 State Machine Table Pattern

```c
typedef void (*StateHandler_t)(void);

static StateHandler_t const g_state_table[STATE_MAX] = {
    [STATE_INIT]    = State_Init,
    [STATE_RUNNING] = State_Running,
    [STATE_FAULT]   = State_Fault,
};

void StateMachine_Run(State_t current) {
    if (current < STATE_MAX) {
        g_state_table[current]();
    }
}
```

---

## 14. Stack Usage and Overflow Prevention

Stack overflow is a common source of embedded system crashes — especially hard to debug because it silently corrupts data before the crash manifests.

### 14.1 Guidelines

1. Declare large arrays as `static` (BSS/data segment) rather than on the stack.
2. Avoid deep recursion — flat call trees are safer (see also MISRA Rule 17.2).
3. Use the linker to place a stack guard region (canary pattern or MPU write-protected page).
4. Measure worst-case stack usage with static analysis (PC-lint, IAR Stack Analyzer) and dynamic measurement (stack paint pattern).
5. Set RTOS stack sizes at 1.5× the measured peak, with overflow detection enabled.

```c
/* Stack paint pattern: fill stack with known value at startup */
#define STACK_CANARY  0xDEADBEEFu

void Stack_Paint(void) {
    extern uint32_t _stack_start;
    extern uint32_t _stack_end;
    uint32_t *p = &_stack_start;
    while (p < &_stack_end) { *p++ = STACK_CANARY; }
}

uint32_t Stack_GetMinFree(void) {
    extern uint32_t _stack_start;
    extern uint32_t _stack_end;
    uint32_t *p = &_stack_start;
    while ((*p == STACK_CANARY) && (p < &_stack_end)) { p++; }
    return (uint32_t)((uintptr_t)p - (uintptr_t)&_stack_start);
}
```

---

## 15. Const Correctness

Use `const` aggressively — it communicates intent, enables read-only placement in Flash, and helps the compiler optimise.

```c
/* Pointer to const data: cannot modify data through this pointer */
const uint8_t *p_data;

/* Const pointer: cannot change what it points to */
uint8_t * const p_reg;

/* Const pointer to const data */
const uint8_t * const p_rom_table;

/* Function parameters: input-only pointers must be const */
uint16_t Checksum_Calc(const uint8_t *data, uint32_t len);

/* Lookup tables in Flash: const at file scope */
static const uint16_t k_crc_table[256] = { /* ... */ };
```

---

## 16. Coding Style Conventions

### 16.1 BARR-C:2018 Key Rules (Selected)

| Rule | Description |
|---|---|
| **1.1a** | Use C99 or later (not C++); no language mixing |
| **1.2a** | All code shall be compiled with all warnings enabled; zero warnings tolerance |
| **3.1b** | Lines shall not exceed 80 characters |
| **3.2a** | No tabs in source code; use 4-space indentation |
| **4.1a** | Use `/* */` comments, not `//` (C90 compatibility where required) |
| **4.2a** | Never comment out code; use `#if 0 / #endif` |
| **5.1a** | All names shall be meaningful and fully spelled out (no abbreviations except industry-standard ones) |
| **5.2a** | No global variables; use module-level `static` with accessor functions |
| **6.1a** | Use `stdint.h` types; no bare `int`, `long`, `short` |
| **6.2a** | All variables shall be initialised before use |
| **7.1d** | Braces shall surround all `if/else/for/while` bodies, even single-statement |
| **8.1a** | All functions shall have a prototype visible at the call site |
| **8.2d** | Functions shall be no longer than 60 lines; single responsibility |
| **9.1a** | No dynamic memory allocation (malloc/free) |
| **9.2a** | No recursion |

### 16.2 NASA JPL C Coding Standard (Power of Ten) — Selected Rules

| Rule | Description |
|---|---|
| **1** | Restrict to simple control flow constructs; no goto, setjmp/longjmp, indirect recursion |
| **2** | All loops shall have a fixed upper bound verifiable by a static analysis tool |
| **3** | Do not use dynamic memory allocation after task initialisation |
| **4** | No function shall be longer than 60 lines of text fitting on a printed page |
| **5** | Assertion density: minimum 2 assertions per function on average |
| **6** | Data objects shall be declared at the smallest possible scope level |
| **7** | Return value of non-void functions shall always be checked |
| **8** | Use of the preprocessor shall be limited to file inclusions and simple macros |
| **9** | Pointer use shall be restricted: no more than one level of dereferencing per expression |
| **10** | All code must compile with all warnings enabled; zero warnings |

---

## 17. Code Documentation Standards

### 17.1 File Header

```c
/**
 * @file    can_driver.c
 * @brief   CAN/CAN-FD driver for TRAVEO T2G CYT4BB
 * @version 1.3.0
 * @date    2025-06-15
 *
 * @copyright (c) 2025 Acme Automotive GmbH
 *
 * ASIL classification: ASIL-B (ISO 26262-6)
 * MISRA C:2012 compliance: Full (AMD1); see deviation log DEV-CAN-001
 *
 * @req SYS-VSC-CAN-001, SYS-VSC-CAN-002, SYS-VSC-CAN-003
 */
```

### 17.2 Function Header

```c
/**
 * @brief   Transmit a CAN FD frame on the specified mailbox.
 *
 * @param[in]  mailbox   Mailbox index [0..MAX_MAILBOX-1]
 * @param[in]  frame     Pointer to the frame to transmit (not NULL)
 *
 * @return  E_OK         Frame accepted for transmission
 * @return  E_NOT_OK     Invalid parameter or mailbox busy
 *
 * @pre     CAN_Init() must have been called successfully.
 * @post    Frame is queued in hardware TX FIFO; interrupt will fire on completion.
 *
 * @req     SW-VSC-CAN-0003
 * @asil    ASIL-B
 *
 * @note    Not reentrant; protect with SchM_Enter_CAN_EXCLUSIVE_AREA if called
 *          from multiple tasks.
 */
Std_ReturnType CAN_Transmit(uint8_t mailbox, const CAN_Frame_t *frame);
```

---

## 18. Memory Sections and Linker Integration

In AUTOSAR and other structured embedded environments, variables and code are explicitly placed in named linker sections for:
- Initialisation ordering
- Cache configuration (code in fast-access SRAM bank)
- MPU/SMPU protection regions
- Non-volatile data persistence

```c
/* AUTOSAR memory section macros */
#define CAN_START_SEC_CODE
#include "MemMap.h"

Std_ReturnType CAN_Init(const CAN_ConfigType *cfg) {
    /* ... */
}

#define CAN_STOP_SEC_CODE
#include "MemMap.h"

#define CAN_START_SEC_VAR_CLEARED_8
#include "MemMap.h"
static uint8_t g_can_state;
#define CAN_STOP_SEC_VAR_CLEARED_8
#include "MemMap.h"

#define CAN_START_SEC_CONST_32
#include "MemMap.h"
static const uint32_t k_can_baud_prescaler = 4u;
#define CAN_STOP_SEC_CONST_32
#include "MemMap.h"
```

---

## 19. Reentrant and Thread-Safe Code

### 19.1 Reentrancy Requirements

| Code Type | Required? | Pattern |
|---|---|---|
| ISR handlers | Mandatory | No global mutable state; use local variables only |
| RTOS tasks sharing data | Mandatory | Mutex / semaphore / critical section |
| Library utility functions | Strongly recommended | No static local variables; pure functions |
| AUTOSAR runnables | AUTOSAR guarantees no concurrent invocation of same runnable | SchM exclusive areas for shared data |

### 19.2 Critical Section Pattern (Arm Cortex-M)

```c
/* Portable critical section using interrupt disable/enable */
typedef uint32_t CriticalSection_t;

static inline CriticalSection_t CritSec_Enter(void) {
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    __DSB();  /* Data Synchronisation Barrier */
    __ISB();  /* Instruction Synchronisation Barrier */
    return primask;
}

static inline void CritSec_Exit(CriticalSection_t saved) {
    __set_PRIMASK(saved);
    __ISB();
}

/* Usage */
CriticalSection_t cs = CritSec_Enter();
g_shared_var = new_value;
CritSec_Exit(cs);
```

---

## 20. AutoPragma Integration Map

| AutoPragma Process | Embedded C Guideline Application |
|---|---|
| SWE.1 (SwRS) | Verification method set to INSPECTION for coding-standard requirements; requirement text references specific guidelines (BARR-C, CERT-C, MISRA C) |
| SWE.3 (Detailed design) | Unit interface design follows Section 17 (documentation), Section 13 (function pointers), Section 15 (const correctness) |
| SWE.4 (Unit verification) | Static analysis items cover MISRA C compliance (Polyspace/LDRA), complexity (McCabe), documentation (Doxygen completeness); dynamic tests include volatile correctness, stack usage checks |
| SWE.6 (Qualification test) | Integration-level tests cover: volatile shared variable correctness (ISR interactions), watchdog service pattern, ring buffer bounds, integer wrap-around on boundary inputs |
| AUTOSAR BSW | MCAL and BSW code follows Section 18 (memory sections), AUTOSAR MISRA deviations process, SchM exclusive areas (Section 19) |
