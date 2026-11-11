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
#define ERROR_ENCAPS        0x20000000
#define ERROR_DECAPS        0x30000000
#define ERROR_PSET          0x40000000
#define ERROR_SANITY_CHECK  0x50000000
#define ERROR_MISC          0xFFF00000
//sanity check errors: ERROR_SANITY_CHECK | (case index << 8) | one of the following
#define ERROR_PUBLIC_KEY    0x00000001
#define ERROR_SECRET_KEY    0x00000002
#define ERROR_CIPHERTEXT    0x00000003
#define ERROR_SHARED_SECRET 0x00000004
#define ERROR_REJECT        0x00000005
#define ERROR_NO_DK_CHECK   0x00000006 //decapsulation accepted a key failing the FIPS 203 hash check
#define ERROR_NO_EK_CHECK   0x00000007 //encapsulation accepted a key failing the FIPS 203 modulus check

#define MLKEM512_SECRETKEYBYTES 1632
#define MLKEM512_PUBLICKEYBYTES 800
#define MLKEM512_CIPHERTEXTBYTES 768

#define MLKEM768_SECRETKEYBYTES 2400
#define MLKEM768_PUBLICKEYBYTES 1184
#define MLKEM768_CIPHERTEXTBYTES 1088

#define MLKEM1024_SECRETKEYBYTES 3168
#define MLKEM1024_PUBLICKEYBYTES 1568
#define MLKEM1024_CIPHERTEXTBYTES 1568

#define MLKEM_SHAREDSECRETBYTES 32
#define MLKEM_KEYGEN_SEEDBYTES 64 //d || z
#define MLKEM_ENCAPS_SEEDBYTES 32 //m

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
#define PSET 512
#endif

#if PSET != 512 && PSET != 768 && PSET != 1024
  #error "PSET must be 512, 768 or 1024"
#endif

#define KEM_SECRET_KEY_SIZE CAT3(MLKEM,PSET,_SECRETKEYBYTES)
#define KEM_PUBLIC_KEY_SIZE CAT3(MLKEM,PSET,_PUBLICKEYBYTES)
#define KEM_CIPHERTEXT_SIZE CAT3(MLKEM,PSET,_CIPHERTEXTBYTES)
#define KEM_SHARED_SECRET_SIZE MLKEM_SHAREDSECRETBYTES

#define IMPL_STUB 1
#define IMPL_PQCLE 2
#define IMPL_STM32PQC 3
#define IMPL_WOLFSSL 4
#define IMPL_PQRV 5
#define IMPL_EXTERNAL 6
#define MLKEM_LIB_INDEX CAT(IMPL_,MLKEM_LIB)

//for wrappers doing the FIPS 203 section 7.3 hash check: dk = dk_PKE || ek || H(ek) || z
#define ERROR_DK_CHECK 0x00DC0000 //with ERROR_DECAPS: the wrapper's hash check rejected the decapsulation key
#define KEM_DK_EK_OFFSET (KEM_SECRET_KEY_SIZE - KEM_PUBLIC_KEY_SIZE - 2*32)
#define KEM_DK_H_OFFSET  (KEM_SECRET_KEY_SIZE - 2*32)
//non-zero when h, the hash of the decapsulation key's ek, matches the H(ek) stored in it
__attribute__((unused)) static int kem_dk_hash_matches(const uint8_t h[32], const void*const secret_key){
  const uint8_t*const stored = (const uint8_t*)secret_key + KEM_DK_H_OFFSET;
  uint8_t d = 0;
  for(unsigned int i=0;i<32;i++) d |= h[i] ^ stored[i];
  return 0 == d;
}
//for wrappers doing the FIPS 203 section 7.2 modulus check, ek = ek_PKE || rho: non-zero when every 12-bit
//coefficient of ek_PKE is below q, i.e. ByteEncode_12(ByteDecode_12(ek_PKE)) == ek_PKE
#define ERROR_EK_CHECK 0x00EC0000 //with ERROR_ENCAPS: the wrapper's modulus check rejected the encapsulation key
__attribute__((unused)) static int kem_ek_modulus_ok(const void*const public_key){
  const uint8_t*p = (const uint8_t*)public_key;
  uint32_t bad = 0;
  for(unsigned int i=0;i<(KEM_PUBLIC_KEY_SIZE-32)/3;i++,p+=3){
    const uint32_t a = p[0] | ((uint32_t)(p[1] & 0x0F) << 8);
    const uint32_t b = (p[1] >> 4) | ((uint32_t)p[2] << 4);
    bad |= (3328 - a) | (3328 - b); //bit 31 set if a or b >= q = 3329
  }
  return 0 == (bad >> 31);
}

