include("${CMAKE_CURRENT_LIST_DIR}/../rv64imc.cmake")
set(TARGET_NAME rv64imc)
set(TARGET_DIR ${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME})


set(linker_script_SRC ${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME}/link.ld)

set(target_SRCS 
	${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME}/startup.s
	${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME}/hal.c
    #${CMAKE_CURRENT_SOURCE_DIR}/target/${TARGET_NAME}/fips202_rv64im.S
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