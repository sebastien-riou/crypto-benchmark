
include("${CMAKE_CURRENT_LIST_DIR}/gcc-riscv-none-elf.cmake")
set(CMAKE_SYSTEM_PROCESSOR riscv32)

# Core MCU flags, CPU, instruction set and FPU setup
set(cpu_PARAMS ${cpu_PARAMS}
  -mabi=ilp32 
  # the cflags of lean-bsp-pico2's rv32imcb target (Hazard3, as pico-sdk sets them), so that the footprint,
  # Renode and the board describe the same code. The Hazard3 has no Zbc, Zbkc or Zbkx.
  -march=rv32imac_zicsr_zifencei_zba_zbb_zbs_zbkb
)