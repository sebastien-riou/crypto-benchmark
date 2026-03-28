OUTPUT_ARCH( "riscv" )
LD_FEATURE("SANE_EXPR")
/* Entry Point */
ENTRY(_start)

/* Highest address of the user mode stack */
_estack = ORIGIN(RAM) + LENGTH(RAM); /* end of "RAM" Ram type memory */

_Min_Heap_Size = 0x200; /* required amount of heap */
_Min_Stack_Size = 64*1024; /* required amount of stack */

/* Memories definition */
MEMORY
{
  RAM   (xrw)   : ORIGIN = 0x20000000, LENGTH = 2M
  FLASH (rx)    : ORIGIN = 0x00000000, LENGTH = 512K
}

/* Sections */
SECTIONS
{
  /* The program code and other data into "FLASH" Rom type memory */
  .text : ALIGN(8)
  {
    *(.text)           /* .text sections (code) */
    *(.text*)          /* .text* sections (code) */
    *(.eh_frame)
    __global_pointer$ = .;

    KEEP (*(.init))
    KEEP (*(.fini))
    . = ALIGN(8);
    _etext = .;        /* define a global symbols at end of code */
  } >FLASH

  /* Constant data into "FLASH" Rom type memory */
  .rodata : ALIGN(8)
  {
    *(.rodata)         /* .rodata sections (constants, strings, etc.) */
    *(.rodata*)        /* .rodata* sections (constants, strings, etc.) */
    *(.srodata*)        /* .rodata* sections (constants, strings, etc.) */
    . = ALIGN(8);
    _erodata = .;        /* define a global symbols at end of code */
  } >FLASH

  /* Initialized data sections into "RAM" Ram type memory */
  .data :
  {
    _sdata = .;        /* create a global symbol at data start */
    *(.data)           /* .data sections */
    *(.data*)          /* .data* sections */
    *(.sdata*)         /* .sdata* sections */
    *(.RamFunc)        /* .RamFunc sections */
    *(.RamFunc*)       /* .RamFunc* sections */

    _edata = .;        /* define a global symbol at data end */
  } >RAM AT>FLASH

  /* Used by the startup to initialize data */
  _sidata = LOADADDR(.data);

  /* Zero initialized data section into "RAM" Ram type memory */
  .bss :
  {
    /* This is used by the startup in order to initialize the .bss section */
    _sbss = .;         /* define a global symbol at bss start */
    __bss_start = _sbss;
    *(.bss)
    *(.bss*)
    *(.sbss*)
    *(COMMON)

    _ebss = .;         /* define a global symbol at bss end */
    __bss_end = _ebss;
  } >RAM

  /* User_heap_stack section, used to check that there is enough "RAM" Ram type memory left */
  ._user_heap_stack :
  {
    . = ALIGN(8);
    PROVIDE ( end = . );
    PROVIDE ( _end = . );
    . = . + _Min_Heap_Size;
    . = . + _Min_Stack_Size;
    . = ALIGN(8);
  } >RAM

  /* Remove information from the compiler libraries */
  /DISCARD/ :
  {
    libc.a ( * )
    libm.a ( * )
    libgcc.a ( * )
  }
}
