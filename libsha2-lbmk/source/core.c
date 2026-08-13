#include <setjmp.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "lbmk.h"

static jmp_buf main_exception_ctx;
static jmp_buf*exception_ctx = &main_exception_ctx;
jmp_buf*get_exception_ctx(){
  return exception_ctx;
}
jmp_buf*set_exception_ctx(jmp_buf*new_exception_ctx){
  jmp_buf*old = exception_ctx;
  exception_ctx = new_exception_ctx;
  return old;
}
void throw_exception(uint32_t err_code){
  longjmp(*exception_ctx,err_code);
}

#define ERROR_PSET          0x40000000
#define ERROR_SANITY_CHECK  0x50000000
#define ERROR_MISC          0xFFF00000

#define ERROR_NOT_IMPLEMENTED 1

#define xstr(s) str(s)
#define str(s) #s

#define CONCAT_INNER(x,y) x ## y
#define CONCAT(x,y) CONCAT_INNER(x,y)
#define CAT3(x,y,z) CONCAT(x,CONCAT(y,z))
#define CAT(a,...) CAT_IMPL(a, __VA_ARGS__)
#define CAT_IMPL(a,...) a ## __VA_ARGS__

#define NELEM(x) (sizeof((x)) / sizeof((x)[0]))

//PSET
#ifndef PSET
#define PSET 256
#endif

#define DIGEST_SIZE CAT3(SHA2_,PSET,_DIGEST_SIZE)

#define IMPL_STUB 1
#define IMPL_PQCLE 2
#define IMPL_LIBTOMCRYPT 3
#define SHA2_LIB_INDEX CAT(IMPL_,SHA2_LIB)

#if SHA2_LIB_INDEX == IMPL_STUB
  #include "impl_stub.h"
#elif SHA2_LIB_INDEX == IMPL_PQCLE
  #include "impl_pqcle.h"
#elif SHA2_LIB_INDEX == IMPL_LIBTOMCRYPT
  #include "impl_tomcrypt.h"
#else
  #error "No implementation defined. To fix this, you need to define SHA2_LIB"
#endif

#ifndef SHA2_256_DIGEST_SIZE
  #define SHA2_224_DIGEST_SIZE (28)
  #define SHA2_256_DIGEST_SIZE (32)
  #define SHA2_384_DIGEST_SIZE (48)
  #define SHA2_512_DIGEST_SIZE (64)
  #define SHA2_512_224_DIGEST_SIZE (28)
  #define SHA2_512_256_DIGEST_SIZE (32)
#endif

#define SHA2_513_DIGEST_SIZE SHA2_512_224_DIGEST_SIZE
#define SHA2_514_DIGEST_SIZE SHA2_512_256_DIGEST_SIZE

#define SHA2_1224_DIGEST_SIZE SHA2_224_DIGEST_SIZE
#define SHA2_1256_DIGEST_SIZE SHA2_256_DIGEST_SIZE
#define SHA2_1384_DIGEST_SIZE SHA2_384_DIGEST_SIZE
#define SHA2_1512_DIGEST_SIZE SHA2_512_DIGEST_SIZE
#define SHA2_1513_DIGEST_SIZE SHA2_512_224_DIGEST_SIZE
#define SHA2_1514_DIGEST_SIZE SHA2_512_256_DIGEST_SIZE

static uint8_t digest[DIGEST_SIZE]={0};

static uint8_t message[10*1024] = {0};
#if PSET<1000
void sha2_1block(uintptr_t*args){
  args[0] = (uintptr_t)digest;
  args[1] = (uintptr_t)message;
  args[2] = 1;//message size = 1 byte
}
uint64_t sha2_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  void* digest=(void*)argsp[0];
  const void*const message=(const void*const)argsp[1];
  size_t message_size=argsp[2];
  sha2(digest,message,message_size);
  return 0;
} 
benchmark_setup_t sha2_1block_benchmark_setup = {
  .dut_name = "sha2",
  .dut = sha2_dut,
  .args_setup_name = "sha2_1block",
  .args_setup = sha2_1block,
  .nargs = 3,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = 0,
  .nextra_data = 0
};
#else
static uint8_t zeroes[10*1024] = {0};
void sha2_1block(uintptr_t*args){
  args[0] = (uintptr_t)digest;
  args[1] = (uintptr_t)message;
  args[2] = (uintptr_t)zeroes;
  args[3] = 1;
}
uint64_t sha2_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  void* digest=(void*)argsp[0];
  const void*const share0=(const void*const)argsp[1];
  const void*const share1=(const void*const)argsp[2];
  size_t message_size=argsp[3];
  sha2_secure(digest,share0,share1,message_size);
  return 0;
} 
benchmark_setup_t sha2_1block_benchmark_setup = {
  .dut_name = "sha2_secure",
  .dut = sha2_dut,
  .args_setup_name = "sha2_secure_1block",
  .args_setup = sha2_1block,
  .nargs = 4,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = 0,
  .nextra_data = 0
};
#endif

