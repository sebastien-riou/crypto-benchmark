include("${CMAKE_CURRENT_LIST_DIR}/../cortex-m7.cmake")
set(TARGET_DIR ${CMAKE_CURRENT_SOURCE_DIR}/target/cortex-m7)


set(linker_script_SRC ${CMAKE_CURRENT_SOURCE_DIR}/target/cortex-m7/generic.ld)

set(target_SRCS 
    ${TARGET_DIR}/startup.s
    ${TARGET_DIR}/hal.c
    ${TARGET_DIR}/syscall.c
    ${TARGET_DIR}/sysmem.c
)

set(target_include_c_DIRS 

)

set(linker_OPTS
    --specs=nosys.specs
    -Wl,-Map=${CMAKE_PROJECT_NAME}.map
    -Wl,--start-group
    -lc
    -lm
    -lstdc++
    -lsupc++
    -Wl,--end-group
    -Wl,-z,max-page-size=8 # Allow good software remapping across address space (with proper GCC section making)
    -Wl,--print-memory-usage
)