#include <stdint.h>
#include <stdbool.h>
#include <setjmp.h>
#include <string.h>
#include "error.h"
#include "util.h"

//Application level HAL
void init(int argc, const char*argv[]);
void com_tx(const void *const buf, unsigned int size);
#ifdef HAS_DELAY_MS
void delay_ms(unsigned int ms);
#endif

#define xstr(s) str(s)
#define str(s) #s

void lean_benchmark(unsigned int ninfo, const char*info[], bool run_forever);
int main(int argc, const char*argv[]) {
  init(argc,argv);
  const char*hw_info[] = {
    "hw_platform", xstr(CPU),
  };
  lean_benchmark(2,hw_info,0);
  const char*done = "done\n";
  com_tx(done,strlen(done));
  #ifdef HAS_DELAY_MS
  delay_ms(200);//give time to the transmission to complete
  #endif
  return 0;
}
