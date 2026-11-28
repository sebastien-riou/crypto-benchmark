/* crypto-benchmark as a lean-bsp application: the board glue.
 *
 * benchmark.py builds the benchmark into build/<cpu>/libcrypto-benchmark.a (app.toml's [app.build]): the crypto
 * library, lean-benchmark and crypto-benchmark's core, which calls lean_benchmark()'s board hooks. This file is
 * those hooks on the lean-bsp contract (bsp_api.h), and app_main, which runs the benchmark once. It does what the
 * board repositories' main.c did (crypto-benchmark-stm32u5, -m5531 and -rp2350), the board set-up (clocks, caches,
 * the cycle counter) being the BSP's:
 *  - lean-benchmark's byte channel (com_tx, com_rx, common/lbmk.h) is UART 0;
 *  - LBMK_get_cpu_timestamp, LBMK_clear_caches and the heap count map onto bsp_cycle_count, bsp_clear_caches and
 *    bsp_heap_usage (contract 1.4: the same count as common/lbmk_heap.c);
 *  - interrupts are masked while lean_benchmark() runs, so that no handler runs in the timed code or pushes its
 *    frame on the measured stack. UART 0 works with them masked: the U5A5 and M5531 BSPs poll their UART, and the
 *    Pico 2's lets interrupts in for the duration of each call, its USB serial port moving bytes only from the USB
 *    interrupt (as crypto-benchmark-rp2350 did);
 *  - the info fields: the platform name (CB_HW_PLATFORM, which benchmark.py passes with `lbsp build --define`), the
 *    clock, and the cache state where the old firmware reported it.
 * printf is not used: the BSP sends it to UART 0 as it is, and after the handshake every byte on UART 0 must be
 * lean-com framed. LBMK_println frames it.
 *
 * Experiments, off unless defined (benchmark.py passes CB_LBSP_DEFINES="K=V K2=V2" to `lbsp build --define`), each
 * described where it is defined: CB_XIP_COUNT (RP2350 XIP cache misses), CB_PMU_EV0/CB_PMU_EV1 (M5531 PMU events),
 * CB_REG_SNAPSHOT (M5531 configuration registers), CB_LAYOUT_PAD and CB_TEXT_PAD (the benchmarked code moved). */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "bsp_api.h"
#include "lean-benchmark.h"

#ifndef CB_HW_PLATFORM
#error "CB_HW_PLATFORM: the platform name the results carry, e.g. \"pico2-cortex-m33\" (benchmark.py passes it)"
#endif

/* the archive's entry point (lib*-lbmk/source/core.c) */
void lean_benchmark(unsigned int ninfo, const char *info[], bool run_forever);

/* ---- lean-benchmark's byte channel (common/lbmk.h): UART 0 ---- */

void com_tx(const void *const buf, unsigned int size) { bsp_uart_tx(0, buf, size); }

/* lean-com waits for what it asks for, as the old firmware did: until the host sends it */
void com_rx(void *const buf, unsigned int size) {
    uint8_t *p = buf;
    while (size) {
        const size_t n = bsp_uart_rx(0, p, size);
        p += n;
        size -= (unsigned int)n;
    }
}

/* ---- lean-benchmark's board hooks ---- */

#if defined(CB_XIP_COUNT)
/* An experiment (CB_LBSP_DEFINES="CB_XIP_COUNT=1"): the RP2350's XIP cache accesses and misses per timed call.
 * LBMK_timeit takes a timestamp before and after each timed call. The first clears the XIP cache counters, then reads
 * the cycle counter; the second reads the cycle counter, then latches the counters: the counting stays outside the
 * timed window. LBMK_get_heap_usage, read after each trial's operation, returns accesses << 32 | misses of the last
 * timed call (the operation's) in place of the heap. */
#if !defined(LEAN_BSP_MCU_IS_RP2350)
#error "CB_XIP_COUNT: RP2350 only"
#endif
#define XIP_CTR_HIT (*(volatile uint32_t *)0x400c800cu) /* XIP_CTRL_BASE + XIP_CTR_HIT_OFFSET; any write clears */
#define XIP_CTR_ACC (*(volatile uint32_t *)0x400c8010u) /* XIP_CTRL_BASE + XIP_CTR_ACC_OFFSET */
static bool xip_timing;
static uint32_t xip_hit, xip_acc;