//each implementation provides:
//  kem_init(): one-time library initialization, not benchmarked
//  kem_keygen(seed,public_key,secret_key): deterministic key generation from d || z (FIPS 203 ML-KEM.KeyGen_internal)
//  kem_encaps(public_key,seed,ciphertext,shared_secret): deterministic encapsulation from m (FIPS 203 ML-KEM.Encaps_internal),
//    with the encapsulation key modulus check of FIPS 203 section 7.2: done by the library, or else by the wrapper.
//    A failed check throws ERROR_ENCAPS (check_key_checks verifies it).
//  kem_decaps(secret_key,ciphertext,shared_secret): decapsulation (FIPS 203 ML-KEM.Decaps_internal), with the
//    decapsulation key hash check of FIPS 203 section 7.3: done by the library, or else by the wrapper, with the
//    library's own SHA3-256 when it has one. A failed check throws ERROR_DECAPS (check_key_checks verifies it).
//keys and ciphertext are byte strings as specified by FIPS 203, any decoding/encoding is part of the benchmarked operation.
//errors are reported using throw_exception.
//optionally, an implementation can report extra data after each operation, it shall then define
//  KEM_NEXTRA_DATA: number of extra data items
//  kem_extra_data(extra_data_info): fill KEM_NEXTRA_DATA tlv_t
#if MLKEM_LIB_INDEX == IMPL_STUB
  #include "impl_stub.h"
#elif MLKEM_LIB_INDEX == IMPL_PQCLE
  #include "impl_umlkem.h"
#elif MLKEM_LIB_INDEX == IMPL_STM32PQC
  #include "impl_stm32pqc.h"
#elif MLKEM_LIB_INDEX == IMPL_WOLFSSL
  #include "impl_wolfssl.h"
#elif MLKEM_LIB_INDEX == IMPL_PQRV
  #include "impl_pqrv.h"
#elif MLKEM_LIB_INDEX == IMPL_EXTERNAL
  //in the folder of the external library (see "External libraries" in README.md)
  #include "impl_mlkem.h"
#else
  #error "No implementation defined. To fix this, you need to define MLKEM_LIB"
#endif

#ifndef KEM_NEXTRA_DATA
  #define KEM_NEXTRA_DATA 0
  static void kem_extra_data(tlv_t*extra_data_info){
  }
#endif

typedef struct {
  uint8_t keygen_seed[MLKEM_KEYGEN_SEEDBYTES];
  uint8_t encaps_seed[MLKEM_ENCAPS_SEEDBYTES];
  uint8_t pk_sha256[32];
  uint8_t sk_sha256[32];
  uint8_t ct_sha256[32];
  uint8_t ss[MLKEM_SHAREDSECRETBYTES];
  uint8_t ss_reject[MLKEM_SHAREDSECRETBYTES];//expected output of decaps on the corrupted ciphertext
} mlkem_test_case_t;

typedef struct {
  const char*name;
  unsigned int mlkem_pset;
  unsigned int ncases;
  const mlkem_test_case_t*cases;
} mlkem_test_vectors_t;

