include("${CMAKE_CURRENT_LIST_DIR}/../rv32imc.cmake")
set(TARGET_NAME rv32imc)
set(TARGET_DIR ${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME})


set(linker_script_SRC ${TARGET_DIR}/link.ld)

set(target_SRCS 
	${TARGET_DIR}/startup.s
	${TARGET_DIR}/hal.c
    ${TARGET_DIR}/syscall.c
    #${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME}/keccakf1600_asm.S #need more integration work
    #${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME}/fips202_rv32im.S
)

set(target_include_c_DIRS 

)

set(linker_OPTS
    --specs=nosys.specs
    -ffreestanding -nostdlib
    -Wl,-Map=${CMAKE_PROJECT_NAME}.map
    -Wl,--start-group
    -Wl,--end-group
    -Wl,-z,max-page-size=8 # Allow good software remapping across address space (with proper GCC section making)
    -Wl,--print-memory-usage
)