uint64_t LBMK_get_cpu_timestamp() {
    if (!xip_timing) {
        XIP_CTR_HIT = 0;
        XIP_CTR_ACC = 0;
        xip_timing = true;
        return bsp_cycle_count();
    }
    const uint32_t cycles = bsp_cycle_count();
    xip_hit = XIP_CTR_HIT;
    xip_acc = XIP_CTR_ACC;
    xip_timing = false;
    return cycles;
}
#elif defined(CB_PMU_EV0)
/* An experiment (CB_LBSP_DEFINES="CB_PMU_EV0=<event> CB_PMU_EV1=<event>"): two Cortex-M55 PMU events per timed call
 * (e.g. 0x0001 L1I_CACHE_REFILL, 0x0003 L1D_CACHE_REFILL), each on a chained pair of 16-bit counters (0 and 1, 2 and
 * 3; event 0x001E CHAIN counts the even counter's overflows). As CB_XIP_COUNT: the first timestamp of a timed call
 * starts the counters from 0, then reads the cycle counter; the second reads the cycle counter, then stops and latches
 * them. LBMK_get_heap_usage returns EV1 << 32 | EV0 of the last timed call in place of the heap. */
#if !defined(LEAN_BSP_MCU_IS_M5531)
#error "CB_PMU_EV0: M5531 only"
#endif
#if !defined(CB_PMU_EV1)
#error "CB_PMU_EV0 goes with CB_PMU_EV1, the second event"
#endif
#define CB_PMU_EVCNTR(n) (*(volatile uint32_t *)(0xE0003000u + 4u * (n)))
#define CB_PMU_EVTYPER(n) (*(volatile uint32_t *)(0xE0003400u + 4u * (n)))
#define CB_PMU_CNTENSET (*(volatile uint32_t *)0xE0003C00u)
#define CB_PMU_CNTENCLR (*(volatile uint32_t *)0xE0003C20u)
#define CB_PMU_OVSCLR (*(volatile uint32_t *)0xE0003C80u)
#define CB_PMU_CTRL (*(volatile uint32_t *)0xE0003E04u)
static bool cb_pmu_timing;
static uint32_t cb_pmu_ev[2];
static void cb_pmu_start(void) {
    CB_PMU_CNTENCLR = 0xFu;
    CB_PMU_EVTYPER(0) = CB_PMU_EV0;
    CB_PMU_EVTYPER(1) = 0x001Eu;
    CB_PMU_EVTYPER(2) = CB_PMU_EV1;
    CB_PMU_EVTYPER(3) = 0x001Eu;
    CB_PMU_CTRL |= 1u | 2u; /* E: enabled; P: the event counters to 0 (not the cycle counter) */
    CB_PMU_OVSCLR = 0xFu;
    CB_PMU_CNTENSET = 0xFu;
}
static void cb_pmu_stop(void) {
    CB_PMU_CNTENCLR = 0xFu;
    cb_pmu_ev[0] = (CB_PMU_EVCNTR(1) & 0xFFFFu) << 16 | (CB_PMU_EVCNTR(0) & 0xFFFFu);
    cb_pmu_ev[1] = (CB_PMU_EVCNTR(3) & 0xFFFFu) << 16 | (CB_PMU_EVCNTR(2) & 0xFFFFu);
}
uint64_t LBMK_get_cpu_timestamp() {
    if (!cb_pmu_timing) {
        cb_pmu_start();
        cb_pmu_timing = true;
        return bsp_cycle_count();
    }
    const uint32_t cycles = bsp_cycle_count();
    cb_pmu_stop();
    cb_pmu_timing = false;
    return cycles;
}
#else
/* 32 bits on every board: lean-benchmark keeps the difference of two readings in 32 bits */
uint64_t LBMK_get_cpu_timestamp() { return bsp_cycle_count(); }
#endif

void LBMK_clear_caches() { bsp_clear_caches(); }

void LBMK_init_heap_usage() { bsp_heap_usage_reset(); }

#if defined(CB_XIP_COUNT)
uint64_t LBMK_get_heap_usage() { return (uint64_t)xip_acc << 32 | (uint32_t)(xip_acc - xip_hit); }
#elif defined(CB_PMU_EV0)
uint64_t LBMK_get_heap_usage() { return (uint64_t)cb_pmu_ev[1] << 32 | cb_pmu_ev[0]; }
#else
uint64_t LBMK_get_heap_usage() {
    const size_t used = bsp_heap_usage();
    return used == SIZE_MAX ? UINT64_MAX : used;  /* unknown: common/lbmk_heap.c's UINT64_MAX */
}
#endif

/* ---- interrupts ---- */

static uint32_t irq_save_disable(void) {
#if defined(__arm__)
    uint32_t primask;
    __asm volatile("mrs %0, primask\n\tcpsid i" : "=r"(primask) : : "memory");
    return primask;
#elif defined(__riscv)
    uint32_t mstatus;
    __asm volatile("csrrci %0, mstatus, 8" : "=r"(mstatus) : : "memory");  /* mstatus.MIE */
    return mstatus & 8u;
#else
    return 0;  /* a native process: nothing to mask */
#endif
}

