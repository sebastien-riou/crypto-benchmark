#pragma once

#define IMPL_NAME "stub"
#include <lean-benchmark/lean-benchmark.h>

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
#if PSET<1000
static void sha2(
  void* digest,
  const void*const message,
  size_t message_size
){
  LBMK_touch_pointers(3, digest, message, &message_size);
}
#else
static void sha2_secure(
  void* digest,
  const void*const share0,
  const void*const share1,
  size_t message_size
){
  LBMK_touch_pointers(3, digest, share0, share1, &message_size);
}
#endif


