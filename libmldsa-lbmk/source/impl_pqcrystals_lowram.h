#pragma once

#define IMPL_NAME "pqcrystals-mldsa-lowram"

#include <pqcrystals-mldsa-lowram/api.h>


typedef int (*pqcrystals_lowram_keypair_from_seed_t)(const void* seed,uint8_t *pk, uint8_t *sk);

typedef int (*pqcrystals_lowram_signature_t)(uint8_t *sig, size_t *siglen,
                                        const uint8_t *m, size_t mlen,
                                        const uint8_t *ctx, size_t ctxlen,
                                        const uint8_t *sk);

typedef int (*pqcrystals_lowram_verify_t)(const uint8_t *sig, size_t siglen,
                                     const uint8_t *m, size_t mlen,
                                     const uint8_t *ctx, size_t ctxlen,
                                     const uint8_t *pk);

static uint8_t impl_private_key[DSA_PRIVATE_KEY_SIZE]={0};
static uint8_t impl_public_key[DSA_PUBLIC_KEY_SIZE]={0};

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  int r;
  pqcrystals_lowram_keypair_from_seed_t impl;
  switch(pset){
    #if PSET == 44
    case 44: impl = pqcrystals_dilithium2_lowram_keypair_from_seed;break;
    #endif
    #if PSET == 65
    case 65: impl = pqcrystals_dilithium3_lowram_keypair_from_seed;break;
    #endif
    #if PSET == 87
    case 87: impl = pqcrystals_dilithium5_lowram_keypair_from_seed;break;
    #endif
    default: throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  r = impl(seed,impl_public_key, impl_private_key);
  if (r) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}
static void dsa_get_private_key(void* private_key){
  memcpy(private_key, impl_private_key, DSA_PRIVATE_KEY_SIZE);
}
static void dsa_get_public_key(void* public_key){
  memcpy(public_key, impl_public_key, DSA_PUBLIC_KEY_SIZE);
}

static uint32_t dsa_verify(
  const unsigned int pset,
  const void*const signature,
  const void*const message,
  size_t message_size){
  int r;
  size_t signature_size = DSA_SIG_SIZE;
  const uint8_t *ctx=0;
  size_t ctxlen=0;
  pqcrystals_lowram_verify_t impl;
  switch(pset){
    #if PSET == 44
    case 44: impl = pqcrystals_dilithium2_lowram_verify;break;
    #endif
    #if PSET == 65
    case 65: impl = pqcrystals_dilithium3_lowram_verify;break;
    #endif
    #if PSET == 87
    case 87: impl = pqcrystals_dilithium5_lowram_verify;break;
    #endif
    default: throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  r = impl(
    signature, signature_size, 
    message, message_size, 
    ctx, ctxlen,
    impl_public_key);
  
  return r;
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  size_t signature_size = DSA_SIG_SIZE;
  const uint8_t *ctx=0;
  size_t ctxlen=0;
  int r;
  pqcrystals_lowram_signature_t impl;
  switch(pset){
    #if PSET == 44
    case 44: impl = pqcrystals_dilithium2_lowram_signature;break;
    #endif
    #if PSET == 65
    case 65: impl = pqcrystals_dilithium3_lowram_signature;break;
    #endif
    #if PSET == 87
    case 87: impl = pqcrystals_dilithium5_lowram_signature;break;
    #endif
    default: throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  r = impl(
    signature, &signature_size, 
    message, message_size, 
    ctx, ctxlen,
    impl_private_key);
  if (r) {
    throw_exception(ERROR_SIGN|r);
  }
}


