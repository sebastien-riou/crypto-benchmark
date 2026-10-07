#pragma once

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/wc_mlkem.h>

#ifndef WOLFSSL_HAVE_MLKEM
  #error "WOLFSSL built without ML-KEM (use buildit-mlkem-<goal> in the wolfssl repo)"
#endif

#define WOLFSSL_small 1
#define WOLFSSL_fast 2
//same options as small / fast, with wolfSSL's Thumb-2 assembly (cortex-m* only)
#define WOLFSSL_small_armasm 3
#define WOLFSSL_fast_armasm 4

#define WOLFSSL_INDEX CAT(WOLFSSL_,GOAL)

#if WOLFSSL_INDEX == WOLFSSL_small || WOLFSSL_INDEX == WOLFSSL_small_armasm
  #if !defined(WOLFSSL_MLKEM_SMALL) || !defined(WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM) || !defined(WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM)
    #error "wolfssl-small expects a build with WOLFSSL_MLKEM_SMALL, WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM and WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM (buildit-mlkem-small or buildit-mlkem-small-armasm)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_fast || WOLFSSL_INDEX == WOLFSSL_fast_armasm
  #if defined(WOLFSSL_MLKEM_SMALL) || defined(WOLFSSL_MLKEM_NO_LARGE_CODE) || defined(WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM) || defined(WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM)
    #error "wolfssl-fast expects a build without the ML-KEM small code/memory options (buildit-mlkem-fast or buildit-mlkem-fast-armasm)"
  #endif
#else
  #error "WOLFSSL ML-KEM supports GOAL small, fast, small-armasm or fast-armasm"
#endif

#if WOLFSSL_INDEX == WOLFSSL_small_armasm || WOLFSSL_INDEX == WOLFSSL_fast_armasm
  #ifndef WOLFSSL_ARMASM_THUMB2
    #error "wolfssl-*-armasm expects a build with wolfSSL's Thumb-2 assembly (buildit-mlkem-small-armasm or buildit-mlkem-fast-armasm)"
  #endif
#elif defined(WOLFSSL_ARMASM)
  #error "wolfssl-small and wolfssl-fast expect a build without wolfSSL's ARM assembly (buildit-mlkem-small or buildit-mlkem-fast)"
#endif

#if WOLFSSL_INDEX == WOLFSSL_small
  #define IMPL_NAME "wolfssl-small"
#elif WOLFSSL_INDEX == WOLFSSL_fast
  #define IMPL_NAME "wolfssl-fast"
#elif WOLFSSL_INDEX == WOLFSSL_small_armasm
  #define IMPL_NAME "wolfssl-small-armasm"
#else
  #define IMPL_NAME "wolfssl-fast-armasm"
#endif

#include <stddef.h>

static int pset_to_type(unsigned int pset){
  switch(pset){
    case 512: return WC_ML_KEM_512;break;
    case 768: return WC_ML_KEM_768;break;
    case 1024: return WC_ML_KEM_1024;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}

//wolfSSL error codes are negative
#define WOLFSSL_ERR(r) ((uint32_t)(-(r)) & 0xFFFF)

//the key object is the internal representation used by wolfSSL.
//keys and ciphertext are exchanged as byte strings, so each operation encodes/decodes them,
//like the other libraries do internally.
static MlKemKey key;

static void kem_init(void){
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  int r = wc_MlKemKey_Init(&key, pset_to_type(PSET), NULL, INVALID_DEVID);
  if (r) {
    throw_exception(ERROR_KEY_GEN|ERROR_LIB_INIT|WOLFSSL_ERR(r));
  }
  r = wc_MlKemKey_MakeKeyWithRandom(&key, seed, MLKEM_KEYGEN_SEEDBYTES);
  if (0 == r) {
    r = wc_MlKemKey_EncodePublicKey(&key, public_key, KEM_PUBLIC_KEY_SIZE);
  }
  if (0 == r) {
    r = wc_MlKemKey_EncodePrivateKey(&key, secret_key, KEM_SECRET_KEY_SIZE);
  }
  wc_MlKemKey_Free(&key);
  if (r) {
    throw_exception(ERROR_KEY_GEN|WOLFSSL_ERR(r));
  }
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  int r = wc_MlKemKey_Init(&key, pset_to_type(PSET), NULL, INVALID_DEVID);
  if (r) {
    throw_exception(ERROR_ENCAPS|ERROR_LIB_INIT|WOLFSSL_ERR(r));
  }
  r = wc_MlKemKey_DecodePublicKey(&key, public_key, KEM_PUBLIC_KEY_SIZE);
  if (0 == r) {
    r = wc_MlKemKey_EncapsulateWithRandom(&key, ciphertext, shared_secret, seed, MLKEM_ENCAPS_SEEDBYTES);
  }
  wc_MlKemKey_Free(&key);
  if (r) {
    throw_exception(ERROR_ENCAPS|WOLFSSL_ERR(r));
  }
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  int r = wc_MlKemKey_Init(&key, pset_to_type(PSET), NULL, INVALID_DEVID);
  if (r) {
    throw_exception(ERROR_DECAPS|ERROR_LIB_INIT|WOLFSSL_ERR(r));
  }
  r = wc_MlKemKey_DecodePrivateKey(&key, secret_key, KEM_SECRET_KEY_SIZE);
  if (0 == r) {
    r = wc_MlKemKey_Decapsulate(&key, shared_secret, ciphertext, KEM_CIPHERTEXT_SIZE);
  }
  wc_MlKemKey_Free(&key);
  if (r) {
    throw_exception(ERROR_DECAPS|WOLFSSL_ERR(r));
  }
}
