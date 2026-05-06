#pragma once


#define STM32PQC_small 1
#define STM32PQC_balanced 2

#define STM32PQC_INDEX CAT(STM32PQC_,GOAL)

#if STM32PQC_INDEX == STM32PQC_small
  #define IMPL_NAME "stm32pqc-small"
  #define LOWRAM
#endif

#if STM32PQC_INDEX == STM32PQC_balanced
  #define IMPL_NAME "stm32pqc-balanced"
#endif

#include <stm32pqc/include/cmox_crypto.h>
#include <stm32pqc/include/pqc/cmox_pqc_dsa.h>
#include <stddef.h>

static cmox_pqc_dsa_verify_algo_t pset_to_verify_algo(unsigned int pset){
  switch(pset){
    case 44: return CMOX_PQC_ML_DSA_44_VERIFY_ALGO;break;
    case 65: return CMOX_PQC_ML_DSA_65_VERIFY_ALGO;break;
    case 87: return CMOX_PQC_ML_DSA_87_VERIFY_ALGO;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}

#ifdef LOWRAM
  //#define IMPL_NAME "stm32pqc-lowram"
  #if PSET == 44
    static uint8_t membuf[11340];
  #endif
  #if PSET == 65
    static uint8_t membuf[15436];
  #endif
  #if PSET == 87
    static uint8_t membuf[19532];
  #endif
  static cmox_pqc_dsa_sign_algo_t pset_to_sign_algo(unsigned int pset){
    switch(pset){
      case 44: return CMOX_PQC_ML_DSA_44_DET_SIGN_LOWRAM_ALGO;break;
      case 65: return CMOX_PQC_ML_DSA_65_DET_SIGN_LOWRAM_ALGO;break;
      case 87: return CMOX_PQC_ML_DSA_87_DET_SIGN_LOWRAM_ALGO;break;
      default: throw_exception(ERROR_PSET);
    }
    __builtin_unreachable();
  }
#else
  //#define IMPL_NAME "stm32pqc-fast"
  #if PSET == 44
    static uint8_t membuf[30796];
  #endif
  #if PSET == 65
    static uint8_t membuf[43084];
  #endif
  #if PSET == 87
    static uint8_t membuf[57420];
  #endif
  static cmox_pqc_dsa_sign_algo_t pset_to_sign_algo(unsigned int pset){
    switch(pset){
      case 44: return CMOX_PQC_ML_DSA_44_DET_SIGN_ALGO;break;
      case 65: return CMOX_PQC_ML_DSA_65_DET_SIGN_ALGO;break;
      case 87: return CMOX_PQC_ML_DSA_87_DET_SIGN_ALGO;break;
      default: throw_exception(ERROR_PSET);
    }
    __builtin_unreachable();
  }
#endif

static cmox_pqc_dsa_keygen_algo_t pset_to_keygen_algo(unsigned int pset){
  switch(pset){
    case 44: return CMOX_PQC_ML_DSA_44_KEYGEN_ALGO;break;
    case 65: return CMOX_PQC_ML_DSA_65_KEYGEN_ALGO;break;
    case 87: return CMOX_PQC_ML_DSA_87_KEYGEN_ALGO;break;
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
  /* Ensure CRC is enabled for cryptographic processing */
  //__HAL_RCC_CRC_RELEASE_RESET();
  //__HAL_RCC_CRC_CLK_ENABLE();
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
  /* Do not turn off CRC to avoid side effect on other SW parts using it */
  return CMOX_INIT_SUCCESS;
}

static void dsa_init(){
  const cmox_pqc_retval_t r = cmox_initialize(NULL);
  if (CMOX_INIT_SUCCESS != r){
    throw_exception(ERROR_LIB_INIT | r);
  }
  cmox_pqc_dsa_construct(&Pqc_Ctx, CMOX_PQC_LLENGINES_DEFAULT, membuf, sizeof(membuf));
}

static uint8_t stm_private_key[DSA_PRIVATE_KEY_SIZE]={0};
static uint8_t stm_public_key[DSA_PUBLIC_KEY_SIZE]={0};

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  dsa_init();
  cmox_pqc_dsa_keygen_algo_t algo = pset_to_keygen_algo(pset);
  size_t private_key_size = DSA_PRIVATE_KEY_SIZE;
  size_t public_key_size = DSA_PUBLIC_KEY_SIZE;
  cmox_pqc_retval_t r = cmox_pqc_dsa_keyGen(&Pqc_Ctx,                          /* Initialized context */
              algo,    /* Use ML-DSA-44 key generation algorithm */
              seed, 32,  /* Random seed (and its length) to generate keys */
              stm_private_key,                       /* Buffer that will contain the private key */
              &private_key_size,               /* Variable that will contain private key length */
              stm_public_key,                        /* Buffer that will contain the public key */
              &public_key_size);               /* Variable that will contain public key length */

  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}
static void dsa_get_private_key(void* private_key){
  memcpy(private_key, stm_private_key, DSA_PRIVATE_KEY_SIZE);
}
static void dsa_get_public_key(void* public_key){
  memcpy(public_key, stm_public_key, DSA_PUBLIC_KEY_SIZE);
}

static uint32_t dsa_verify(
  const unsigned int pset,
  const void*const signature,
  const void*const message,
  size_t message_size){
  uint8_t header[CMOX_PQC_DSA_HEADER_MAX_LENGTH];
  size_t header_size = sizeof(header);
  cmox_pqc_retval_t r = cmox_pqc_dsa_prepareHeader(&Pqc_Ctx,                         /* Initialized PQC context */
                          NULL, 0, /* Signing context, that is a personalization binary string */
                          CMOX_PQC_DSA_STANDARD,            /* ML-DSA standard, not the pre-hashed version */
                          header,                           /* Buffer that will contain the signing header */
                          &header_size);                  /* Variable that will contain the header length */
  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_SIGN|ERROR_LIB_INIT|r);
  }
  cmox_pqc_dsa_verify_algo_t algo = pset_to_verify_algo(pset);
  uint32_t fault_check = CMOX_PQC_AUTH_FAIL;
  r = cmox_pqc_dsa_verify(&Pqc_Ctx,                              /* Initialized context */
        algo, /* Use ML-DSA-44 key signature verification algorithm */
        stm_public_key, DSA_PUBLIC_KEY_SIZE,        /* Buffer containing the public key, and its length */
        header, header_size,                 /* Buffer containing the header, and its length */
        message, message_size,              /* Buffer containing the message, and its length */
        signature, DSA_SIG_SIZE,          /* Buffer containing the signature, and its length */
        &fault_check);                         /* Variable that will contain an additional return value
                                                  to check, in order to be protected against simple
                                                  fault attacks */
  
  if (r == CMOX_PQC_AUTH_SUCCESS){
    if (fault_check == CMOX_PQC_AUTH_SUCCESS){
      return 0;//success
    }
  }
  return 1;//sig mismatch
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  
  uint8_t header[CMOX_PQC_DSA_HEADER_MAX_LENGTH];
  size_t header_size = sizeof(header);
  cmox_pqc_retval_t r = cmox_pqc_dsa_prepareHeader(&Pqc_Ctx,                         /* Initialized PQC context */
                          NULL, 0, /* Signing context, that is a personalization binary string */
                          CMOX_PQC_DSA_STANDARD,            /* ML-DSA standard, not the pre-hashed version */
                          header,                           /* Buffer that will contain the signing header */
                          &header_size);                  /* Variable that will contain the header length */
  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_SIGN|ERROR_LIB_INIT|r);
  }
  cmox_pqc_dsa_sign_algo_t algo = pset_to_sign_algo(pset);
  size_t signature_size = DSA_SIG_SIZE;
  r = cmox_pqc_dsa_sign(&Pqc_Ctx,                            /* Initialized context */
    		algo, 
        NULL, 0,          /* Random seed (and its length) to sign the message */
        stm_private_key, DSA_PRIVATE_KEY_SIZE,    /* Buffer containing the private key, and its length */
        header, header_size,               /* Buffer containing the header, and its length */
        message, message_size,            /* Buffer containing the message, and its length */
        signature,                           /* Buffer that will contain the signature */
        &signature_size);                  /* Variable that will contain the signature length */
  if (r != CMOX_PQC_SUCCESS) {
    throw_exception(ERROR_SIGN|r);
  }
}

