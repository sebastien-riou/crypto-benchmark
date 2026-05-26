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
#define ERROR_KEY_GEN       0x10000000
#define ERROR_SIGN          0x20000000
#define ERROR_VERIFY        0x30000000
#define ERROR_PSET          0x40000000
#define ERROR_SANITY_CHECK  0x50000000
#define ERROR_MISC          0xFFF00000
#define ERROR_PUBLIC_KEY    0x00000001
#define ERROR_PRIVATE_KEY   0x00000002

#define ERROR_NOT_IMPLEMENTED 1

#define MLDSA44_SECRETKEYBYTES 2560
#define MLDSA44_PUBLICKEYBYTES 1312
#define MLDSA44_BYTES 2420

#define MLDSA65_SECRETKEYBYTES 4032
#define MLDSA65_PUBLICKEYBYTES 1952
#define MLDSA65_BYTES 3309

#define MLDSA87_SECRETKEYBYTES 4896
#define MLDSA87_PUBLICKEYBYTES 2592
#define MLDSA87_BYTES 4627

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
#define PSET 44
#endif

#define DSA_PRIVATE_KEY_SIZE CAT3(MLDSA,PSET,_SECRETKEYBYTES)
#define DSA_PUBLIC_KEY_SIZE CAT3(MLDSA,PSET,_PUBLICKEYBYTES)
#define DSA_SIG_SIZE CAT3(MLDSA,PSET,_BYTES)

#define IMPL_STUB 1
#define IMPL_PQCLE 2
#define IMPL_PQCRYSTALS_LOWRAM 3
#define IMPL_STM32PQC 4
#define IMPL_WOLFSSL 5
#define MLDSA_LIB_INDEX CAT(IMPL_,MLDSA_LIB)

#if MLDSA_LIB_INDEX == IMPL_STUB
  #include "impl_stub.h"
#elif MLDSA_LIB_INDEX == IMPL_PQCLE
  #include "impl_umldsa.h"
#elif MLDSA_LIB_INDEX == IMPL_PQCRYSTALS_LOWRAM
  #include "impl_pqcrystals_lowram.h"
#elif MLDSA_LIB_INDEX == IMPL_STM32PQC
  #include "impl_stm32pqc.h"
#elif MLDSA_LIB_INDEX == IMPL_WOLFSSL
  #include "impl_wolfssl.h"
#else
  #error "No implementation defined. To fix this, you need to define MLDSA_LIB"
#endif


typedef struct generic_mldsa_test_vectors_struct {
  const char* name;
	unsigned int mldsa_pset;
	const uint8_t*mldsa_seed;
	const uint8_t*sk;
	const uint8_t*pk;
	unsigned int nmessages;
	unsigned int message_size;
  const uint8_t *sign_messages;
	const uint8_t*sigs_sha256_digest;
} generic_mldsa_test_vectors_t;

#define GENERIC_TV(src) {\
  .name = src->name,\
  .mldsa_pset = src->mldsa_pset,\
  .mldsa_seed = src->mldsa_seed,\
	.sk = src->sk,\
	.pk = src->pk,\
	.nmessages = src->nmessages,\
	.message_size = src->message_size,\
	.sign_messages = (const uint8_t *)&(src->sign_messages),\
	.sigs_sha256_digest = src->sigs_sha256_digest\
}

const generic_mldsa_test_vectors_t *generic_tv;
uint8_t private_key[DSA_PRIVATE_KEY_SIZE]={0};
uint8_t public_key[DSA_PUBLIC_KEY_SIZE]={0};
uint8_t signature[DSA_SIG_SIZE]={0};
static size_t message_size;
void set_gpo0(unsigned int);

typedef void(*dsa_sign_t)(const void*const private_key,
  void* signature,
  const void*const message,
  size_t message_size);

#if PSET == 44
  #include "mldsa44-m69-h8517CD9D.c" 
  static const mldsa44_m69_test_vectors_t*tv = &mldsa44_m69_test_vectors;
  #include "mldsa44-m10K-h6AA1568B.c" 
  static const mldsa44_m10K_test_vectors_t*tv10K = &mldsa44_m10K_test_vectors;
  #include "mldsa44-m1M-h19FDA9AA.c" 
  static const mldsa44_m1M_test_vectors_t*tv1M = &mldsa44_m1M_test_vectors;
