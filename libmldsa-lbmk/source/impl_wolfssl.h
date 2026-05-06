#pragma once

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/dilithium.h>

#ifndef HAVE_DILITHIUM
  #error "WOLFSSL built without dilithium/MLDSA"
#endif


#define WOLFSSL_small 1
#define WOLFSSL_balanced 2
#define WOLFSSL_fast 3

#define WOLFSSL_INDEX CAT(WOLFSSL_,GOAL)

#if WOLFSSL_INDEX == WOLFSSL_small
  #define IMPL_NAME "wolfssl-small"
  #ifndef WOLFSSL_DILITHIUM_SIGN_SMALL_MEM
    #error
  #endif
#endif

#if WOLFSSL_INDEX == WOLFSSL_balanced
  #define IMPL_NAME "wolfssl-fast" //we do not support a balanced build yet
  #ifdef WOLFSSL_DILITHIUM_SIGN_SMALL_MEM
    #error
  #endif
#endif

#if WOLFSSL_INDEX == WOLFSSL_fast
  #define IMPL_NAME "wolfssl-fast"
  #ifdef WOLFSSL_DILITHIUM_SIGN_SMALL_MEM
    #error
  #endif
#endif


//#ifdef WOLFSSL_DILITHIUM_SIGN_SMALL_MEM
//#define IMPL_NAME "wolfssl-lowram"
//#else
//#define IMPL_NAME "wolfssl-fast"
//#endif


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
