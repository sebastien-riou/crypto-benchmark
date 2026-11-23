#pragma once

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/cmac.h>

#ifndef WOLFSSL_CMAC
  #error "WOLFSSL built without CMAC (use buildit-aes-<goal> in the wolfssl repo)"
#endif

//goal smallcode is built by wolfssl's buildit-aes-small (see crypto-libraries/wolfssl.py)
#define WOLFSSL_smallcode 1
#define WOLFSSL_fast 2

#define WOLFSSL_INDEX CAT(WOLFSSL_,GOAL)

#if WOLFSSL_INDEX == WOLFSSL_smallcode
  #define IMPL_NAME "wolfssl-smallcode"
  #ifndef WOLFSSL_AES_SMALL_TABLES
    #error "wolfssl-smallcode expects a build with WOLFSSL_AES_SMALL_TABLES (buildit-aes-small)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_fast
  #define IMPL_NAME "wolfssl-fast"
  #ifdef WOLFSSL_AES_SMALL_TABLES
    #error "wolfssl-fast expects a build without WOLFSSL_AES_SMALL_TABLES (buildit-aes-fast)"
  #endif
#else
  #error "WOLFSSL AES-CMAC supports GOAL smallcode or fast"
#endif

static void aes_init(void){
}

static uint32_t aes_cmac_verify(
  const void*const tag,
  const void*const message,
  size_t message_size,
  const void*const key
){
  const int r = wc_AesCmacVerify(tag, AES_CMAC_TAG_SIZE, message, (word32)message_size, key, AES_KEY_SIZE);
  return r != 0;
}