//generated by gen-tv.py
#if PSET == 512
  #include "mlkem512-n16-hA9D61CDB.c"
  static const mlkem_test_vectors_t*tv = &mlkem512_n16_test_vectors;
#endif
#if PSET == 768
  #include "mlkem768-n16-h99342E63.c"
  static const mlkem_test_vectors_t*tv = &mlkem768_n16_test_vectors;
#endif
#if PSET == 1024
  #include "mlkem1024-n16-hCDD815CA.c"
  static const mlkem_test_vectors_t*tv = &mlkem1024_n16_test_vectors;
#endif

#include "sha-256.h"

static const mlkem_test_case_t*tv_case;
static unsigned int tv_case_index;
//buffers exchanged with the implementation. identifiers in this file use a "bench_" prefix to avoid
//clashes with the libraries: wolfSSL for example has internal mlkem_* functions.
static uint8_t bench_public_key[KEM_PUBLIC_KEY_SIZE]={0};
static uint8_t bench_secret_key[KEM_SECRET_KEY_SIZE]={0};
static uint8_t bench_ciphertext[KEM_CIPHERTEXT_SIZE]={0};
static uint8_t bench_ciphertext_reject[KEM_CIPHERTEXT_SIZE]={0};
static uint8_t bench_shared_secret[KEM_SHARED_SECRET_SIZE]={0};

static void sanity_check(const void*const data, size_t size, const uint8_t expected_sha256[32], uint32_t err_code){
  uint8_t digest[32];
  calc_sha_256(digest, data, size);
  if(memcmp(digest,expected_sha256,sizeof digest)){
    throw_exception(ERROR_SANITY_CHECK | (tv_case_index << 8) | err_code);
  }
}
static void check_shared_secret(const uint8_t expected[KEM_SHARED_SECRET_SIZE], uint32_t err_code){
  if(memcmp(bench_shared_secret,expected,sizeof bench_shared_secret)){
    throw_exception(ERROR_SANITY_CHECK | (tv_case_index << 8) | err_code);
  }
}

//outputs are cleared before each trial so a trial cannot pass on the results of a previous one
static void bench_keygen_args(uintptr_t*args){
  memset(bench_public_key,0,sizeof bench_public_key);
  memset(bench_secret_key,0,sizeof bench_secret_key);
  args[0] = (uintptr_t)tv_case->keygen_seed;
  args[1] = (uintptr_t)bench_public_key;
  args[2] = (uintptr_t)bench_secret_key;
}
static uint64_t bench_keygen_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  const void*const seed=(const void*const)argsp[0];
  void*public_key=(void*)argsp[1];
  void*secret_key=(void*)argsp[2];
  kem_keygen(seed,public_key,secret_key);
  return 0;
}
static void bench_keygen_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  sanity_check(bench_public_key, sizeof bench_public_key, tv_case->pk_sha256, ERROR_PUBLIC_KEY);
  sanity_check(bench_secret_key, sizeof bench_secret_key, tv_case->sk_sha256, ERROR_SECRET_KEY);
  kem_extra_data(extra_data_info);
}

static void bench_encaps_args(uintptr_t*args){
  memset(bench_ciphertext,0,sizeof bench_ciphertext);
  memset(bench_shared_secret,0,sizeof bench_shared_secret);
  args[0] = (uintptr_t)bench_public_key;
  args[1] = (uintptr_t)tv_case->encaps_seed;
  args[2] = (uintptr_t)bench_ciphertext;
  args[3] = (uintptr_t)bench_shared_secret;
}
static uint64_t bench_encaps_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  const void*const public_key=(const void*const)argsp[0];
  const void*const seed=(const void*const)argsp[1];
  void*ciphertext=(void*)argsp[2];
  void*shared_secret=(void*)argsp[3];
  kem_encaps(public_key,seed,ciphertext,shared_secret);
  return 0;
}
static void bench_encaps_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  sanity_check(bench_ciphertext, sizeof bench_ciphertext, tv_case->ct_sha256, ERROR_CIPHERTEXT);
  check_shared_secret(tv_case->ss, ERROR_SHARED_SECRET);
  kem_extra_data(extra_data_info);
}

