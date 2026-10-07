#pragma once

#define IMPL_NAME "pqrv"

#include <pqrv/pqrv.h>

//PQRV keeps the expanded matrix on the stack: signing needs up to 124 KB (ML-DSA-87)
#define DSA_MAX_STACK_SIZE (160*1024)

//PQRV functions of the parameter set, e.g. PQRV_MLDSA(_verify) is pqrv_mldsa44_verify
#define PQRV_MLDSA(name) CAT3(pqrv_mldsa,PSET,name)
#define PQRV_MLDSA_SIZE(name) CAT3(PQRV_MLDSA,PSET,name)

_Static_assert(PQRV_MLDSA_SIZE(_PUBLICKEYBYTES) == DSA_PUBLIC_KEY_SIZE, "public key size");
_Static_assert(PQRV_MLDSA_SIZE(_SECRETKEYBYTES) == DSA_PRIVATE_KEY_SIZE, "private key size");
_Static_assert(PQRV_MLDSA_SIZE(_BYTES) == DSA_SIG_SIZE, "signature size");

static uint8_t impl_private_key[DSA_PRIVATE_KEY_SIZE]={0};
static uint8_t impl_public_key[DSA_PUBLIC_KEY_SIZE]={0};

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  int r;
  if (pset != PSET) {
    throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  r = PQRV_MLDSA(_keypair_internal)(impl_public_key, impl_private_key, seed);
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
  if (pset != PSET) {
    throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  //pure ML-DSA with an empty context string
  return PQRV_MLDSA(_verify)(
    signature, DSA_SIG_SIZE,
    message, message_size,
    0, 0,
    impl_public_key);
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  size_t signature_size = DSA_SIG_SIZE;
  int r;
  if (pset != PSET) {
    throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  //deterministic pure ML-DSA with an empty context string
  r = PQRV_MLDSA(_signature)(
    signature, &signature_size,
    message, message_size,
    0, 0,
    impl_private_key);
  if (r) {
    throw_exception(ERROR_SIGN|r);
  }
}
