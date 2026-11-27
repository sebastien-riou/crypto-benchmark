include("${CMAKE_CURRENT_LIST_DIR}/gcc-arm-none-eabi.cmake")
set(CMAKE_SYSTEM_PROCESSOR armv8-m)

# Core MCU flags, CPU, instruction set and FPU setup
set(cpu_PARAMS ${cpu_PARAMS}
    # the cflags of the lean-bsp targets for this CPU (numaker-m5531), so that the footprint and the board
    # describe the same code. -mfpu=auto: the M55's whole FPU (double precision too) and Helium (MVE).
    # softfp: the startup enables the FPU (startup.s)
    # In the BSPs' order: LTO objects record their options, so the same flags in another order change the objects.
    -mcpu=cortex-m55
    -mthumb
    -mfpu=auto
    -mfloat-abi=softfp
)