static void bench_decaps_args(uintptr_t*args){
  memset(bench_shared_secret,0,sizeof bench_shared_secret);
  args[0] = (uintptr_t)bench_secret_key;
  args[1] = (uintptr_t)bench_ciphertext;
  args[2] = (uintptr_t)bench_shared_secret;
}
//the ciphertext with bit 0 of its first byte flipped (gen-tv.py does the same)
//decaps shall not fail but output the implicit rejection shared secret J(z || c')
static void bench_decaps_reject_args(uintptr_t*args){
  memcpy(bench_ciphertext_reject,bench_ciphertext,sizeof bench_ciphertext_reject);
  bench_ciphertext_reject[0] ^= 1;
  memset(bench_shared_secret,0,sizeof bench_shared_secret);
  args[0] = (uintptr_t)bench_secret_key;
  args[1] = (uintptr_t)bench_ciphertext_reject;
  args[2] = (uintptr_t)bench_shared_secret;
}
static uint64_t bench_decaps_dut(uintptr_t*args){
  //anything here is part of the benchmark, so it should be just setting arguments
  uintptr_t*argsp = (uintptr_t*)args;
  const void*const secret_key=(const void*const)argsp[0];
  const void*const ciphertext=(const void*const)argsp[1];
  void*shared_secret=(void*)argsp[2];
  kem_decaps(secret_key,ciphertext,shared_secret);
  return 0;
}
static void bench_decaps_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  check_shared_secret(tv_case->ss, ERROR_SHARED_SECRET);
  kem_extra_data(extra_data_info);
}
static void bench_decaps_reject_post_exec(tlv_t*extra_data_info, uintptr_t*args,uint64_t output){
  check_shared_secret(tv_case->ss_reject, ERROR_REJECT);
  kem_extra_data(extra_data_info);
}

static benchmark_setup_t bench_keygen_setup = {
  .dut_name = "mlkem_keygen",
  .dut = bench_keygen_dut,
  .args_setup_name = "mlkem_keygen",
  .args_setup = bench_keygen_args,
  .nargs = 3,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = bench_keygen_post_exec,
  .nextra_data = KEM_NEXTRA_DATA
};
static benchmark_setup_t bench_encaps_setup = {
  .dut_name = "mlkem_encaps",
  .dut = bench_encaps_dut,
  .args_setup_name = "mlkem_encaps",
  .args_setup = bench_encaps_args,
  .nargs = 4,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = bench_encaps_post_exec,
  .nextra_data = KEM_NEXTRA_DATA
};
static benchmark_setup_t bench_decaps_setup = {
  .dut_name = "mlkem_decaps",
  .dut = bench_decaps_dut,
  .args_setup_name = "mlkem_decaps",
  .args_setup = bench_decaps_args,
  .nargs = 3,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = bench_decaps_post_exec,
  .nextra_data = KEM_NEXTRA_DATA
};
static benchmark_setup_t bench_decaps_reject_setup = {
  .dut_name = "mlkem_decaps",
  .dut = bench_decaps_dut,
  .args_setup_name = "mlkem_decaps_reject",
  .args_setup = bench_decaps_reject_args,
  .nargs = 3,
  .ntrials = 5,
  .max_stack_size = 40*1024,
  .post_exec = bench_decaps_reject_post_exec,
  .nextra_data = KEM_NEXTRA_DATA
};

