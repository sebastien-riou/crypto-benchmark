#pragma once

#define IMPL_NAME "pqcle"

#include <pqcle/pqs_hash.h>
#include <stddef.h>

#define SHA2_224_DIGEST_SIZE (28)
#define SHA2_256_DIGEST_SIZE (32)
#define SHA2_384_DIGEST_SIZE (48)
#define SHA2_512_DIGEST_SIZE (64)
#define SHA2_512_224_DIGEST_SIZE (28)
#define SHA2_512_256_DIGEST_SIZE (32)

static unsigned int pset_to_digest_size(unsigned int pset){
  switch(pset){
    case 1224:
    case 224: return SHA2_224_DIGEST_SIZE;
    case 1256:
    case 256: return SHA2_256_DIGEST_SIZE;
    case 1384:
    case 384: return SHA2_384_DIGEST_SIZE;
    case 1512:
    case 512: return SHA2_512_DIGEST_SIZE;
    case 1513:
    case 513: return SHA2_512_224_DIGEST_SIZE;
    case 1514:
    case 514: return SHA2_512_256_DIGEST_SIZE;
    default: throw_exception(ERROR_PSET);
  }
  //unreachable();
  __builtin_unreachable();
}
static unsigned int pset_to_algid(unsigned int pset){
  switch(pset){
    case 224: return PQS_HASH_ALGID_SHA2_224;
    case 256: return PQS_HASH_ALGID_SHA2_256;
    case 384: return PQS_HASH_ALGID_SHA2_384;
    case 512: return PQS_HASH_ALGID_SHA2_512;
    case 513: return PQS_HASH_ALGID_SHA2_512_224;
    case 514: return PQS_HASH_ALGID_SHA2_512_256;
    case 1224: return PQS_HASH_ALGID_SECURE_SHA2_224;
    case 1256: return PQS_HASH_ALGID_SECURE_SHA2_256;
    case 1384: return PQS_HASH_ALGID_SECURE_SHA2_384;
    case 1512: return PQS_HASH_ALGID_SECURE_SHA2_512;
    case 1513: return PQS_HASH_ALGID_SECURE_SHA2_512_224;
    case 1514: return PQS_HASH_ALGID_SECURE_SHA2_512_256;
    default: throw_exception(ERROR_PSET);
  }
  //unreachable();
  __builtin_unreachable();
}

//#define VALIDATE_SHA2_SECURE
#ifdef VALIDATE_SHA2_SECURE
uint32_t pqs_hash_sha2_secure_test();
int debug_level();
void debug_println32d(int min_level, const char*msg,uint32_t d){
  if(min_level<=debug_level()){
    LBMK_println32d(msg,d);
  }
}
void debug_print_buf(int min_level, const char*msg, const void*buf, unsigned int size){
  if(min_level<=debug_level()){
    LBMK_print32x(msg,(uintptr_t)buf,"");
    LBMK_print32d(" (",size," bytes)");
    LBMK_println_bytes(":",buf,size);
  }
}
#endif

#if PSET<1000
static void sha2(
  void* digest,
  const void*const message,
  size_t message_size
){
  #ifdef VALIDATE_SHA2_SECURE
  uint32_t status = pqs_hash_sha2_secure_test();
  if(status) throw_exception(ERROR_SANITY_CHECK | status);
  #endif
  const unsigned int algid = pset_to_algid(PSET);
  const struct pqs_hash_impl *impl = pqs_hash_get_impl(algid);
  const unsigned int digest_size = pset_to_digest_size(PSET);

  uint8_t *const shares[] = {(uint8_t *)message};
  struct pqs_hash_data data_in = {
    .data = shares,
    .num_shares = 1,
    .data_len = message_size
  };
  uint8_t *const out_shares[] = {digest};
  struct pqs_hash_data data_out = {
    .data = out_shares,
    .num_shares = 1,
    .data_len = digest_size
  };
  pqs_hash_oneshot(impl,&data_in,&data_out);
}
#else
static void sha2_secure(
  void* digest,
  const void*const share0,
  const void*const share1,
  size_t message_size
){

  const unsigned int algid = pset_to_algid(PSET);
  const struct pqs_hash_impl *impl = pqs_hash_get_impl(algid);
  const unsigned int digest_size = pset_to_digest_size(PSET);

  uint8_t *const shares[] = {(uint8_t *)share0,(uint8_t *)share1};
  struct pqs_hash_data data_in = {
    .data = shares,
    .num_shares = 2,
    .data_len = message_size
  };
  
  uint8_t *const out_shares[] = {digest};
  struct pqs_hash_data data_out = {
    .data = out_shares,
    .num_shares = 1,
    .data_len = digest_size
  };
  pqs_hash_oneshot(impl,&data_in,&data_out);
}
#endif
