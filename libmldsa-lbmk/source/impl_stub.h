#pragma once

#define IMPL_NAME "stub"
#include <lean-benchmark/lean-benchmark.h>

//this function is called to set the key for subsequent get/sign/verify operations
//implement shall store the generated key as a global variable if not stored in hardware
static void dsa_gen_key_from_seed(
  const unsigned int pset,
  const void* seed
){
  LBMK_touch_pointers(2, &pset, seed);
}
static void dsa_get_private_key(void* private_key){
  LBMK_touch_pointers(1, private_key);
}
static void dsa_get_public_key(void* public_key){
  LBMK_touch_pointers(1, public_key);
}
static uint32_t dsa_verify(
  const unsigned int pset,
  const void*const signature,
  const void*const message,
  size_t message_size){
  LBMK_touch_pointers(4, &pset, signature, message);
  return 1;
}
static void dsa_sign(
  const unsigned int pset,
  void* signature,
  const void*const message,
  size_t message_size){
  LBMK_touch_pointers(4, &pset, signature, message, &message_size);
}



