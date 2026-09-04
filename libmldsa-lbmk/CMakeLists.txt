

set(LIB mldsa-lbmk-core)

add_library(${LIB} STATIC 
    ${CMAKE_CURRENT_SOURCE_DIR}/source/core.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/../common/sha-256.c
)

#OPTION(PSET "MLDSA parameter set [44,65,87]" 44)
if(NOT DEFINED PSET)
set(PSET 44)
ENDIF()
MESSAGE("PSET=" ${PSET})
ADD_DEFINITIONS(-DPSET=${PSET})

#OPTION(MLDSA_LIB "MLDSA implementation [PQCLE,PQCRYSTALS_LOWRAM]" PQCRYSTALS_LOWRAM) # set "cmake -DMLDSA_LIB=PQCRYSTALS_LOWRAM .."
if(NOT DEFINED MLDSA_LIB)
set(MLDSA_LIB PQCRYSTALS_LOWRAM)
ENDIF()
MESSAGE("MLDSA_LIB=" ${MLDSA_LIB})
ADD_DEFINITIONS(-DMLDSA_LIB=${MLDSA_LIB})

set( EXTRA_INCLUDES "" )

IF ( ${MLDSA_LIB} STREQUAL "STM32PQC" )
	set( EXTRA_INCLUDES 
        ${TARGET_DIR}/stm32pqc/include
    )
ENDIF()

# OPTION(IMPL_PQCLE "use PQCLE implementation" OFF) # Disabled by default, activate using "cmake -DIMPL_PQCLE=ON .."
# MESSAGE("IMPL_PQCLE=" ${IMPL_PQCLE})
# IF(IMPL_PQCLE)
#     ADD_DEFINITIONS(-DIMPL_PQCLE)
# ENDIF(IMPL_PQCLE)

# OPTION(IMPL_PQCRYSTALS_LOWRAM "use pqcrystals lowram implementation" OFF)
# MESSAGE("IMPL_PQCRYSTALS_LOWRAM=" ${IMPL_PQCRYSTALS_LOWRAM})
# IF(IMPL_PQCRYSTALS_LOWRAM)
#     ADD_DEFINITIONS(-DIMPL_PQCRYSTALS_LOWRAM)
# ENDIF(IMPL_PQCRYSTALS_LOWRAM)

target_include_directories(${LIB}
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../common
    ${TARGET_DIR}
    ${EXTRA_INCLUDES}
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

SET(LIB_NAME mldsa-lbmk)
SET(LIB_FILE ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a)
SET(LIB_HEADER_FOLDER ${CMAKE_CURRENT_SOURCE_DIR}/include)

IF(${MLDSA_LIB} STREQUAL "STUB")
MESSAGE("MLDSA_LIB is STUB")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT STUB (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "PQCLE")
MESSAGE("MLDSA_LIB is PQCLE")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libumldsa.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libhash.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libsha2.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libsha3.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcle/libprng.a 
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
    MESSAGE("MLDSA_LIB is NOT PQCLE (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "PQCRYSTALS_LOWRAM")
MESSAGE("MLDSA_LIB is PQCRYSTALS_LOWRAM")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        #COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcrystals_lowram/libmldsa_release_sha3_asm.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqcrystals-mldsa-lowram/libpqcrystals-mldsa-${PSET}-lowram.a
        
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
MESSAGE("MLDSA_LIB is NOT PQCRYSTALS_LOWRAM (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "STM32PQC")
MESSAGE("MLDSA_LIB is STM32PQC")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/stm32pqc/lib/libSTM32PQC_CM33.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/stm32pqc/lib/libSTM32Cryptographic_CM33.a
        
        #detect non constant time instruction in Cortex-M3
        COMMAND ${CMAKE_OBJDUMP} -D --visualize-jumps *.${CMAKE_AR_O_EXT} > disassembly.asm
        COMMAND grep smull disassembly.asm >> non_ct.report || true
        COMMAND grep umull disassembly.asm >> non_ct.report || true
        COMMAND grep smlal disassembly.asm >> non_ct.report || true
        COMMAND grep umlal disassembly.asm >> non_ct.report || true
        COMMAND grep sdiv disassembly.asm >> non_ct.report || true
        COMMAND grep udiv disassembly.asm >> non_ct.report || true
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT} *.o
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT STM32PQC (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "WOLFSSL")
MESSAGE("MLDSA_LIB is WOLFSSL")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/wolfssl/libwolfssl.a
        
        #detect non constant time instruction in Cortex-M3
        COMMAND ${CMAKE_OBJDUMP} -D --visualize-jumps *.${CMAKE_AR_O_EXT} > disassembly.asm
        COMMAND grep smull disassembly.asm >> non_ct.report || true
        COMMAND grep umull disassembly.asm >> non_ct.report || true
        COMMAND grep smlal disassembly.asm >> non_ct.report || true
        COMMAND grep umlal disassembly.asm >> non_ct.report || true
        COMMAND grep sdiv disassembly.asm >> non_ct.report || true
        COMMAND grep udiv disassembly.asm >> non_ct.report || true
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT} *.o
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT WOLFSSL (it is '" ${MLDSA_LIB} "')")
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
    COMMAND cp ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a ${CMAKE_BINARY_DIR}/../../libcrypto-benchmark-${MLDSA_LIB}-${ALGO}-${PSET}.a
)