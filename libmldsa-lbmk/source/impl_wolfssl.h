#pragma once

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/dilithium.h>

#ifndef HAVE_DILITHIUM
  #error "WOLFSSL built without dilithium/MLDSA"
#endif


//what each goal is made of is defined in crypto-libraries/wolfssl.py, which builds the library (benchmark.py, or
//"python3 goals.py build WOLFSSL <target> mldsa <pset> <goal>"); the checks below reject a library built otherwise.
//A build with options (GOAL_CUSTOM) may differ from its goal's configuration.
#define WOLFSSL_smallram 1
#define WOLFSSL_balanced 2
#define WOLFSSL_fast 3
#define WOLFSSL_smallcode 4

#define WOLFSSL_INDEX CAT(WOLFSSL_,GOAL)

//on Cortex-M the library is configured with wolfSSL's Thumb-2 assembly (for ML-DSA, only Keccak): this rejects a
//build from before that, or for another CPU
#if defined(__ARM_ARCH_PROFILE) && (__ARM_ARCH_PROFILE == 'M')
  #ifndef WOLFSSL_ARMASM_THUMB2
    #error "on Cortex-M, wolfssl-<goal> expects a build with wolfSSL's Thumb-2 assembly (rebuild it: see crypto-libraries/wolfssl.py)"
  #endif
#elif defined(WOLFSSL_ARMASM)
  #error "wolfSSL's ARM assembly is only expected on Cortex-M (rebuild it: see crypto-libraries/wolfssl.py)"
#endif

//the small memory key generation, signature and verification, the verification buffers on the heap
#if defined(WOLFSSL_DILITHIUM_SMALL) && defined(WOLFSSL_DILITHIUM_MAKE_KEY_SMALL_MEM) \
  && defined(WOLFSSL_DILITHIUM_SIGN_SMALL_MEM) && defined(WOLFSSL_DILITHIUM_VERIFY_SMALL_MEM) \
  && !defined(WOLFSSL_DILITHIUM_VERIFY_NO_MALLOC)
  #define WOLFSSL_SMALL_MEM_BUILD 1
#else
  #define WOLFSSL_SMALL_MEM_BUILD 0
#endif

#if WOLFSSL_INDEX == WOLFSSL_smallram
  #define IMPL_NAME "wolfssl-smallram"
  #if !GOAL_CUSTOM && (!WOLFSSL_SMALL_MEM_BUILD || defined(WOLFSSL_DILITHIUM_SIGN_SMALL_MEM_PRECALC_A) || defined(WOLFSSL_SHA3_SMALL))
    #error "wolfssl-smallram expects a build with the small code and the small memory operations (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_smallcode
  #define IMPL_NAME "wolfssl-smallcode"
  #if !GOAL_CUSTOM && (!WOLFSSL_SMALL_MEM_BUILD || defined(WOLFSSL_DILITHIUM_SIGN_SMALL_MEM_PRECALC_A) || !defined(WOLFSSL_SHA3_SMALL))
    #error "wolfssl-smallcode expects a build with the small code, the small memory operations and the compact Keccak (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_balanced
  #define IMPL_NAME "wolfssl-balanced"
  #if !GOAL_CUSTOM && (!WOLFSSL_SMALL_MEM_BUILD || !defined(WOLFSSL_DILITHIUM_SIGN_SMALL_MEM_PRECALC_A))
    #error "wolfssl-balanced expects a build with the small code and the signature that keeps the matrix A (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_fast
  #define IMPL_NAME "wolfssl-fast"
  #if !GOAL_CUSTOM && (defined(WOLFSSL_DILITHIUM_SMALL) || defined(WOLFSSL_DILITHIUM_SIGN_SMALL_MEM) || !defined(WOLFSSL_DILITHIUM_VERIFY_SMALL_MEM))
    #error "wolfssl-fast expects a build without the small code and the small memory signature, with the small memory verification (see crypto-libraries/wolfssl.py)"
  #endif
#else
  #error "WOLFSSL ML-DSA supports GOAL smallram, smallcode, balanced or fast"
#endif


#include <stddef.h>
int _gettimeofday( struct timeval *tv, void *tzvp){
  return 0;
}

static unsigned int pset_to_sec_cat(unsigned int pset){
  switch(pset){
    case 44: return 2;break;
    case 65: return 3;break;
    case 87: return 5;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}

static MlDsaKey key;

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  int r = wc_MlDsaKey_Init(&key, NULL, INVALID_DEVID);
  if (r) {// Context initialization failed.
    throw_exception(ERROR_KEY_GEN|ERROR_LIB_INIT|r);
  }
  r = wc_MlDsaKey_SetParams(&key, pset_to_sec_cat(pset));
  if (r) {// Context initialization failed.
    throw_exception(ERROR_KEY_GEN|ERROR_LIB_INIT|r);
  }
  r = wc_dilithium_make_key_from_seed(&key, seed);
  if (r) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}

static void dsa_get_private_key(void* private_key){
  unsigned int priv_len = DSA_PRIVATE_KEY_SIZE;
  int r = wc_MlDsaKey_ExportPrivRaw(&key, private_key, &priv_len);
  if (r) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}
static void dsa_get_public_key(void* public_key){
  unsigned int pub_len = DSA_PUBLIC_KEY_SIZE;
  int r = wc_MlDsaKey_ExportPubRaw(&key, public_key, &pub_len);
  if (r) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}

static uint32_t dsa_verify(//returns 0 if success
  const unsigned int pset,
  const void*const signature,
  const void*const message,
  size_t message_size){
  int verify_res = 0;
  int r = wc_dilithium_verify_ctx_msg(signature, DSA_SIG_SIZE, NULL, 0, message, message_size, &verify_res, &key);
  if (r) {
    throw_exception(ERROR_VERIFY|r);
  }
  return verify_res != 1;
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  uint8_t seed[32] = {0};
  unsigned int sig_len = DSA_SIG_SIZE;
  int r = wc_dilithium_sign_ctx_msg_with_seed(NULL, 0, message, message_size, signature, &sig_len, &key, seed);
  if (r) {
    throw_exception(ERROR_SIGN|r);
  }
}
