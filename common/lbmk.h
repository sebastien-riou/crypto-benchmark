#pragma once


#include <lean-benchmark/lean-benchmark.h>

//What was built, for the info fields of every benchmark (set by CMakeLists.txt, read by format_results.py):
//the library, its goal, the options given on top of it (empty for a standard goal), the core set the library may
//use, and the library's revision. The revision is in an array of fixed size: a new one does not move the code.
#define LBMK_LIB_REV_SIZE 17
static const char lbmk_lib_rev[LBMK_LIB_REV_SIZE] = LIB_REV_STR;
#define LBMK_BUILD_INFO \
    "crypto_lib", LBMK_STR(CRYPTO_LIB), \
    "goal", LBMK_STR(GOAL), \
    "goal_opts", GOAL_OPTS_STR, \
    "cores", CORES_STR, \
    "lib_rev", lbmk_lib_rev
#define LBMK_STR_(s) #s
#define LBMK_STR(s) LBMK_STR_(s)
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
