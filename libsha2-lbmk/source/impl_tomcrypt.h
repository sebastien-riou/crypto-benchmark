#pragma once

#define IMPL_NAME "libtomcrypt"

#define LTC_API_PREFIX ltc
#include <libtomcrypt/tomcrypt.h>

typedef void (*sha2_t)(void* digest,
  const void*const message,
  size_t message_size);


static void sha2_256(void* digest,
  const void*const message,
  size_t message_size){
  hash_state md;
  ltc_sha256_init(&md);
  ltc_sha256_process(&md,message,message_size);
  ltc_sha256_done(&md,digest);
}

static void sha2(
  void* digest,
  const void*const message,
  size_t message_size){
  sha2_t impl;
  switch(PSET){
    case 256: impl = sha2_256;break;
    default: throw_exception(ERROR_NOT_IMPLEMENTED);
  }
  impl(digest, message, message_size);
}
