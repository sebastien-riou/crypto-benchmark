#pragma once

//mlkem-native, compiled for the parameter set PSET and the goal GOAL by libmlkem-lbmk/CMakeLists.txt
#include <mlkem_native.h>

#define MLKEM_NATIVE_fast 1

#define MLKEM_NATIVE_INDEX CAT(MLKEM_NATIVE_,GOAL)

//the configuration of the goal; a build with options (GOAL_CUSTOM) may differ from it
#if MLKEM_NATIVE_INDEX == MLKEM_NATIVE_fast
  #if !defined(MLK_CONFIG_SERIAL_FIPS202_ONLY) && !GOAL_CUSTOM
    #error "mlkem-native-fast expects MLK_CONFIG_SERIAL_FIPS202_ONLY"
  #endif
#else
  #error "mlkem-native supports GOAL fast only"
#endif

#define IMPL_NAME "mlkem-native-" xstr(GOAL)

#if MLK_CONFIG_PARAMETER_SET != PSET
  #error "mlkem-native is built for another parameter set"
#endif

_Static_assert(MLKEM_PUBLICKEYBYTES(PSET) == KEM_PUBLIC_KEY_SIZE, "public key size");
_Static_assert(MLKEM_SECRETKEYBYTES(PSET) == KEM_SECRET_KEY_SIZE, "secret key size");
_Static_assert(MLKEM_CIPHERTEXTBYTES(PSET) == KEM_CIPHERTEXT_SIZE, "ciphertext size");
_Static_assert(MLKEM_BYTES == KEM_SHARED_SECRET_SIZE, "shared secret size");

//mlkem-native's errors are negative
#define MLKEM_NATIVE_ERR(r) ((uint32_t)(-(r)) & 0xFF)

static void kem_init(void){
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  int r = mlkem_native_keypair_derand(public_key, secret_key, seed);
  if (r) {
    throw_exception(ERROR_KEY_GEN|MLKEM_NATIVE_ERR(r));
  }
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  //mlkem_native_enc_derand does the FIPS 203 section 7.2 modulus check
  int r = mlkem_native_enc_derand(ciphertext, shared_secret, public_key, seed);
  if (MLK_ERR_INVALID_PK == r) {
    throw_exception(ERROR_ENCAPS|ERROR_EK_CHECK);
  }
  if (r) {
    throw_exception(ERROR_ENCAPS|MLKEM_NATIVE_ERR(r));
  }
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  //mlkem_native_dec does the FIPS 203 section 7.3 hash check
  int r = mlkem_native_dec(shared_secret, ciphertext, secret_key);
  if (MLK_ERR_INVALID_SK == r) {
    throw_exception(ERROR_DECAPS|ERROR_DK_CHECK);
  }
  if (r) {
    throw_exception(ERROR_DECAPS|MLKEM_NATIVE_ERR(r));
  }
}
