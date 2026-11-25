#pragma once

#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/settings.h>
#include <wolfssl/wolfcrypt/cmac.h>

#ifndef WOLFSSL_CMAC
  #error "WOLFSSL built without CMAC (rebuild it: see crypto-libraries/wolfssl.py)"
#endif

//what each goal is made of is defined in crypto-libraries/wolfssl.py, which builds the library (benchmark.py, or
//"python3 goals.py build WOLFSSL <target> aes <pset> <goal>"); the checks below reject a library built otherwise.
//A build with options (GOAL_CUSTOM) may differ from its goal's configuration.
#define WOLFSSL_smallcode 1
#define WOLFSSL_fast 2

#define WOLFSSL_INDEX CAT(WOLFSSL_,GOAL)

#if WOLFSSL_INDEX == WOLFSSL_smallcode
  #define IMPL_NAME "wolfssl-smallcode"
  #if !GOAL_CUSTOM && !defined(WOLFSSL_AES_SMALL_TABLES)
    #error "wolfssl-smallcode expects a build with WOLFSSL_AES_SMALL_TABLES (see crypto-libraries/wolfssl.py)"
  #endif
#elif WOLFSSL_INDEX == WOLFSSL_fast
  #define IMPL_NAME "wolfssl-fast"
  #if !GOAL_CUSTOM && defined(WOLFSSL_AES_SMALL_TABLES)
    #error "wolfssl-fast expects a build without WOLFSSL_AES_SMALL_TABLES (see crypto-libraries/wolfssl.py)"
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
