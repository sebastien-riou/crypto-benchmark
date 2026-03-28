#include <stdint.h>
#include <stdbool.h>

typedef struct
{
    uint32_t RxTx;
    uint32_t TxFull;
    uint32_t RxEmpty;
    uint32_t EventStatus;
    uint32_t EventPending;
    uint32_t EventEnable;
} UART;

const uint32_t TxEvent = 1;
const uint32_t RxEvent = 2;
volatile UART *const uart = (UART *)0x60001800;

//****************************************************************************

volatile unsigned int *DWT_CYCCNT   = (volatile unsigned int *)0xE0001004;
volatile unsigned int *DWT_CONTROL  = (volatile unsigned int *)0xE0001000;
volatile unsigned int *DWT_LAR      = (volatile unsigned int *)0xE0001FB0;
volatile unsigned int *SCB_DHCSR    = (volatile unsigned int *)0xE000EDF0;
volatile unsigned int *SCB_DEMCR    = (volatile unsigned int *)0xE000EDFC;
volatile unsigned int *ITM_TER      = (volatile unsigned int *)0xE0000E00;
volatile unsigned int *ITM_TCR      = (volatile unsigned int *)0xE0000E80;

volatile unsigned int *DWT_COMP0   = (volatile unsigned int *)0xE0001020;
volatile unsigned int *DWT_MASK0   = (volatile unsigned int *)0xE0001024;
volatile unsigned int *DWT_FUNC0   = (volatile unsigned int *)0xE0001028;
#define DWT_FUNC0_CYCMATCH 			(1<<7)
#define DWT_FUNC0_GEN_WATCHPOINT 	4
//****************************************************************************

static int Debug_ITMDebug = 0;

//****************************************************************************
volatile uint32_t dwt_comp = 15444020;//15444036
void EnableTiming(void){
  if ((*SCB_DHCSR & 1) && (*ITM_TER & 1)) // Enabled?
    Debug_ITMDebug = 1;

  *SCB_DEMCR |= 0x01000000;
  *DWT_LAR = 0xC5ACCE55; // enable access
  *DWT_CYCCNT = 0; // reset the counter

  //setup break point based on clock cycles
  *DWT_COMP0 = dwt_comp;
  *DWT_MASK0 = 0;
  //*DWT_FUNC0 = DWT_FUNC0_CYCMATCH | DWT_FUNC0_GEN_WATCHPOINT;


  *DWT_CONTROL |= 1 ; // enable the counter
}

uint64_t LBMK_get_cpu_timestamp(){
	return *DWT_CYCCNT;
}

void init(int argc, const char*argv[]){
  EnableTiming();
}
void led1(bool on){

}
bool button(){
    return false;
}
void com_tx(const void *const buf, unsigned int size){
    const uint8_t*const buf8 = (const uint8_t*const)buf;
    for(unsigned int i=0;i<size;i++){
        //wait tx buffer ready
        while (uart->TxFull);

        //send the byte
        uart->RxTx = buf8[i];
    }
}
void com_rx(void *const buf, unsigned int size){

}
void delay_ms(unsigned int ms){

}
