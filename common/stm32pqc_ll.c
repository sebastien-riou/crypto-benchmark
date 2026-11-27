//the low level hooks of the STM32 Cryptographic library. ST's library needs the CRC unit's clock running before it
//does anything: cmox_ll_init() switches it on for the STM32 family that benchmark.py names when it builds the
//library (STM32PQC_FAMILY, cmake/stm32_cryptographic.cmake). Without a family, as in a footprint-only build or the
//non-CT report's build, cmox_ll_init() is a placeholder that never returns: the library runs only on an STM32.
//
//the definitions are weak, so an application can still define its own.
//this file is compiled without LTO (cmake/stm32_cryptographic.cmake). Since V5, cmox_initialize() is inline and
//calls cmox_ll_init() directly. Seen by LTO, these weak definitions would be inlined in place of an application's
//own definitions.
#include <stdint.h>
#include <stm32pqc/include/cmox_crypto.h>

#if defined(STM32PQC_FAMILY_U5)
//STM32U5: RCC at 0x46020C00, its non-secure alias (TrustZone off or non-secure). The CRC unit is on AHB1, bit 12 of
//both the reset register (CRCRST) and the clock enable register (CRCEN).
#define LL_RCC_AHB1RSTR (*(volatile uint32_t *)0x46020C60u)
#define LL_RCC_AHB1ENR  (*(volatile uint32_t *)0x46020C88u)
#define LL_RCC_AHB1_CRC (1u << 12)
#endif

__attribute__((weak)) cmox_init_retval_t cmox_ll_init(void *pArg)
{
  (void)pArg;
#if defined(STM32PQC_FAMILY_U5)
  //what __HAL_RCC_CRC_RELEASE_RESET() and __HAL_RCC_CRC_CLK_ENABLE() do
  LL_RCC_AHB1RSTR &= ~LL_RCC_AHB1_CRC;
  LL_RCC_AHB1ENR |= LL_RCC_AHB1_CRC;
  (void)LL_RCC_AHB1ENR;//read back: a delay after enabling a peripheral clock
  return CMOX_INIT_SUCCESS;
#else
  while(1);//no STM32 family named: we really need to execute on STM32 hardware (see the head of this file)
  return CMOX_INIT_SUCCESS;
#endif
}

__attribute__((weak)) cmox_init_retval_t cmox_ll_deInit(void *pArg)
{
  (void)pArg;
  //the CRC unit stays on, other software may use it
  return CMOX_INIT_SUCCESS;
}
