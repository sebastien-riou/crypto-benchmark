#pragma once


#define UMLDSA_small 1
#define UMLDSA_balanced 2

#define UMLDSA_INDEX CAT(UMLDSA_,GOAL)

#if UMLDSA_INDEX == UMLDSA_small
  #define IMPL_NAME "umldsa-small"
#endif

#if UMLDSA_INDEX == UMLDSA_balanced
  #define IMPL_NAME "umldsa-balanced"
#endif

#include <pqcle/pqs_mldsa.h>
#include <stddef.h>

static unsigned int pset_to_algid(unsigned int pset){
  switch(pset){
    case 44: return PQS_MLDSA_ALGID_MLDSA_44;break;
    case 65: return PQS_MLDSA_ALGID_MLDSA_65;break;
    case 87: return PQS_MLDSA_ALGID_MLDSA_87;break;
    default: throw_exception(ERROR_PSET);
  }
  //unreachable();
  __builtin_unreachable();
}

//#define CTX_IN_STACK
#ifndef CTX_IN_STACK
static uint8_t ctx[PQS_MLDSA_CTX_SIZE] = { 0 };
#endif
static uint8_t pqs_private_key[DSA_PRIVATE_KEY_SIZE]={0};
static uint8_t pqs_public_key[DSA_PUBLIC_KEY_SIZE]={0};

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  #ifdef CTX_IN_STACK
  uint8_t ctx[PQS_MLDSA_CTX_SIZE] = { 0 };
  #endif
  // Initialization of the context
  enum pqs_mldsa_result r = pqs_mldsa_ctx_init((struct pqs_mldsa_ctx*)ctx, pset_to_algid(pset), NULL);
  if (r != PQS_MLDSA_SUCCESS) {// Context initialization failed.
    throw_exception(ERROR_KEY_GEN|ERROR_LIB_INIT|r);
  }
  r = pqs_mldsa_keygen((struct pqs_mldsa_ctx*)ctx, seed, pqs_private_key, pqs_public_key);
  if (r != PQS_MLDSA_SUCCESS) {// Context initialization failed.
    throw_exception(ERROR_KEY_GEN|r);
  }
}

static void dsa_get_private_key(void* private_key){
  memcpy(private_key, pqs_private_key, DSA_PRIVATE_KEY_SIZE);
}
static void dsa_get_public_key(void* public_key){
  memcpy(public_key, pqs_public_key, DSA_PUBLIC_KEY_SIZE);
}

static uint32_t dsa_verify(
  const unsigned int pset,
  const void*const signature,
  const void*const message,
  size_t message_size){
  #ifdef CTX_IN_STACK
  uint8_t ctx[PQS_MLDSA_CTX_SIZE] = { 0 };
  #endif
  size_t signature_size = DSA_SIG_SIZE;
  // Initialization of the context
  enum pqs_mldsa_result r = pqs_mldsa_ctx_init((struct pqs_mldsa_ctx*)ctx, pset_to_algid(pset), NULL);
  if (r != PQS_MLDSA_SUCCESS) {// Context initialization failed.
    throw_exception(ERROR_VERIFY|ERROR_LIB_INIT|r);
  }
  r = pqs_mldsa_verify_msg(
    (struct pqs_mldsa_ctx*)ctx, 
    pqs_public_key, 
    signature, signature_size, 
    message, message_size, 0, 0);
  
  return r!=PQS_MLDSA_SUCCESS;
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  #ifdef CTX_IN_STACK
  uint8_t ctx[PQS_MLDSA_CTX_SIZE] = { 0 };
  #endif
  size_t signature_size = DSA_SIG_SIZE;
  uint8_t seed[32] = {0};//deterministic
  // Initialization of the context
  enum pqs_mldsa_result r = pqs_mldsa_ctx_init((struct pqs_mldsa_ctx*)ctx, pset_to_algid(pset), NULL);
  if (r != PQS_MLDSA_SUCCESS) {// Context initialization failed.
    throw_exception(ERROR_SIGN|ERROR_LIB_INIT|r);
  }
  r = pqs_mldsa_sign_msg(
    (struct pqs_mldsa_ctx*)ctx, 
    seed, 
    pqs_private_key, 
    signature, &signature_size, 
    message, message_size, 0, 0);
  if (r != PQS_MLDSA_SUCCESS) {// Context initialization failed.
    throw_exception(ERROR_SIGN|r);
  }
}


