#pragma once

//mldsa-native, compiled for the parameter set PSET and the goal GOAL by libmldsa-lbmk/CMakeLists.txt
#include <mldsa_native.h>

#define MLDSA_NATIVE_small 1
#define MLDSA_NATIVE_fast 2

#define MLDSA_NATIVE_INDEX CAT(MLDSA_NATIVE_,GOAL)

#if MLDSA_NATIVE_INDEX == MLDSA_NATIVE_small
  #ifndef MLD_CONFIG_REDUCE_RAM
    #error "mldsa-native-small expects MLD_CONFIG_REDUCE_RAM"
  #endif
#elif MLDSA_NATIVE_INDEX == MLDSA_NATIVE_fast
  #ifdef MLD_CONFIG_REDUCE_RAM
    #error "mldsa-native-fast expects the default memory mode"
  #endif
  //the default memory mode keeps the expanded matrix on the stack: signing needs about 107 KB (ML-DSA-87)
  #define DSA_MAX_STACK_SIZE (160*1024)
#else
  #error "mldsa-native supports GOAL small or fast only"
#endif

#define IMPL_NAME "mldsa-native-" xstr(GOAL)

#if MLD_CONFIG_PARAMETER_SET != PSET
  #error "mldsa-native is built for another parameter set"
#endif

_Static_assert(MLDSA_PUBLICKEYBYTES(PSET) == DSA_PUBLIC_KEY_SIZE, "public key size");
_Static_assert(MLDSA_SECRETKEYBYTES(PSET) == DSA_PRIVATE_KEY_SIZE, "private key size");
_Static_assert(MLDSA_BYTES(PSET) == DSA_SIG_SIZE, "signature size");

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
  r = mldsa_native_keypair_internal(impl_public_key, impl_private_key, seed);
  if (r) {
    throw_exception(ERROR_KEY_GEN|(r & 0xFF));
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
  return mldsa_native_verify(
    signature,
    message, message_size,
    0, 0,
    impl_public_key) != 0;
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  //pure ML-DSA with an empty context string: the message is prefixed by 0 (not pre-hashed) and the context length
  static const uint8_t prefix[2] = {0, 0};
  //deterministic signing
  static const uint8_t rnd[MLDSA_RNDBYTES] = {0};
  int r;
  if (pset != PSET) {
    throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  r = mldsa_native_signature_internal(
    signature,
    message, message_size,
    prefix, sizeof(prefix),
    rnd,
    impl_private_key,
    0);
  if (r) {
    throw_exception(ERROR_SIGN|(r & 0xFF));
  }
}
