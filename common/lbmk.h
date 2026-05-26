#pragma once


#include <lean-benchmark/lean-benchmark.h>
void com_tx(const void *const buf, unsigned int size);
void LBMK_com_tx(const void*data, unsigned int size){
  com_tx(data,size);
}

void com_rx(void *const buf, unsigned int size);
void LBMK_com_rx(void*const data, unsigned int size){
  com_rx(data,size);
}

void tx_u32_str(uint32_t val){
  const uint8_t*const val8 = (const uint8_t*const)&val;
  const uint8_t hex[] = {'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'};
  uint8_t buf[8];
  for(unsigned int i = 0;i<4;i++){
    uint8_t b = val8[3-i];
    uint8_t h = b >> 4;
    uint8_t l = b & 0xF;
    buf[2*i] = hex[h];
    buf[2*i+1] = hex[l];
  }
  LBMK_com_tx(buf,sizeof(buf));
}