//Every implementation is benchmarked with the input checks of FIPS 203:
//- section 7.2, encapsulation: the key ek = ek_PKE || rho is rejected when a coefficient of ek_PKE is not below q;
//- section 7.3, decapsulation: the key dk = dk_PKE || ek || H(ek) || z is rejected when its stored H(ek) does not
//  match ek.
//The library does them, or else its wrapper (impl_*.h) does them inside kem_encaps / kem_decaps, so they are part
//of the measured operations either way.
//This verifies both after the measurements of each pass, before their end is announced: an encapsulation or a
//decapsulation that accepts such a key stops the run with an exception, and the host records no results. It runs
//after the measurements so that their heap usage is not hidden: some platforms measure the growth of the heap end,
//which this would cause.
//The stub does nothing, so it cannot pass: it runs the same code without the verdict, which keeps the firmware the
//same apart from the library (the footprint is the size of a firmware minus that of the stub's).
static volatile uint8_t key_check_verdict = MLKEM_LIB_INDEX == IMPL_STUB ? 1 : 2; //non-zero: in .data for both
//decapsulation with a valid ciphertext and a key whose stored H(ek) is wrong
static void key_check_bad_dk(void){
  tv_case = &tv->cases[0];
  kem_keygen(tv_case->keygen_seed, bench_public_key, bench_secret_key);
  kem_encaps(bench_public_key, tv_case->encaps_seed, bench_ciphertext, bench_shared_secret);
  bench_secret_key[KEM_DK_H_OFFSET] ^= 1; //first byte of the stored H(ek)
  kem_decaps(bench_secret_key, bench_ciphertext, bench_shared_secret);
}
//encapsulation with the key of key_check_bad_dk, its first coefficient set to q
static void key_check_bad_ek(void){
  bench_public_key[0] = 0x01; //coefficient 0 is bench_public_key[0] | (bench_public_key[1] & 0x0F) << 8
  bench_public_key[1] = (bench_public_key[1] & 0xF0) | 0x0D; //0xD01 = q = 3329
  kem_encaps(bench_public_key, tv_case->encaps_seed, bench_ciphertext, bench_shared_secret);
}
//runs trial, returns the exception it throws, 0 if none
static uint32_t key_check_trial(void (*trial)(void)){
  jmp_buf ctx;
  jmp_buf*const outer = set_exception_ctx(&ctx);
  volatile uint32_t err;
  if(0 == (err = setjmp(ctx))){
    trial();
  }
  set_exception_ctx(outer);
  return err;
}
static void check_key_checks(void){
  const uint32_t dk_err = key_check_trial(key_check_bad_dk);
  const uint32_t ek_err = key_check_trial(key_check_bad_ek);
  if(2 != key_check_verdict){
    return;
  }
  if(0 == dk_err){
    throw_exception(ERROR_SANITY_CHECK | ERROR_NO_DK_CHECK);
  }
  if((dk_err & 0xF0000000) != ERROR_DECAPS){
    throw_exception(dk_err); //key generation or encapsulation failed
  }
  if(0 == ek_err){
    throw_exception(ERROR_SANITY_CHECK | ERROR_NO_EK_CHECK);
  }
  if((ek_err & 0xF0000000) != ERROR_ENCAPS){
    throw_exception(ek_err);
  }
}

void lean_benchmark(unsigned int ninfo, const char*info[], bool run_forever){
  const char*sw_build_info[] = {
    "sw_target_cpu", xstr(CPU),
    "algo", "mlkem",
    "pset", xstr(PSET),
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
    if(tv->mlkem_pset != PSET){
      throw_exception(ERROR_PSET);
    }
    kem_init();
    while(1){
      LBMK_announce_start(NELEM(all_info),all_info);
      //each operation uses the outputs of the previous one, checked by its post_exec function
      for(tv_case_index=0;tv_case_index<tv->ncases;tv_case_index++){
        tv_case = &tv->cases[tv_case_index];
        LBMK_benchmarkit(&bench_keygen_setup,tv_case_index);
        LBMK_benchmarkit(&bench_encaps_setup,tv_case_index);
        LBMK_benchmarkit(&bench_decaps_setup,tv_case_index);
        LBMK_benchmarkit(&bench_decaps_reject_setup,tv_case_index);
      }
      check_key_checks();
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
