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

#define ERROR_LIB_INIT      0x01000000
#define ERROR_VERIFY        0x30000000
#define ERROR_PSET          0x40000000
#define ERROR_SANITY_CHECK  0x50000000
#define ERROR_MISC          0xFFF00000

#define xstr(s) str(s)
#define str(s) #s

#define CONCAT_INNER(x,y) x ## y
#define CONCAT(x,y) CONCAT_INNER(x,y)
#define CAT3(x,y,z) CONCAT(x,CONCAT(y,z))
#define CAT(a,...) CAT_IMPL(a, __VA_ARGS__)
#define CAT_IMPL(a,...) a ## __VA_ARGS__

#define NELEM(x) (sizeof((x)) / sizeof((x)[0]))

//PSET is the AES key size in bits
#ifndef PSET
#define PSET 128
#endif

#if PSET != 128
  #error "Only AES-128 is supported (PSET=128)"
#endif

#define AES_KEY_SIZE (PSET/8)
#define AES_CMAC_TAG_SIZE 16

#define IMPL_STUB 1
#define IMPL_STM32PQC 2
#define IMPL_WOLFSSL 3
#define AES_LIB_INDEX CAT(IMPL_,AES_LIB)

//each implementation provides:
//  aes_init(): one-time library initialization, not benchmarked
//  aes_cmac_verify(tag,message,message_size,key): returns 0 if the tag is valid
#if AES_LIB_INDEX == IMPL_STUB
  #include "impl_stub.h"
#elif AES_LIB_INDEX == IMPL_STM32PQC
  #include "impl_stm32pqc.h"
#elif AES_LIB_INDEX == IMPL_WOLFSSL
  #include "impl_wolfssl.h"
#else
  #error "No implementation defined. To fix this, you need to define AES_LIB"
#endif

//NIST SP 800-38B appendix D.1, examples 2 and 4 (also RFC 4493 section 4)
//they share the key, example 2 uses the first 16 bytes of the example 4 message
static const uint8_t key[AES_KEY_SIZE] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};
static const uint8_t message[64] = {
  0x6b, 0xc1, 0xbe, 0xe2, 0x2e, 0x40, 0x9f, 0x96, 0xe9, 0x3d, 0x7e, 0x11, 0x73, 0x93, 0x17, 0x2a,
  0xae, 0x2d, 0x8a, 0x57, 0x1e, 0x03, 0xac, 0x9c, 0x9e, 0xb7, 0x6f, 0xac, 0x45, 0xaf, 0x8e, 0x51,
  0x30, 0xc8, 0x1c, 0x46, 0xa3, 0x5c, 0xe4, 0x11, 0xe5, 0xfb, 0xc1, 0x19, 0x1a, 0x0a, 0x52, 0xef,
  0xf6, 0x9f, 0x24, 0x45, 0xdf, 0x4f, 0x9b, 0x17, 0xad, 0x2b, 0x41, 0x7b, 0xe6, 0x6c, 0x37, 0x10
};
static const uint8_t tag16[AES_CMAC_TAG_SIZE] = {
  0x07, 0x0a, 0x16, 0xb4, 0x6b, 0x4d, 0x41, 0x44, 0xf7, 0x9b, 0xdd, 0x9d, 0xd0, 0x4a, 0x28, 0x7c
};
static const uint8_t tag64[AES_CMAC_TAG_SIZE] = {
  0x51, 0xf0, 0xbe, 0xbf, 0x7e, 0x3b, 0x9d, 0x92, 0xfc, 0x49, 0x74, 0x17, 0x79, 0x36, 0x3c, 0xfe
};

void aes_cmac_verify64(uintptr_t*args){
  args[0] = (uintptr_t)tag64;
  args[1] = (uintptr_t)message;
  args[2] = sizeof(message);
  args[3] = (uintptr_t)key;
}
uint64_t aes_cmac_verify_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  const void*const tag=(const void*const)argsp[0];
  const void*const message=(const void*const)argsp[1];
  size_t message_size=argsp[2];
  const void*const key=(const void*const)argsp[3];
  return aes_cmac_verify(tag,message,message_size,key);
}
void aes_cmac_verify_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  //check if verify was succesful, we benchmark only succesful case
  if(output){
    throw_exception(ERROR_VERIFY);
  }
}
benchmark_setup_t aes_cmac_verify64_benchmark_setup = {
  .dut_name = "aes_cmac_verify",
  .dut = aes_cmac_verify_dut,
  .args_setup_name = "aes_cmac_verify64",
  .args_setup = aes_cmac_verify64,
  .nargs = 4,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = aes_cmac_verify_post_exec,
  .nextra_data = 0
};

//16 bytes message with several tags: case 0 is the correct tag, case i (1..16) is the correct
//tag with byte i-1 corrupted. Comparing cases shows whether timing depends on where the tag differs.
#define TAG_CASES (1+AES_CMAC_TAG_SIZE)
static unsigned int tag_case;
static uint8_t candidate_tag[AES_CMAC_TAG_SIZE];

void aes_cmac_verify16_tags(uintptr_t*args){
  memcpy(candidate_tag,tag16,sizeof(candidate_tag));
  if(tag_case){
    candidate_tag[tag_case-1] ^= 1;
  }
  args[0] = (uintptr_t)candidate_tag;
  args[1] = (uintptr_t)message;
  args[2] = 16;
  args[3] = (uintptr_t)key;
}
void aes_cmac_verify16_tags_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  const bool accepted = 0 == output;
  const bool must_accept = 0 == tag_case;
  if(accepted != must_accept){
    throw_exception(ERROR_VERIFY | tag_case);
  }
}
benchmark_setup_t aes_cmac_verify16_tags_benchmark_setup = {
  .dut_name = "aes_cmac_verify",
  .dut = aes_cmac_verify_dut,
  .args_setup_name = "aes_cmac_verify16_tags",
  .args_setup = aes_cmac_verify16_tags,
  .nargs = 4,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = aes_cmac_verify16_tags_post_exec,
  .nextra_data = 0
};

void lean_benchmark(unsigned int ninfo, const char*info[], bool run_forever){
  const char*sw_build_info[] = {
    "sw_target_cpu", xstr(CPU),
    "algo", "aes",
    "pset", xstr(PSET),
    "impl_name", IMPL_NAME,
    "sw_version", xstr(GIT_VERSION),
    "tv_name", "sp800-38b",
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
    aes_init();
    while(1){
      LBMK_announce_start(NELEM(all_info),all_info);
      LBMK_benchmarkit(&aes_cmac_verify64_benchmark_setup,0);
      for(tag_case=0;tag_case<TAG_CASES;tag_case++){
        LBMK_benchmarkit(&aes_cmac_verify16_tags_benchmark_setup,tag_case);
      }
      LBMK_announce_end();
      if(!run_forever) break;
    }
    LBMK_println("done");
  }else{
    LBMK_println("");
    LBMK_println("EXCEPTION");
    LBMK_println32x("Error code: 0x",err_code);
  }
}
