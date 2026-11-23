

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
	include(${CMAKE_SOURCE_DIR}/cmake/stm32_cryptographic.cmake)
	set( EXTRA_INCLUDES 
        ${TARGET_DIR}/stm32pqc/include
    )
ENDIF()

get_filename_component(TARGET_CPU ${TARGET_DIR} NAME)

IF ( ${MLDSA_LIB} STREQUAL "PQRV" )
	IF ( NOT EXISTS ${TARGET_DIR}/pqrv/libpqrv.a )
		MESSAGE( FATAL_ERROR "PQRV is not built for ${TARGET_CPU} (${TARGET_DIR}/pqrv/libpqrv.a is missing). Run '(cd ../PQRV/libpqrv && ./buildit ${TARGET_CPU})' then 'python3 link_ext.py'" )
	ENDIF()
ENDIF()

IF ( ${MLDSA_LIB} STREQUAL "EXTERNAL" )
	# sets EXTERNAL_MLDSA_ARCHIVES and optionally EXTERNAL_INCLUDE_DIRS
	include(${EXTERNAL_LIB_DIR}/mldsa.cmake)
	foreach( ARCHIVE ${EXTERNAL_MLDSA_ARCHIVES} )
		IF ( NOT EXISTS ${ARCHIVE} )
			MESSAGE( FATAL_ERROR "${CRYPTO_LIB} is not built for ${TARGET_CPU} (${ARCHIVE} is missing)" )
		ENDIF()
	endforeach()
	# impl_mldsa.h is in EXTERNAL_LIB_DIR
	set( EXTRA_INCLUDES
        ${EXTERNAL_LIB_DIR}
        ${EXTERNAL_INCLUDE_DIRS}
    )
ENDIF()

IF ( ${MLDSA_LIB} STREQUAL "MLDSA_NATIVE" )
	# upstream mldsa-native (see setup_manifest.py), unmodified: compiled here from its single-file sources, with
	# the flags of the firmware
	if(NOT DEFINED MLDSA_NATIVE_DIR)
	set(MLDSA_NATIVE_DIR ${CMAKE_SOURCE_DIR}/../mldsa-native)
	ENDIF()
	IF ( NOT EXISTS ${MLDSA_NATIVE_DIR}/mldsa/mldsa_native.c )
		MESSAGE( FATAL_ERROR "mldsa-native is missing (${MLDSA_NATIVE_DIR}/mldsa/mldsa_native.c). Run './initial-setup --addons mldsa-native'" )
	ENDIF()
	# smallram keeps the vectors packed and expands them on demand (MLD_CONFIG_REDUCE_RAM); fast is the default
	# memory mode. Both are built with -Os: on the pico2 (both cores) and the STM32U5A5, fast ML-DSA-87 ran 3 to
	# 11 % faster with -Os than with -O3, and -O2 was the slowest (2026-11-21)
	IF ( ${GOAL} STREQUAL "smallram" )
		set( MLDSA_NATIVE_GOAL_REDUCE_RAM 1 )
	ELSEIF ( ${GOAL} STREQUAL "fast" )
		set( MLDSA_NATIVE_GOAL_REDUCE_RAM 0 )
	ELSE()
		MESSAGE( FATAL_ERROR "mldsa-native supports GOAL smallram or fast, not '${GOAL}'" )
	ENDIF()
	# the options of crypto-libraries/mldsa-native.py
	goal_opt( MLDSA_NATIVE_REDUCE_RAM reduce_ram ${MLDSA_NATIVE_GOAL_REDUCE_RAM} )
	goal_opt( MLDSA_NATIVE_OPT opt -Os )
	IF ( "${MLDSA_NATIVE_REDUCE_RAM}" STREQUAL "1" )
		set( MLDSA_NATIVE_GOAL_DEFS MLD_CONFIG_REDUCE_RAM )
	ELSEIF ( "${MLDSA_NATIVE_REDUCE_RAM}" STREQUAL "0" )
		set( MLDSA_NATIVE_GOAL_DEFS "" )
	ELSE()
		MESSAGE( FATAL_ERROR "mldsa-native: option reduce_ram is 0 or 1, not '${MLDSA_NATIVE_REDUCE_RAM}'" )
	ENDIF()
	# cmake/generic_binary.cmake enables ASM only after this directory is processed
	enable_language(ASM)
	add_library(mldsa-native STATIC
		${MLDSA_NATIVE_DIR}/mldsa/mldsa_native.c
		# empty except on RV32 with M, where it holds the RV32IM NTT
		${MLDSA_NATIVE_DIR}/mldsa/mldsa_native_asm.S
	)
	target_compile_definitions(mldsa-native
	  PUBLIC
		MLD_CONFIG_PARAMETER_SET=${PSET}
		MLD_CONFIG_NAMESPACE_PREFIX=mldsa_native
		# key generation from a seed and deterministic signing only: no randombytes()
		MLD_CONFIG_NO_RANDOMIZED_API
		${MLDSA_NATIVE_GOAL_DEFS}
	  PRIVATE
		# single compilation unit
		MLD_CONFIG_INTERNAL_API_QUALIFIER=static
		# the RV32IM backend; C on the CPUs no backend matches
		MLD_CONFIG_USE_NATIVE_BACKEND_ARITH
	)
	target_include_directories(mldsa-native PUBLIC ${MLDSA_NATIVE_DIR}/mldsa)
	target_compile_options(mldsa-native PRIVATE
		${cpu_PARAMS}
		${compiler_OPTS}
		$<$<CONFIG:Debug>:-Og -g3 -ggdb>
		$<$<NOT:$<CONFIG:Debug>>:${MLDSA_NATIVE_OPT}>
	)
	target_link_libraries(${LIB} PRIVATE mldsa-native)
