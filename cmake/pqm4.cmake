# pqm4 (see setup_manifest.py), unmodified: one of its Cortex-M4 implementations of ALGO (mlkem or mldsa) for PSET
# and GOAL, compiled here with the flags of the firmware into the static library pqm4.
# Included by libmlkem-lbmk/CMakeLists.txt and libmldsa-lbmk/CMakeLists.txt, after TARGET_CPU is set.
if(NOT DEFINED PQM4_DIR)
set(PQM4_DIR ${CMAKE_SOURCE_DIR}/../pqm4)
ENDIF()
IF ( NOT EXISTS ${PQM4_DIR}/mupq/common/fips202.c )
	MESSAGE( FATAL_ERROR "pqm4 or its mupq submodule is missing (${PQM4_DIR}/mupq/common/fips202.c). Run './initial-setup --addons pqm4'" )
ENDIF()

# The assembly uses DSP instructions and keeps data in the FPU registers s0-s29. softfp makes the FPU available
# to the assembly with the calling convention of the rest of the firmware (soft-float on cortex-m4, m7 and m52,
# softfp already on cortex-m33 and m55), and the glue enables the FPU (CPACR) before the first call. The FPU must
# be explicit: the assembly sets .cpu cortex-m4, which otherwise resets it.
IF ( ${TARGET_CPU} MATCHES "^cortex-m(4|7|33)$" )
	set( PQM4_FPU_PARAMS -mfloat-abi=softfp -mfpu=fpv4-sp-d16 )
ELSEIF ( ${TARGET_CPU} MATCHES "^cortex-m(52|55)$" )
	set( PQM4_FPU_PARAMS -mfloat-abi=softfp -mfpu=fpv5-sp-d16 )
ELSE()
	MESSAGE( FATAL_ERROR "pqm4 needs a Cortex-M with DSP instructions and an FPU (cortex-m4, m7, m33, m52, m55), not ${TARGET_CPU}" )
ENDIF()

# goals: fast is m4fspeed (ML-KEM) / m4f (ML-DSA), smallram is m4fstack
IF ( ${ALGO} STREQUAL "mlkem" )
	set( PQM4_SCHEME crypto_kem/ml-kem-${PSET} )
	set( PQM4_FAST m4fspeed )
ELSEIF ( ${ALGO} STREQUAL "mldsa" )
	set( PQM4_SCHEME crypto_sign/ml-dsa-${PSET} )
	set( PQM4_FAST m4f )
ELSE()
	MESSAGE( FATAL_ERROR "pqm4 is integrated for ALGO mlkem or mldsa, not '${ALGO}'" )
ENDIF()
IF ( ${GOAL} STREQUAL "fast" )
	set( PQM4_GOAL_IMPL ${PQM4_FAST} )
ELSEIF ( ${GOAL} STREQUAL "smallram" )
	set( PQM4_GOAL_IMPL m4fstack )
ELSE()
	MESSAGE( FATAL_ERROR "pqm4 supports GOAL smallram or fast, not '${GOAL}'" )
ENDIF()
# the options of crypto-libraries/pqm4.py
goal_opt( PQM4_IMPL impl ${PQM4_GOAL_IMPL} )
set( PQM4_IMPL_DIR ${PQM4_DIR}/${PQM4_SCHEME}/${PQM4_IMPL} )
MESSAGE("pqm4 implementation: " ${PQM4_IMPL_DIR})

# Most files of the other parameter sets are symbolic links into ml-kem-768 / ml-dsa-44: they must be compiled
# by these paths, not the files they point to, so that their includes (params.h, config.h) come from this
# parameter set's folder. The .i files are included by the assembly, they are not sources.
file(GLOB PQM4_SOURCES LIST_DIRECTORIES false ${PQM4_IMPL_DIR}/*.c ${PQM4_IMPL_DIR}/*.S ${PQM4_IMPL_DIR}/*.s)
IF ( NOT PQM4_SOURCES )
	MESSAGE( FATAL_ERROR "no pqm4 sources in ${PQM4_IMPL_DIR}" )
ENDIF()

# -O3 is pqm4's own speed setting
goal_opt( PQM4_OPT opt -O3 )

# cmake/generic_binary.cmake enables ASM only after this directory is processed
enable_language(ASM)
add_library(pqm4 STATIC
	${PQM4_SOURCES}
	# FIPS 202, with the bit-interleaved Keccak-f[1600] for ARMv7-M that pqm4 uses
	${PQM4_DIR}/mupq/common/fips202.c
	${PQM4_DIR}/common/keccakf1600.S
)
# api.h of the implementation; fips202.h, randombytes.h and hal.h of mupq
target_include_directories(pqm4 PUBLIC ${PQM4_IMPL_DIR} ${PQM4_DIR}/mupq/common)
target_compile_options(pqm4 PRIVATE
	${cpu_PARAMS}
	${compiler_OPTS}
	${PQM4_FPU_PARAMS}
	$<$<CONFIG:Debug>:-Og -g3 -ggdb>
	$<$<NOT:$<CONFIG:Debug>>:${PQM4_OPT}>
)
