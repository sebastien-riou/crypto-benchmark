#pragma once

#define IMPL_NAME "stub"
#include <lean-benchmark/lean-benchmark.h>

static void kem_init(void){
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  LBMK_touch_pointers(3, seed, public_key, secret_key);
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  LBMK_touch_pointers(4, public_key, seed, ciphertext, shared_secret);
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  LBMK_touch_pointers(3, secret_key, ciphertext, shared_secret);
}
