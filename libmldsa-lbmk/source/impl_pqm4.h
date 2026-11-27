#pragma once

//pqm4 ML-DSA, compiled for PSET and GOAL by cmake/pqm4.cmake: goal fast is m4f, smallram is m4fstack
#define IMPL_NAME "pqm4-" xstr(GOAL)

//api.h of the implementation; randombytes.h of mupq
#include "api.h"
#include "randombytes.h"

_Static_assert(CRYPTO_PUBLICKEYBYTES == DSA_PUBLIC_KEY_SIZE, "public key size");
_Static_assert(CRYPTO_SECRETKEYBYTES == DSA_PRIVATE_KEY_SIZE, "private key size");
_Static_assert(CRYPTO_BYTES == DSA_SIG_SIZE, "signature size");

//m4f keeps the matrix on the stack: about 98 KB for keygen and 108 KB for signing (ML-DSA-87, pqm4's benchmarks)
#define DSA_MAX_STACK_SIZE (160*1024)

//pqm4 has only the randomized API: keygen draws its 32-byte seed and signing its 32-byte rnd from randombytes(),
//which hands over the benchmark's seed, or 32 zero bytes for deterministic signing. Exactly one matching call per
//operation, else the operation fails.
#define ERROR_SEED 0x00000100
static const uint8_t *pqm4_seed;
static size_t pqm4_seed_size;
static int pqm4_seed_misuse;
static const uint8_t pqm4_rnd[32] = {0};

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

//the assembly keeps data in the FPU registers: enable CP10/CP11 full access, before main and outside the
//measurements (core.c has no initialization hook for ML-DSA). The boards' start-up code already does it, the
//generic start-up used with Renode only on the softfp targets (cortex-m33, m55).
__attribute__((constructor)) static void pqm4_enable_fpu(void){
  volatile uint32_t *cpacr = (volatile uint32_t *)0xE000ED88;
  *cpacr |= (0xFu << 20);
  __asm volatile ("dsb\n\tisb" ::: "memory");
}

static uint8_t impl_private_key[DSA_PRIVATE_KEY_SIZE] __attribute__((aligned(4)));
static uint8_t impl_public_key[DSA_PUBLIC_KEY_SIZE] __attribute__((aligned(4)));
//pure ML-DSA with an empty context string
static const uint8_t impl_ctx[1] = {0};

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  if (pset != PSET) {
    throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  pqm4_set_seed(seed, 32);
  int r = crypto_sign_keypair(impl_public_key, impl_private_key);
  if (!pqm4_seed_used()) {
    throw_exception(ERROR_KEY_GEN|ERROR_SEED);
  }
  if (r) {
    throw_exception(ERROR_KEY_GEN|((uint32_t)r & 0xFF));
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
  return crypto_sign_verify_ctx(signature, DSA_SIG_SIZE, message, message_size, impl_ctx, 0, impl_public_key) != 0;
}

static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  size_t signature_size = 0;
  if (pset != PSET) {
    throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  //deterministic: rnd is 32 zero bytes
  pqm4_set_seed(pqm4_rnd, sizeof pqm4_rnd);
  int r = crypto_sign_signature_ctx(signature, &signature_size, message, message_size, impl_ctx, 0,
                                    impl_private_key);
  if (!pqm4_seed_used()) {
    throw_exception(ERROR_SIGN|ERROR_SEED);
  }
  if (r || signature_size != DSA_SIG_SIZE) {
    throw_exception(ERROR_SIGN|((uint32_t)r & 0xFF));
  }
}