#endif

#if PSET == 65
  #include "mldsa65-m69-hCAD14C27.c"
  static const mldsa65_m69_test_vectors_t*tv = &mldsa65_m69_test_vectors;
  #include "mldsa65-m10K-h5DD83C7E.c" 
  static const mldsa65_m10K_test_vectors_t*tv10K = &mldsa65_m10K_test_vectors;
  #include "mldsa65-m1M-hDA428ED5.c" 
  static const mldsa65_m1M_test_vectors_t*tv1M = &mldsa65_m1M_test_vectors;
#endif

#if PSET == 87
  #include "mldsa87-m69-h7D444798.c"
  static const mldsa87_m69_test_vectors_t*tv = &mldsa87_m69_test_vectors;
  #include "mldsa87-m10K-hECF6652D.c" 
  static const mldsa87_m10K_test_vectors_t*tv10K = &mldsa87_m10K_test_vectors;
  #include "mldsa87-m1M-h89D1B828.c" 
  static const mldsa87_m1M_test_vectors_t*tv1M = &mldsa87_m1M_test_vectors;
#endif

static const uint8_t*tv_sign_message;
#ifndef MSG_MAX_SIZE
  #if LARGE_TV
    #define MSG_MAX_SIZE (1*1024*1024)
  #else
    #define MSG_MAX_SIZE (10*1024)
#endif
#endif 
static uint8_t message[MSG_MAX_SIZE] = {0};
void mldsa_gen_key(uintptr_t*args){
  args[0] = (uintptr_t)generic_tv->mldsa_seed;
}
void mldsa_sign(uintptr_t*args){
  args[0] = (uintptr_t)signature;
  args[1] = (uintptr_t)message;
  args[2] = generic_tv->message_size;
  message_size = generic_tv->message_size;
  memset(message,0,generic_tv->message_size);
  memcpy(message,tv_sign_message,8);
}
void mldsa_verify(uintptr_t*args){
  args[0] = (uintptr_t)signature;
  args[1] = (uintptr_t)message;
  args[2] = generic_tv->message_size;
  message_size = generic_tv->message_size;
  memset(message,0,generic_tv->message_size);
  memcpy(message,tv_sign_message,8);
}

uint64_t mldsa_gen_key_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  const void*const seed=(const void*const)argsp[0];
  dsa_gen_key_from_seed(PSET,seed);
  return 0;
} 
void mldsa_gen_key_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  dsa_get_public_key(public_key);
  if(memcmp(public_key,generic_tv->pk, sizeof public_key)){
    throw_exception(ERROR_SANITY_CHECK | ERROR_PUBLIC_KEY);
  }
  dsa_get_private_key(private_key);
  if(memcmp(private_key,generic_tv->sk, sizeof private_key)){
    throw_exception(ERROR_SANITY_CHECK | ERROR_PRIVATE_KEY);
  }
}
uint64_t mldsa_sign_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  void* signature=(void*)argsp[0];
  const void*const message=(const void*const)argsp[1];
  size_t message_size=argsp[2];
  dsa_sign(PSET,signature,message,message_size);
  return 0;
} 
void mldsa_sign_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  //LBMK_println_bytes("\n\r\nmsg: ",message, 8);
  //LBMK_println_bytes("\n\r\nsig: ",signature, 16);
  //LBMK_println_bytes("\n\r\npub: ",public_key, 16);
  if(dsa_verify(PSET,signature,message,message_size)){
    throw_exception(ERROR_VERIFY);
  }
}
uint64_t mldsa_verify_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  //const void*const public_key=(const void*const)argsp[0];
  void* signature=(void*)argsp[0];
  const void*const message=(const void*const)argsp[1];
  size_t message_size=argsp[2];
  return dsa_verify(PSET,signature,message,message_size);
} 
void mldsa_verify_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  //check if verify was succesful, we benchmark only succesful case
  if(output){
    throw_exception(ERROR_VERIFY);
  }
}

