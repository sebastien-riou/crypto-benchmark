#pragma once

//PQShield's PQMicroLib-Core has a single ML-KEM implementation, the goal selects the
//pqmicrolib-library preset it is built with: <target>-balanced or <target>-fast (built for speed)
#define UMLKEM_balanced 1
#define UMLKEM_fast 2

#define UMLKEM_INDEX CAT(UMLKEM_,GOAL)

#if UMLKEM_INDEX == UMLKEM_balanced
  #define IMPL_NAME "umlkem-balanced"
#elif UMLKEM_INDEX == UMLKEM_fast
  #define IMPL_NAME "umlkem-fast"
#else
  #error "PQCLE ML-KEM supports GOAL balanced or fast only"
#endif

#include <pqcle/pqs_mlkem.h>
#include <stddef.h>

static enum pqs_mlkem_algid pset_to_algid(unsigned int pset){
  switch(pset){
    case 512: return PQS_MLKEM_ALGID_MLKEM_512;break;
    case 768: return PQS_MLKEM_ALGID_MLKEM_768;break;
    case 1024: return PQS_MLKEM_ALGID_MLKEM_1024;break;
    default: throw_exception(ERROR_PSET);
  }
  __builtin_unreachable();
}

//the context holds pointers, keep it aligned
static uint64_t ctx[(PQS_MLKEM_CTX_SIZE+sizeof(uint64_t)-1)/sizeof(uint64_t)];

static void kem_init(void){
}

static void kem_keygen(
  const void*const seed,
  void*public_key,
  void*secret_key
){
  enum pqs_mlkem_result r = pqs_mlkem_ctx_init((struct pqs_mlkem_ctx*)ctx, pset_to_algid(PSET), NULL);
  if (r != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_KEY_GEN|ERROR_LIB_INIT|r);
  }
  r = pqs_mlkem_keygen((struct pqs_mlkem_ctx*)ctx, seed, secret_key, public_key);
  if (r != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_KEY_GEN|r);
  }
}

static void kem_encaps(
  const void*const public_key,
  const void*const seed,
  void*ciphertext,
  void*shared_secret
){
  enum pqs_mlkem_result r = pqs_mlkem_ctx_init((struct pqs_mlkem_ctx*)ctx, pset_to_algid(PSET), NULL);
  if (r != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_ENCAPS|ERROR_LIB_INIT|r);
  }
  r = pqs_mlkem_encaps((struct pqs_mlkem_ctx*)ctx, seed, public_key, shared_secret, ciphertext);
  if (r != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_ENCAPS|r);
  }
}

static void kem_decaps(
  const void*const secret_key,
  const void*const ciphertext,
  void*shared_secret
){
  enum pqs_mlkem_result r = pqs_mlkem_ctx_init((struct pqs_mlkem_ctx*)ctx, pset_to_algid(PSET), NULL);
  if (r != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_DECAPS|ERROR_LIB_INIT|r);
  }
  //FIPS 203 section 7.3 hash check: pqs_mlkem_decaps leaves key validation to the caller (pqs_mlkem.h);
  //pqs_mlkem_secret_key_validate does it with the library's SHA3-256
  if (pqs_mlkem_secret_key_validate(pset_to_algid(PSET), secret_key, KEM_SECRET_KEY_SIZE) != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_DECAPS|ERROR_DK_CHECK);
  }
  r = pqs_mlkem_decaps((struct pqs_mlkem_ctx*)ctx, secret_key, shared_secret, ciphertext);
  if (r != PQS_MLKEM_SUCCESS) {
    throw_exception(ERROR_DECAPS|r);
  }
}
