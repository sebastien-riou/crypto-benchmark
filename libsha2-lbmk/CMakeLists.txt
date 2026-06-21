

set(LIB sha2-lbmk-core)

add_library(${LIB} STATIC 
    ${CMAKE_CURRENT_SOURCE_DIR}/source/core.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/../common/sha-256.c
)

if(NOT DEFINED PSET)
set(PSET 256)
ENDIF()
MESSAGE("PSET=" ${PSET})
ADD_DEFINITIONS(-DPSET=${PSET})

if(NOT DEFINED SHA2_LIB)
set(SHA2_LIB LIBTOMCRYPT)
ENDIF()
MESSAGE("SHA2_LIB=" ${SHA2_LIB})
ADD_DEFINITIONS(-DSHA2_LIB=${SHA2_LIB})

target_include_directories(${LIB}
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../common
    ${TARGET_DIR}
)

# Compiler options
target_compile_options(${LIB} PRIVATE
    ${cpu_PARAMS}
    ${compiler_OPTS}
    -Wall
    -Wextra
    -Wpedantic
    -Wno-unused-parameter
    $<$<COMPILE_LANGUAGE:C>: >
    $<$<COMPILE_LANGUAGE:CXX>:

    # -Wno-volatile
    # -Wold-style-cast
    # -Wuseless-cast
    # -Wsuggest-override
    >
    $<$<COMPILE_LANGUAGE:ASM>:-x assembler-with-cpp -MMD -MP>
    $<$<CONFIG:Debug>:-Og -g3 -ggdb>
    $<$<CONFIG:Release>:-Os -g0>
)

include("${CMAKE_CURRENT_LIST_DIR}/../cmake/git_version.cmake")
add_definitions( -DGIT_VERSION=${GIT_VERSION} )
add_definitions( -DVERSION_TIMESTAMP=${VERSION_TIMESTAMP} )
add_definitions( -DBUILD_TYPE=${CMAKE_BUILD_TYPE})

SET(LIB_NAME sha2-lbmk)
SET(LIB_FILE ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a)
SET(LIB_HEADER_FOLDER ${CMAKE_CURRENT_SOURCE_DIR}/include)

IF(${SHA2_LIB} STREQUAL "STUB")
MESSAGE("SHA2_LIB is STUB")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:sha2-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("SHA2_LIB is NOT STUB (it is '" ${SHA2_LIB} "')")
ENDIF()

IF(${SHA2_LIB} STREQUAL "PQCLE")
MESSAGE("SHA2_LIB is PQCLE")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:sha2-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libhash.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libsha2.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libsha2_secure.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libsha3.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libcommon.a 
        #detect non constant time instruction in Cortex-M3
        COMMAND ${CMAKE_OBJDUMP} -D --visualize-jumps *.${CMAKE_AR_O_EXT} > disassembly.asm
        COMMAND grep smull disassembly.asm >> non_ct.report || true
        COMMAND grep umull disassembly.asm >> non_ct.report || true
        COMMAND grep smlal disassembly.asm >> non_ct.report || true
        COMMAND grep umlal disassembly.asm >> non_ct.report || true
        COMMAND grep sdiv disassembly.asm >> non_ct.report || true
        COMMAND grep udiv disassembly.asm >> non_ct.report || true
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
    MESSAGE("SHA2_LIB is NOT PQCLE (it is '" ${SHA2_LIB} "')")
ENDIF()

IF(${SHA2_LIB} STREQUAL "LIBTOMCRYPT")
MESSAGE("SHA2_LIB is LIBTOMCRYPT")

add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:sha2-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/libtomcrypt/libtomcrypt.a
        
        #detect non constant time instruction in Cortex-M3
        COMMAND ${CMAKE_OBJDUMP} -D --visualize-jumps *.${CMAKE_AR_O_EXT} > disassembly.asm
        COMMAND grep smull disassembly.asm >> non_ct.report || true
        COMMAND grep umull disassembly.asm >> non_ct.report || true
        COMMAND grep smlal disassembly.asm >> non_ct.report || true
        COMMAND grep umlal disassembly.asm >> non_ct.report || true
        COMMAND grep sdiv disassembly.asm >> non_ct.report || true
        COMMAND grep udiv disassembly.asm >> non_ct.report || true
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("SHA2_LIB is NOT LIBTOMCRYPT (it is '" ${SHA2_LIB} "')")
ENDIF()

add_library(${LIB_NAME} STATIC IMPORTED GLOBAL)
add_dependencies(${LIB_NAME} combined_target)

# specify where the library is and where to find the headers
set_target_properties(${LIB_NAME}
    PROPERTIES
    IMPORTED_LOCATION ${LIB_FILE}
    INTERFACE_INCLUDE_DIRECTORIES ${LIB_HEADER_FOLDER})

# Execute post-build copy the lib with most generic name and most specific name
add_custom_command(TARGET combined_target POST_BUILD
    COMMAND cp ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a ${CMAKE_BINARY_DIR}/libcrypto-benchmark.a
    COMMAND cp ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a ${CMAKE_BINARY_DIR}/../../libcrypto-benchmark.a
    COMMAND cp ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a ${CMAKE_BINARY_DIR}/../../libcrypto-benchmark-${SHA2_LIB}-${ALGO}-${PSET}.a
)