benchmark_setup_t mldsa_gen_key_benchmark_setup = {
  .dut_name = "mldsa_gen_key",
  .dut = mldsa_gen_key_dut,
  .args_setup_name = "mldsa_gen_key",
  .args_setup = mldsa_gen_key,
  .nargs = 1,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = mldsa_gen_key_post_exec,
  .nextra_data = 0
};
benchmark_setup_t mldsa_sign_benchmark_setup = {
  .dut_name = "mldsa_sign",
  .dut = mldsa_sign_dut,
  .args_setup_name = "mldsa_sign",
  .args_setup = mldsa_sign,
  .nargs = 3,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = mldsa_sign_post_exec,
  .nextra_data = 0
};
benchmark_setup_t mldsa_verify_benchmark_setup = {
  .dut_name = "mldsa_verify",
  .dut = mldsa_verify_dut,
  .args_setup_name = "mldsa_verify",
  .args_setup = mldsa_verify,
  .nargs = 3,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = mldsa_verify_post_exec,
  .nextra_data = 0
};

#include "sha-256.h"
uint8_t sigs_digest[32];

void benchmarkit(benchmark_setup_t*sign, benchmark_setup_t*verify, const generic_mldsa_test_vectors_t *tv){
  generic_tv = tv;
  LBMK_benchmarkit(&mldsa_gen_key_benchmark_setup,0);

  memset(sigs_digest,0,sizeof sigs_digest);
  struct Sha_256 sha_256;
  sha_256_init(&sha_256, sigs_digest);

  for(unsigned int index = 0;index < tv->nmessages; index++){
    tv_sign_message = (const uint8_t*)&(tv->sign_messages[index*8]);
    LBMK_benchmarkit(sign,index);
    LBMK_benchmarkit(verify,index);
    //LBMK_println_bytes("\n\r\nmsg: ",tv_sign_message, 8);
    //LBMK_println_bytes("\n\r\nsig: ",signature, 16);
    sha_256_write(&sha_256, signature, sizeof signature);
  }

  //sanity check
  sha_256_close(&sha_256);
  if(memcmp(sigs_digest,tv->sigs_sha256_digest, sizeof sigs_digest)){
    throw_exception(ERROR_MISC | __LINE__);
  }
}

void lean_benchmark(unsigned int ninfo, const char*info[], bool run_forever){
  const char*sw_build_info[] = {
    "sw_target_cpu", xstr(CPU),
    "mldsa_pset", xstr(PSET),
    "impl_name", IMPL_NAME,
    "sw_version", xstr(GIT_VERSION),
    "tv_name", tv->name,
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

      const bool msg69=1;
      const bool msg10K=(MSG_MAX_SIZE) >= 10*1024;
      const bool msg1M=(MSG_MAX_SIZE) >= 1*1024*1024;
      benchmark_setup_t*sign = &mldsa_sign_benchmark_setup;
      benchmark_setup_t*verify = &mldsa_verify_benchmark_setup;
      if(msg69){
        generic_mldsa_test_vectors_t generic_tv = GENERIC_TV(tv);
        sign->args_setup_name = "mldsa_sign69";
        verify->args_setup_name = "mldsa_verify69";
        benchmarkit(sign,verify,&generic_tv);
      }
      if(msg10K){
        generic_mldsa_test_vectors_t generic_tv = GENERIC_TV(tv10K);
        sign->args_setup_name = "mldsa_sign10K";
        verify->args_setup_name = "mldsa_verify10K";
        benchmarkit(sign,verify,&generic_tv);
      }
      if(msg1M){
        generic_mldsa_test_vectors_t generic_tv = GENERIC_TV(tv1M);
        sign->args_setup_name = "mldsa_sign1M";
        verify->args_setup_name = "mldsa_verify1M";
        benchmarkit(sign,verify,&generic_tv);
      }

      LBMK_announce_end();
      if(!run_forever) break;
    }
  }else{
    {
      const char*msg = "\n\r\nEXCEPTION ";
      LBMK_com_tx(msg,strlen(msg));
    }
    tx_u32_str(err_code);
    {
      const char*msg = "\n\r\n";
      LBMK_com_tx(msg,strlen(msg));
    }
  }
}