static void irq_restore(uint32_t saved) {
#if defined(__arm__)
    __asm volatile("msr primask, %0" : : "r"(saved) : "memory");
#elif defined(__riscv)
    if (saved) __asm volatile("csrsi mstatus, 8" : : : "memory");
#else
    (void)saved;
#endif
}

/* ---- the info fields ---- */

#if defined(LEAN_BSP_MCU_IS_STM32U5)
/* ST's ICACHE and DCACHE1, CR.EN, at their non-secure addresses (the BSP runs with TrustZone off). The BSP enables
 * both; crypto-benchmark-stm32u5 reported them. */
#define CACHE_INFO 1
static bool icache_enabled(void) { return *(volatile uint32_t *)0x40030400u & 1u; }
static bool dcache_enabled(void) { return *(volatile uint32_t *)0x40031400u & 1u; }
#elif defined(LEAN_BSP_MCU_IS_M5531)
/* the Cortex-M55's own caches: SCB->CCR.IC and .DC; crypto-benchmark-m5531 reported them */
#define CACHE_INFO 1
static bool icache_enabled(void) { return *(volatile uint32_t *)0xE000ED14u & (1u << 17); }
static bool dcache_enabled(void) { return *(volatile uint32_t *)0xE000ED14u & (1u << 16); }
#endif

/* a counter that does not count makes every figure 0: say so rather than let such figures pass */
static bool cycle_counter_alive(void) {
    const uint32_t start = bsp_cycle_count();
    for (volatile unsigned int i = 0; i < 64; i++) {
    }
    return bsp_cycle_count() != start;
}

#if defined(CB_REG_SNAPSHOT)
/* An experiment (CB_LBSP_DEFINES="CB_REG_SNAPSHOT=1"): the Cortex-M55's configuration as lean_benchmark() starts,
 * one "REG <name> = <value>" line each, to compare two firmwares' set-up. Reading DHCSR clears its sticky bits. */
#if !defined(LEAN_BSP_MCU_IS_M5531)
#error "CB_REG_SNAPSHOT: M5531 only"
#endif
static void cb_reg_snapshot(void) {
    static const struct { const char *name; uint32_t addr; } regs[] = {
        {"SCB->CPUID", 0xE000ED00u},         {"SCB->VTOR", 0xE000ED08u},
        {"SCB->AIRCR", 0xE000ED0Cu},         {"SCB->SCR", 0xE000ED10u},
        {"SCB->CCR", 0xE000ED14u},           {"SCB->SHCSR", 0xE000ED24u},
        {"SCB->CPACR", 0xE000ED88u},         {"SCB->NSACR", 0xE000ED8Cu},
        {"ICB->ACTLR", 0xE000E008u},         {"MEMSYSCTL->MSCR", 0xE001E000u},
        {"MEMSYSCTL->PFCR", 0xE001E004u},    {"MEMSYSCTL->ITCMCR", 0xE001E010u},
        {"MEMSYSCTL->DTCMCR", 0xE001E014u},  {"MEMSYSCTL->PAHBCR", 0xE001E018u},
        {"FPU->FPCCR", 0xE000EF34u},         {"DCB->DHCSR", 0xE000EDF0u},
        {"DCB->DEMCR", 0xE000EDFCu},         {"DWT->CTRL", 0xE0001000u},
        {"PMU->CTRL", 0xE0003E04u},          {"PMU->CNTENSET", 0xE0003C00u},
        {"MPU->CTRL", 0xE000ED94u},          {"SAU->CTRL", 0xE000EDD0u},
        {"PWRMODCTL->CPDLPSTATE", 0xE001E300u}, {"PWRMODCTL->DPDLPSTATE", 0xE001E304u},
        {"SysTick->CTRL", 0xE000E010u},      {"FMC->CYCCTL", 0x4004404Cu},
    };
    char line[64];
    for (unsigned int i = 0; i < sizeof regs / sizeof regs[0]; i++) {
        snprintf(line, sizeof line, "REG %s = 0x%08lx", regs[i].name,
                 (unsigned long)*(volatile uint32_t *)regs[i].addr);
        LBMK_println(line);
    }
    uint32_t primask, basepri, faultmask, control, msp;
    __asm volatile("mrs %0, primask" : "=r"(primask));
    __asm volatile("mrs %0, basepri" : "=r"(basepri));
    __asm volatile("mrs %0, faultmask" : "=r"(faultmask));
    __asm volatile("mrs %0, control" : "=r"(control));
    __asm volatile("mrs %0, msp" : "=r"(msp));
    snprintf(line, sizeof line, "REG PRIMASK = 0x%08lx", (unsigned long)primask);
    LBMK_println(line);
    snprintf(line, sizeof line, "REG BASEPRI = 0x%08lx", (unsigned long)basepri);
    LBMK_println(line);
    snprintf(line, sizeof line, "REG FAULTMASK = 0x%08lx", (unsigned long)faultmask);
    LBMK_println(line);
    snprintf(line, sizeof line, "REG CONTROL = 0x%08lx", (unsigned long)control);
    LBMK_println(line);
    snprintf(line, sizeof line, "REG MSP = 0x%08lx", (unsigned long)msp);
    LBMK_println(line);
}
#endif

