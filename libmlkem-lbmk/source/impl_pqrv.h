#pragma once

#define IMPL_NAME "pqrv"

#include <pqrv/pqrv.h>

//PQRV functions of the parameter set, e.g. PQRV_MLKEM(_dec) is pqrv_mlkem512_dec
#define PQRV_MLKEM(name) CAT3(pqrv_mlkem,PSET,name)
#define PQRV_MLKEM_SIZE(name) CAT3(PQRV_MLKEM,PSET,name)

_Static_assert(PQRV_MLKEM_SIZE(_PUBLICKEYBYTES) == KEM_PUBLIC_KEY_SIZE, "public key size");
_Static_assert(PQRV_MLKEM_SIZE(_SECRETKEYBYTES) == KEM_SECRET_KEY_SIZE, "secret key size");
_Static_assert(PQRV_MLKEM_SIZE(_CIPHERTEXTBYTES) == KEM_CIPHERTEXT_SIZE, "ciphertext size");
_Static_assert(PQRV_MLKEM_SSBYTES == KEM_SHARED_SECRET_SIZE, "shared secret size");

static void kem_init(void){
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  int r = PQRV_MLKEM(_keypair_derand)(public_key, secret_key, seed);
  if (r) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  int r = PQRV_MLKEM(_enc_derand)(ciphertext, shared_secret, public_key, seed);
  if (r) {
    throw_exception(ERROR_ENCAPS|r);
  }
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  int r = PQRV_MLKEM(_dec)(shared_secret, ciphertext, secret_key);
  if (r) {
    throw_exception(ERROR_DECAPS|r);
  }
}