ENDIF()

IF ( ${MLDSA_LIB} STREQUAL "PQM4" )
	include(${CMAKE_SOURCE_DIR}/cmake/pqm4.cmake)
	target_link_libraries(${LIB} PRIVATE pqm4)
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
    ${GOAL_DIR}
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
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/pqcle/libumldsa.a
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/pqcle/libhash.a
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/pqcle/libsha2.a
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/pqcle/libsha3.a
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/pqcle/libprng.a 
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/pqcle/libcommon.a 
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
        COMMAND ${CMAKE_AR} -x ${STM32_CRYPTO_LIB}
        
        #build combined lib
        # the STM32 Cryptographic archives (V5) contain only .obj members, so there is no *.o to add
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
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
        COMMAND ${CMAKE_AR} -x ${GOAL_DIR}/wolfssl/libwolfssl.a
        
        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT} *.o
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT WOLFSSL (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "PQRV")
MESSAGE("MLDSA_LIB is PQRV")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/pqrv/libpqrv.a

        #build combined lib
        # libpqrv contains only .obj members (one per parameter set)
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT PQRV (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "MLDSA_NATIVE")
MESSAGE("MLDSA_LIB is MLDSA_NATIVE")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-native>

        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT MLDSA_NATIVE (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "PQM4")
MESSAGE("MLDSA_LIB is PQM4")
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:pqm4>

        #build combined lib
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT PQM4 (it is '" ${MLDSA_LIB} "')")
ENDIF()

IF(${MLDSA_LIB} STREQUAL "EXTERNAL")
MESSAGE("MLDSA_LIB is EXTERNAL")
set( EXTERNAL_EXTRACT_COMMANDS "" )
foreach( ARCHIVE ${EXTERNAL_MLDSA_ARCHIVES} )
	list( APPEND EXTERNAL_EXTRACT_COMMANDS COMMAND ${CMAKE_AR} -x ${ARCHIVE} )
endforeach()
add_custom_target(combined_target
        COMMAND ${CMAKE_AR} -x $<TARGET_FILE:mldsa-lbmk-core>
        COMMAND ${CMAKE_AR} -x ${TARGET_DIR}/lean-benchmark/liblean-benchmark.a
        ${EXTERNAL_EXTRACT_COMMANDS}

        #build combined lib
        # like libpqrv, the external archives must contain only .obj members
        COMMAND ${CMAKE_AR} -qcs ${LIB_FILE} *.${CMAKE_AR_O_EXT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/lib${LIB_NAME}
        )
ELSE()
MESSAGE("MLDSA_LIB is NOT EXTERNAL (it is '" ${MLDSA_LIB} "')")
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