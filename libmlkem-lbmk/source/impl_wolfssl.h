#pragma once

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/wc_mlkem.h>

#ifndef WOLFSSL_HAVE_MLKEM
  #error "WOLFSSL built without ML-KEM (rebuild it: see crypto-libraries/wolfssl.py)"
#endif

//what each goal is made of is defined in crypto-libraries/wolfssl.py, which builds the library (benchmark.py, or
//"python3 goals.py build WOLFSSL <target> mlkem <pset> <goal>"); the checks below reject a library built otherwise.
//A build with options (GOAL_CUSTOM) may differ from its goal's configuration.
#define WOLFSSL_smallram 1
#define WOLFSSL_fast 2
#define WOLFSSL_smallcode 3
#define WOLFSSL_balanced 4

#define WOLFSSL_INDEX CAT(WOLFSSL_,GOAL)

//the small code and the small memory key generation and encapsulation
#if defined(WOLFSSL_MLKEM_SMALL) && defined(WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM) \
  && defined(WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM)
  #define WOLFSSL_SMALL_BUILD 1
#else
  #define WOLFSSL_SMALL_BUILD 0
#endif

#if WOLFSSL_INDEX == WOLFSSL_smallram
  #define IMPL_NAME "wolfssl-smallram"
  #if !GOAL_CUSTOM && (!WOLFSSL_SMALL_BUILD || defined(WOLFSSL_NO_MALLOC) || defined(WC_MLKEM_NO_ASM))
    #error "wolfssl-smallram expects a build with the small code and memory options, and the allocator (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_balanced
  #define IMPL_NAME "wolfssl-balanced"
  #if !GOAL_CUSTOM && (!WOLFSSL_SMALL_BUILD || !defined(WOLFSSL_NO_MALLOC) || defined(WC_MLKEM_NO_ASM))
    #error "wolfssl-balanced expects a build with the small code and memory options, and no allocator (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_smallcode
  #define IMPL_NAME "wolfssl-smallcode"
  #if !GOAL_CUSTOM && (!WOLFSSL_SMALL_BUILD || !defined(WOLFSSL_NO_MALLOC) || !defined(WC_MLKEM_NO_ASM) || !defined(WOLFSSL_SHA3_SMALL))
    #error "wolfssl-smallcode expects a build with the small code and memory options, no allocator, C arithmetic and the compact Keccak (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_fast
  #define IMPL_NAME "wolfssl-fast"
  #if !GOAL_CUSTOM && (defined(WOLFSSL_MLKEM_SMALL) || defined(WOLFSSL_MLKEM_NO_LARGE_CODE) || defined(WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM) || defined(WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM))
    #error "wolfssl-fast expects a build without the ML-KEM small code/memory options (see crypto-libraries/wolfssl.py)"
  #endif
#else
  #error "WOLFSSL ML-KEM supports GOAL smallram, smallcode, balanced or fast"
#endif

//on Cortex-M the library is configured with wolfSSL's Thumb-2 assembly: this rejects a build from before that, or
//for another CPU
#if defined(__ARM_ARCH_PROFILE) && (__ARM_ARCH_PROFILE == 'M')
  #ifndef WOLFSSL_ARMASM_THUMB2
    #error "on Cortex-M, wolfssl-<goal> expects a build with wolfSSL's Thumb-2 assembly (rebuild it: see crypto-libraries/wolfssl.py)"
  #endif
#elif defined(WOLFSSL_ARMASM)
  #error "wolfSSL's ARM assembly is only expected on Cortex-M (rebuild it: see crypto-libraries/wolfssl.py)"
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
  //includes the FIPS 203 section 7.2 modulus check (mlkem_check_reduced)
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
  //includes the FIPS 203 section 7.3 hash check (MLKEM_PUB_HASH_E), and the modulus checks of both vectors
  r = wc_MlKemKey_DecodePrivateKey(&key, secret_key, KEM_SECRET_KEY_SIZE);
  if (0 == r) {
    r = wc_MlKemKey_Decapsulate(&key, shared_secret, ciphertext, KEM_CIPHERTEXT_SIZE);
  }
  wc_MlKemKey_Free(&key);
  if (r) {
    throw_exception(ERROR_DECAPS|WOLFSSL_ERR(r));
  }
}
