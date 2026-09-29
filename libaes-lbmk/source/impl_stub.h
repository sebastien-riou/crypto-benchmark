#pragma once

#define IMPL_NAME "stub"
#include <lean-benchmark/lean-benchmark.h>

static void aes_init(void){
}

static uint32_t aes_cmac_verify(
  const void*const tag,
  const void*const message,
  size_t message_size,
  const void*const key
){
  LBMK_touch_pointers(4, tag, message, &message_size, key);
  return 0;
}
