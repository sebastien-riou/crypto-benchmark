set(LIB aes-lbmk-core)

add_library(${LIB} STATIC
    ${CMAKE_CURRENT_SOURCE_DIR}/source/core.c
)

#PSET is the AES key size in bits
if(NOT DEFINED PSET)
set(PSET 128)
ENDIF()
MESSAGE("PSET=" ${PSET})
ADD_DEFINITIONS(-DPSET=${PSET})

if(NOT DEFINED AES_LIB)
MESSAGE( FATAL_ERROR "CRYPTO_LIB=${CRYPTO_LIB} has no AES implementation. Supported: STUB, STM32PQC, WOLFSSL" )
ENDIF()
MESSAGE("AES_LIB=" ${AES_LIB})
ADD_DEFINITIONS(-DAES_LIB=${AES_LIB})

set( EXTRA_INCLUDES "" )

get_filename_component(TARGET_CPU ${TARGET_DIR} NAME)

IF ( ${AES_LIB} STREQUAL "STM32PQC" )
	include(${CMAKE_SOURCE_DIR}/cmake/stm32_cryptographic.cmake)
	set( EXTRA_INCLUDES
        ${TARGET_DIR}/stm32pqc/include
    )
ENDIF()

# build-all-targets and buildit do not build external libraries, only benchmark.py does
IF ( ${AES_LIB} STREQUAL "WOLFSSL" )
	IF ( NOT EXISTS ${TARGET_DIR}/wolfssl/options.h )
		MESSAGE( FATAL_ERROR "wolfssl is not built for ${TARGET_CPU} with goal ${GOAL} (${TARGET_DIR}/wolfssl/options.h is missing). Run '(cd ../wolfssl && ./buildit-aes-${GOAL} ${TARGET_CPU})' then 'python3 link_ext.py --goal=${GOAL}'" )
	ENDIF()
ENDIF()

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

SET(LIB_NAME aes-lbmk)
SET(LIB_FILE ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a)
SET(LIB_HEADER_FOLDER ${CMAKE_CURRENT_SOURCE_DIR}/include)

IF(${AES_LIB} STREQUAL "STUB")
MESSAGE("AES_LIB is STUB")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:aes-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a

        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("AES_LIB is NOT STUB (it is '" ${AES_LIB} "')")
ENDIF()

IF(${AES_LIB} STREQUAL "STM32PQC")
MESSAGE("AES_LIB is STM32PQC")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:aes-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${STM32_CRYPTO_LIB}

        #build combined lib
        # the STM32 Cryptographic archives (V5) contain only .obj members, so there is no *.o to add
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("AES_LIB is NOT STM32PQC (it is '" ${AES_LIB} "')")
ENDIF()

IF(${AES_LIB} STREQUAL "WOLFSSL")
MESSAGE("AES_LIB is WOLFSSL")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:aes-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/wolfssl/libwolfssl.a

        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT} *.o
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("AES_LIB is NOT WOLFSSL (it is '" ${AES_LIB} "')")
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
    COMMAND cp ${CMAKE_BINARY_DIR}/lib${LIB_NAME}/lib${LIB_NAME}.a ${CMAKE_BINARY_DIR}/../../libcrypto-benchmark-${AES_LIB}-${ALGO}-${PSET}.a
)
