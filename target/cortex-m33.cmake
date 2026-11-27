include("${CMAKE_CURRENT_LIST_DIR}/gcc-arm-none-eabi.cmake")
set(CMAKE_SYSTEM_PROCESSOR armv8-m)

# Core MCU flags, CPU, instruction set and FPU setup
set(cpu_PARAMS ${cpu_PARAMS}
    # the cflags of the lean-bsp targets for this CPU (nucleo-u5a5, nucleo-l552; pico2 writes
    # -march=armv8-m.main+fp+dsp instead of -mfpu, which gives the same multilib and predefined macros), so that
    # the footprint, Renode and the boards describe the same code. softfp: the startup enables the FPU (startup.s)
    # In the BSPs' order: LTO objects record their options, so the same flags in another order change the objects.
    -mcpu=cortex-m33
    -mthumb
    -mfpu=fpv5-sp-d16
    -mfloat-abi=softfp
)
