#pragma once

//pqm4 ML-KEM, compiled for PSET and GOAL by cmake/pqm4.cmake: goal fast is m4fspeed, smallram is m4fstack
#define IMPL_NAME "pqm4-" xstr(GOAL)

//api.h of the implementation; randombytes.h and fips202.h of mupq
#include "api.h"
#include "randombytes.h"
#include "fips202.h"

_Static_assert(CRYPTO_PUBLICKEYBYTES == KEM_PUBLIC_KEY_SIZE, "public key size");
_Static_assert(CRYPTO_SECRETKEYBYTES == KEM_SECRET_KEY_SIZE, "secret key size");
_Static_assert(CRYPTO_CIPHERTEXTBYTES == KEM_CIPHERTEXT_SIZE, "ciphertext size");
_Static_assert(CRYPTO_BYTES == KEM_SHARED_SECRET_SIZE, "shared secret size");

//pqm4 has only the randomized API: keygen draws d || z (64 bytes) and encaps m (32 bytes) from randombytes(),
//which hands over the benchmark's seed. Exactly one matching call per operation, else the operation fails.
//pqm4 has no FIPS 203 input checks (sections 7.2 and 7.3), which core.c requires of every implementation:
//kem_encaps adds the section 7.2 modulus check (core.c's kem_ek_modulus_ok), kem_decaps the section 7.3 hash
//check with pqm4's own SHA3-256.
#define ERROR_SEED 0x00000100
static const uint8_t *pqm4_seed;
static size_t pqm4_seed_size;
static int pqm4_seed_misuse;

//mupq's randombytes.h renames it PQCLEAN_randombytes
int randombytes(uint8_t *out, size_t outlen){
  if (pqm4_seed == NULL || outlen != pqm4_seed_size) {
    pqm4_seed_misuse = 1;
    memset(out, 0, outlen);
    return 0;
  }
  memcpy(out, pqm4_seed, outlen);
  pqm4_seed = NULL;
  return 0;
}

static void pqm4_set_seed(const void *seed, size_t size){
  pqm4_seed = seed;
  pqm4_seed_size = size;
  pqm4_seed_misuse = 0;
}

static int pqm4_seed_used(void){
  int ok = pqm4_seed == NULL && !pqm4_seed_misuse;
  pqm4_seed = NULL;
  return ok;
}

static void kem_init(void){
  //the assembly keeps data in the FPU registers: enable CP10/CP11 full access. The boards' start-up code already
  //does it, the generic start-up used with Renode only on the softfp targets (cortex-m33, m55).
  volatile uint32_t *cpacr = (volatile uint32_t *)0xE000ED88;
  *cpacr |= (0xFu << 20);
  __asm volatile ("dsb\n\tisb" ::: "memory");
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  pqm4_set_seed(seed, 64);
  int r = crypto_kem_keypair(public_key, secret_key);
  if (r) {
    throw_exception(ERROR_KEY_GEN|((uint32_t)r & 0xFF));
  }
  if (!pqm4_seed_used()) {
    throw_exception(ERROR_KEY_GEN|ERROR_SEED);
  }
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  //FIPS 203 section 7.2 modulus check (crypto_kem_enc does not do it)
  if (!kem_ek_modulus_ok(public_key)) {
    throw_exception(ERROR_ENCAPS|ERROR_EK_CHECK);
  }
  pqm4_set_seed(seed, 32);
  int r = crypto_kem_enc(ciphertext, shared_secret, public_key);
  if (r) {
    throw_exception(ERROR_ENCAPS|((uint32_t)r & 0xFF));
  }
  if (!pqm4_seed_used()) {
    throw_exception(ERROR_ENCAPS|ERROR_SEED);
  }
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  //FIPS 203 section 7.3 hash check (crypto_kem_dec does not do it)
  uint8_t h[32];
  sha3_256(h, (const uint8_t*)secret_key + KEM_DK_EK_OFFSET, KEM_PUBLIC_KEY_SIZE);
  if (!kem_dk_hash_matches(h, secret_key)) {
    throw_exception(ERROR_DECAPS|ERROR_DK_CHECK);
  }
  int r = crypto_kem_dec(shared_secret, ciphertext, secret_key);
  if (r) {
    throw_exception(ERROR_DECAPS|((uint32_t)r & 0xFF));
  }
}
