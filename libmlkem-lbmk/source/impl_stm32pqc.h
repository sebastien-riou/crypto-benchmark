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

//working buffer given to the library, STM32PQC_MLKEM_MEMBUF_SIZE bytes.
//ST does not document the size ML-KEM needs, and the library does not count what its ML-KEM code uses: MaxMemUsed of
//the context stays 0 (none of its ML-KEM objects calls cmox_membuf_alloc, the function that updates it). So the use is
//measured: the buffer is filled with a pattern, and after each operation, in post_exec (outside the timed code), the
//highest word that differs from the pattern gives the peak, reported as extra data "membuf peak" (bytes, 32 bit little
//endian); the buffer is then filled again for the next operation.
//On the STM32U5A5 (2026-11-23, buffer of 32 KiB) the peak was 0 for every operation and parameter set: the ML-KEM code
//does not use the buffer. Hence a default of one word, so that the reported static RAM is the library's own.
//An operation that changes the last word of the buffer may have needed more: the run then stops with error
//ERROR_MEMBUF_FULL (0xFFFB0000). Rebuild with a larger -DSTM32PQC_MLKEM_MEMBUF_SIZE=<bytes>, e.g. 32768, and set it to
//the largest peak reported. A buffer the library finds too small makes an operation fail with
//CMOX_PQC_ERR_MEMORY_FAIL (0x0009000C).
#ifndef STM32PQC_MLKEM_MEMBUF_SIZE
  #define STM32PQC_MLKEM_MEMBUF_SIZE 4
#endif
#define ERROR_MEMBUF_FULL 0xFFFB0000
#define MEMBUF_WORDS ((STM32PQC_MLKEM_MEMBUF_SIZE+3)/4)
#define MEMBUF_PATTERN 0xA5C3E10Fu
static uint32_t membuf[MEMBUF_WORDS];

static void membuf_fill(unsigned int nwords){
  for(unsigned int i=0;i<nwords;i++){
    membuf[i] = MEMBUF_PATTERN;
  }
}

#define KEM_NEXTRA_DATA 1
static uint32_t membuf_peak;
static void kem_extra_data(tlv_t*extra_data_info){
  //the words the last operation changed, from the start of the buffer to the highest one
  unsigned int used = MEMBUF_WORDS;
  while(used > 0 && membuf[used-1] == MEMBUF_PATTERN){
    used--;
  }
  if(used == MEMBUF_WORDS){
    throw_exception(ERROR_MEMBUF_FULL);
  }
  membuf_peak = used*4;
  membuf_fill(used);
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

//cmox_ll_init() and cmox_ll_deInit(): placeholders in common/stm32pqc_ll.c, an STM32 application defines them

static void kem_init(void){
  const cmox_init_retval_t r = cmox_initialize(NULL);
  if (CMOX_INIT_SUCCESS != r){
    throw_exception(ERROR_LIB_INIT | r);
  }
  membuf_fill(MEMBUF_WORDS);
}

//each operation constructs and cleans the context, as an application would.
//cmox_pqc_kem_cleanup clears the context (24 bytes), not the working buffer.
static void kem_construct(void){
  cmox_pqc_kem_construct(&Pqc_Ctx, CMOX_PQC_LLENGINES_DEFAULT, (uint8_t*)membuf, STM32PQC_MLKEM_MEMBUF_SIZE);
}
static void kem_cleanup(void){
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
  //includes the FIPS 203 section 7.2 modulus check: the library decodes and re-encodes each polynomial of ek,
  //compares, and returns CMOX_PQC_ERR_INVALID_PUBKEY on a difference (seen in its code: kem768.obj)
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
  //FIPS 203 section 7.3 hash check: cmox_pqc_kem_decapsulate accepts a key whose stored H(ek) is wrong (found
  //with core.c's check_dk_hash_check on the STM32U5A5), so it is done here with the library's SHA3-256
  uint8_t h[32];
  size_t h_size;
  if (cmox_hash_compute(CMOX_SHA3_256_ALGO, (const uint8_t*)secret_key + KEM_DK_EK_OFFSET, KEM_PUBLIC_KEY_SIZE,
                        h, sizeof h, &h_size) != CMOX_HASH_SUCCESS
      || h_size != sizeof h || !kem_dk_hash_matches(h, secret_key)) {
    throw_exception(ERROR_DECAPS|ERROR_DK_CHECK);
  }
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
