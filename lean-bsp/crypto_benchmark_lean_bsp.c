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
 * lean-com framed. LBMK_println frames it. */
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

/* 32 bits on every board: lean-benchmark keeps the difference of two readings in 32 bits */
uint64_t LBMK_get_cpu_timestamp() { return bsp_cycle_count(); }

void LBMK_clear_caches() { bsp_clear_caches(); }

void LBMK_init_heap_usage() { bsp_heap_usage_reset(); }

uint64_t LBMK_get_heap_usage() {
    const size_t used = bsp_heap_usage();
    return used == SIZE_MAX ? UINT64_MAX : used;  /* unknown: common/lbmk_heap.c's UINT64_MAX */
}

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
    const uint32_t saved = irq_save_disable();
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
