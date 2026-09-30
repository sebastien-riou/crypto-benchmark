#pragma once

//the STM32 PQC library has a single ML-KEM implementation
#define STM32PQC_balanced 1

#define STM32PQC_INDEX CAT(STM32PQC_,GOAL)

#if STM32PQC_INDEX == STM32PQC_balanced
  #define IMPL_NAME "stm32pqc-balanced"
#else
  #error "STM32PQC ML-KEM supports GOAL balanced only"
#endif

#include <stm32pqc/include/cmox_crypto.h>
#include <stm32pqc/include/pqc/cmox_pqc_kem.h>
#include <stddef.h>

//working buffer given to the library.
//ST does not document the size ML-KEM needs, so the default is an upper bound: it inflates the static RAM footprint.
//the peak usage of each operation is reported as extra data "membuf peak" (32 bit little endian),
//set STM32PQC_MLKEM_MEMBUF_SIZE to the maximum reported value to get an accurate footprint.
//if the buffer is too small, operations fail with CMOX_PQC_ERR_MEMORY_FAIL (0x0009000C).
#ifndef STM32PQC_MLKEM_MEMBUF_SIZE
  #define STM32PQC_MLKEM_MEMBUF_SIZE (32*1024)
#endif
static uint8_t membuf[STM32PQC_MLKEM_MEMBUF_SIZE];

#define KEM_NEXTRA_DATA 1
static uint32_t membuf_peak;
static void kem_extra_data(tlv_t*extra_data_info){
  extra_data_info[0].tag = "membuf peak";
  extra_data_info[0].length = sizeof(membuf_peak);
  extra_data_info[0].value = (uint8_t*)&membuf_peak;
}

static cmox_pqc_kem_keygen_algo_t pset_to_keygen_algo(unsigned int pset){
  switch(pset){
    case 512: return CMOX_PQC_ML_KEM_512_KEYGEN_ALGO;break;
    case 768: return CMOX_PQC_ML_KEM_768_KEYGEN_ALGO;break;
    case 1024: return CMOX_PQC_ML_KEM_1024_KEYGEN_ALGO;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}
static cmox_pqc_kem_enc_algo_t pset_to_enc_algo(unsigned int pset){
  switch(pset){
    case 512: return CMOX_PQC_ML_KEM_512_ENC_ALGO;break;
    case 768: return CMOX_PQC_ML_KEM_768_ENC_ALGO;break;
    case 1024: return CMOX_PQC_ML_KEM_1024_ENC_ALGO;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}
static cmox_pqc_kem_dec_algo_t pset_to_dec_algo(unsigned int pset){
  switch(pset){
    case 512: return CMOX_PQC_ML_KEM_512_DEC_ALGO;break;
    case 768: return CMOX_PQC_ML_KEM_768_DEC_ALGO;break;
    case 1024: return CMOX_PQC_ML_KEM_1024_DEC_ALGO;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}

static cmox_pqc_handle_t Pqc_Ctx;

/**
  * @brief          CMOX library low level initialization
  * @param          pArg User defined parameter that is transmitted from initialize service
  * @retval         Initialization status: @ref CMOX_INIT_SUCCESS / @ref CMOX_INIT_FAIL
  */
__attribute__((weak)) cmox_init_retval_t cmox_ll_init(void *pArg)
{
  (void)pArg;
  while(1);//we really need to execute on STM32 hardware, override this function in your STM32 application
  return CMOX_INIT_SUCCESS;
}

/**
  * @brief          CMOX library low level de-initialization
  * @param          pArg User defined parameter that is transmitted from finalize service
  * @retval         De-initialization status: @ref CMOX_INIT_SUCCESS / @ref CMOX_INIT_FAIL
  */
__attribute__((weak)) cmox_init_retval_t cmox_ll_deInit(void *pArg)
{
  (void)pArg;
  return CMOX_INIT_SUCCESS;
}

static void kem_init(void){
  const cmox_init_retval_t r = cmox_initialize(NULL);
  if (CMOX_INIT_SUCCESS != r){
    throw_exception(ERROR_LIB_INIT | r);
  }
}

//each operation constructs and cleans the context, as an application would.
//the cleanup wipes the working buffer, which holds secrets.
static void kem_construct(void){
  cmox_pqc_kem_construct(&Pqc_Ctx, CMOX_PQC_LLENGINES_DEFAULT, membuf, sizeof(membuf));
}
static void kem_cleanup(void){
  membuf_peak = Pqc_Ctx.membuf_str.MaxMemUsed;
  cmox_pqc_kem_cleanup(&Pqc_Ctx);
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  size_t secret_key_size = KEM_SECRET_KEY_SIZE;
  size_t public_key_size = KEM_PUBLIC_KEY_SIZE;
  kem_construct();
  const cmox_pqc_retval_t r = cmox_pqc_kem_keyGen(&Pqc_Ctx,
    pset_to_keygen_algo(PSET),
    seed, MLKEM_KEYGEN_SEEDBYTES, /* d || z */
    secret_key, &secret_key_size,
    public_key, &public_key_size);
  kem_cleanup();
  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  size_t ciphertext_size = KEM_CIPHERTEXT_SIZE;
  size_t shared_secret_size = KEM_SHARED_SECRET_SIZE;
  kem_construct();
  const cmox_pqc_retval_t r = cmox_pqc_kem_encapsulate(&Pqc_Ctx,
    pset_to_enc_algo(PSET),
    seed, MLKEM_ENCAPS_SEEDBYTES, /* m */
    public_key, KEM_PUBLIC_KEY_SIZE,
    ciphertext, &ciphertext_size,
    shared_secret, &shared_secret_size);
  kem_cleanup();
  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_ENCAPS|r);
  }
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  size_t shared_secret_size = KEM_SHARED_SECRET_SIZE;
  kem_construct();
  const cmox_pqc_retval_t r = cmox_pqc_kem_decapsulate(&Pqc_Ctx,
    pset_to_dec_algo(PSET),
    secret_key, KEM_SECRET_KEY_SIZE,
    ciphertext, KEM_CIPHERTEXT_SIZE,
    shared_secret, &shared_secret_size);
  kem_cleanup();
  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_DECAPS|r);
  }
}