#if (PSET == 224 ) || (PSET == 1224)
const uint8_t expected[] = {0xff, 0xf9, 0x29, 0x2b, 0x42, 0x01, 0x61, 0x7b, 0xdc, 0x4d, 0x30, 0x53, 0xfc, 0xe0, 0x27, 0x34, 0x16, 0x6a, 0x68, 0x3d, 0x7d, 0x85, 0x8a, 0x7f, 0x5f, 0x59, 0xb0, 0x73};
#endif

#if (PSET == 256 ) || (PSET == 1256)
const uint8_t expected[] = {0x6e, 0x34, 0x0b, 0x9c, 0xff, 0xb3, 0x7a, 0x98, 0x9c, 0xa5, 0x44, 0xe6, 0xbb, 0x78, 0x0a, 0x2c, 0x78, 0x90, 0x1d, 0x3f, 0xb3, 0x37, 0x38, 0x76, 0x85, 0x11, 0xa3, 0x06, 0x17, 0xaf, 0xa0, 0x1d};
#endif

#if (PSET == 384 ) || (PSET == 1384)
const uint8_t expected[] = {0xbe, 0xc0, 0x21, 0xb4, 0xf3, 0x68, 0xe3, 0x06, 0x91, 0x34, 0xe0, 0x12, 0xc2, 0xb4, 0x30, 0x70, 0x83, 0xd3, 0xa9, 0xbd, 0xd2, 0x06, 0xe2, 0x4e, 0x5f, 0x0d, 0x86, 0xe1, 0x3d, 0x66, 0x36, 0x65, 0x59, 0x33, 0xec, 0x2b, 0x41, 0x34, 0x65, 0x96, 0x68, 0x17, 0xa9, 0xc2, 0x08, 0xa1, 0x17, 0x17};
#endif

#if (PSET == 512 ) || (PSET == 1512)
const uint8_t expected[] = {0xb8,0x24,0x4d,0x02,0x89,0x81,0xd6,0x93,0xaf,0x7b,0x45,0x6a,0xf8,0xef,0xa4,0xca,0xd6,0x3d,0x28,0x2e,0x19,0xff,0x14,0x94,0x2c,0x24,0x6e,0x50,0xd9,0x35,0x1d,0x22,0x70,0x4a,0x80,0x2a,0x71,0xc3,0x58,0x0b,0x63,0x70,0xde,0x4c,0xeb,0x29,0x3c,0x32,0x4a,0x84,0x23,0x34,0x25,0x57,0xd4,0xe5,0xc3,0x84,0x38,0xf0,0xe3,0x69,0x10,0xee};
#endif

#if (PSET == 513 ) || (PSET == 1513)
const uint8_t expected[] = {0x28, 0x3b, 0xb5, 0x9a, 0xf7, 0x08, 0x1e, 0xd0, 0x81, 0x97, 0x22, 0x7d, 0x8f, 0x65, 0xb9, 0x59, 0x1f, 0xfe, 0x11, 0x55, 0xbe, 0x43, 0xe9, 0x55, 0x0e, 0x57, 0xf9, 0x41};
#endif

#if (PSET == 514 ) || (PSET == 1514)
const uint8_t expected[] = {0x10, 0xba, 0xad, 0x17, 0x13, 0x56, 0x6a, 0xc2, 0x33, 0x34, 0x67, 0xbd, 0xdb, 0x05, 0x97, 0xde, 0xc9, 0x06, 0x61, 0x20, 0xdd, 0x72, 0xac, 0x2d, 0xcb, 0x83, 0x94, 0x22, 0x1d, 0xcb, 0xe4, 0x3d};
#endif

void lean_benchmark(unsigned int ninfo, const char*info[], bool run_forever){
  const char*sw_build_info[] = {
    "sw_target_cpu", xstr(CPU),
    "algo", "sha2",
    "pset", xstr(PSET),
    "impl_name", IMPL_NAME,
    "sw_version", xstr(GIT_VERSION),
    "tv_name", "default",
  };
  const unsigned int n_all_info = ninfo+NELEM(sw_build_info);
  const char*all_info[n_all_info];
  for(unsigned int i=0;i<ninfo;i++){
    all_info[i] = info[i];
  }
  for(unsigned int i=0;i<NELEM(sw_build_info);i++){
    all_info[ninfo+i] = sw_build_info[i];
  }
  uint32_t err_code=-1;
  if(0 == (err_code = setjmp((long long int*)exception_ctx))){
    while(1){
      LBMK_announce_start(NELEM(all_info),all_info);
      LBMK_benchmarkit(&sha2_1block_benchmark_setup,0);
      if(memcmp(digest,expected,DIGEST_SIZE)){
        throw_exception(ERROR_SANITY_CHECK);
      }
      LBMK_announce_end();
      if(!run_forever) break;
    }
    LBMK_println("done");
  }else{
    LBMK_println("");
    LBMK_println("EXCEPTION");
    LBMK_println32x("Error code: 0x",err_code);
    LBMK_println_bytes("Expected: ",expected,DIGEST_SIZE);
    LBMK_println_bytes("Digest:   ",digest,DIGEST_SIZE);
  }
}

