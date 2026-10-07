//placeholders for the low level hooks of the STM32 Cryptographic library, for builds that are not an STM32
//application, such as the build's own lbmk-test.elf (used for non_ct.report and the footprint). An STM32
//application defines both functions, see the hardware platform (crypto-benchmark-stm32u5).
//
//this file is compiled without LTO (cmake/stm32_cryptographic.cmake). Since V5, cmox_initialize() is inline and
//calls cmox_ll_init() directly. Seen by LTO, these weak placeholders would be inlined in place of the application's
//definitions, and the benchmark would hang in cmox_initialize() on the STM32 too.
#include <stm32pqc/include/cmox_crypto.h>

__attribute__((weak)) cmox_init_retval_t cmox_ll_init(void *pArg)
{
  (void)pArg;
  while(1);//we really need to execute on STM32 hardware, override this function in your STM32 application
  return CMOX_INIT_SUCCESS;
}

__attribute__((weak)) cmox_init_retval_t cmox_ll_deInit(void *pArg)
{
  (void)pArg;
  return CMOX_INIT_SUCCESS;
}
