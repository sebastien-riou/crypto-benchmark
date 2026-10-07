#pragma once

#define STM32PQC_small 1
#define STM32PQC_fast 2

#define STM32PQC_INDEX CAT(STM32PQC_,GOAL)

#if STM32PQC_INDEX == STM32PQC_small
  #define IMPL_NAME "stm32pqc-small"
  #define CMAC_ALGO CMOX_CMAC_AESSMALL_ALGO
#elif STM32PQC_INDEX == STM32PQC_fast
  #define IMPL_NAME "stm32pqc-fast"
  #define CMAC_ALGO CMOX_CMAC_AESFAST_ALGO
#else
  #error "STM32PQC AES-CMAC supports GOAL small or fast"
#endif

#include <stm32pqc/include/cmox_crypto.h>
#include <stddef.h>

//cmox_ll_init() and cmox_ll_deInit(): placeholders in common/stm32pqc_ll.c, an STM32 application defines them

static void aes_init(void){
  const cmox_init_retval_t r = cmox_initialize(NULL);
  if (CMOX_INIT_SUCCESS != r){
    throw_exception(ERROR_LIB_INIT | r);
  }
}

static uint32_t aes_cmac_verify(
  const void*const tag,
  const void*const message,
  size_t message_size,
  const void*const key
){
  const cmox_mac_retval_t r = cmox_mac_verify(CMAC_ALGO,
    message, message_size,
    key, AES_KEY_SIZE,
    NULL, 0, /* no custom data for CMAC */
    tag, AES_CMAC_TAG_SIZE);
  return r != CMOX_MAC_AUTH_SUCCESS;
}