int app_main(void) {
    LBMK_init_leancom();  /* waits for the host's handshake */
    LBMK_println("crypto-benchmark on " CB_HW_PLATFORM);
    char frequency_mhz[12];
    snprintf(frequency_mhz, sizeof frequency_mhz, "%lu", (unsigned long)(bsp_cpu_freq_hz() / 1000000u));
    const char *hw_info[] = {
        "hw_platform", CB_HW_PLATFORM,
        "frequency_mhz", frequency_mhz,
#if defined(CACHE_INFO)
        "ICACHE", icache_enabled() ? "enabled" : "disabled",
        "DCACHE", dcache_enabled() ? "enabled" : "disabled",
#endif
    };
    if (!cycle_counter_alive()) LBMK_println("WARNING: the cycle counter does not count, every figure will read 0");
#if defined(CB_LAYOUT_PAD)
    static volatile bool never;
    void cb_layout_pad(void);
    if (never) cb_layout_pad();
#endif
#if defined(CB_TEXT_PAD)
    static volatile bool never_t;
    void cb_text_pad(void);
    if (never_t) cb_text_pad();
#endif
    const uint32_t saved = irq_save_disable();
#if defined(CB_REG_SNAPSHOT)
    cb_reg_snapshot();
#endif
    lean_benchmark(sizeof hw_info / sizeof hw_info[0], hw_info, false);
    irq_restore(saved);
    return 0;  /* the BSP then parks the CPU: a benchmark that has printed its results must not start over */
}

/* ---- faults: the BSP calls this from its fault handlers, then stops ----
 * The report goes through lean-benchmark's print, lean-com framed once the handshake has run, raw before, as
 * crypto-benchmark-m5531's HardFault report did. Formatted here, without printf: the stack may be what failed. */

static char *put_str(char *p, const char *s) {
    while (*s) *p++ = *s++;
    return p;
}

static char *put_hex(char *p, uint32_t v) {
    static const char hex[] = "0123456789ABCDEF";
    *p++ = '0';
    *p++ = 'x';
    for (int shift = 28; shift >= 0; shift -= 4) *p++ = hex[(v >> shift) & 0xFu];
    return p;
}

void app_on_fault(uint32_t reason, uintptr_t pc) {
    char msg[128];  /* 93 bytes used */
    char *p = put_str(msg, "\r\nEXCEPTION: fault, reason=");
    p = put_hex(p, reason);
    p = put_str(p, " PC=");
    p = put_hex(p, (uint32_t)pc);
    p = put_str(p, "\r\n  halted, any results above are invalid");
    *p = 0;
    LBMK_println(msg);
}

#define CB_STR_(x) #x
#define CB_STR(x) CB_STR_(x)
#if defined(CB_LAYOUT_PAD)
/* An experiment (CB_LBSP_DEFINES="CB_LAYOUT_PAD=<bytes>"): padding between the glue's code and the code linked after
 * it (the archive), which moves the benchmarked code without changing one instruction of it. Last in this file, so
 * last of the glue's code. app_main refers to it (never calls it) so that --gc-sections keeps it; that reference is
 * there for every value, 0 included, so that only the padding differs between two values. */
__attribute__((naked, noinline)) void cb_layout_pad(void) { __asm volatile(".space " CB_STR(CB_LAYOUT_PAD)); }
#endif
#if defined(CB_TEXT_PAD)
/* An experiment (CB_LBSP_DEFINES="CB_TEXT_PAD=<bytes>"): the same padding in the plain .text input section, for a
 * board where the glue links after the archive (the U5A5): linker scripts that take *(.text) before *(.text*) put it
 * among the LTO output, ahead of the archive's non-LTO objects. app_main refers to it as to cb_layout_pad. */
__attribute__((naked, noinline, section(".text"))) void cb_text_pad(void) {
    __asm volatile(".space " CB_STR(CB_TEXT_PAD));
}
#endif
