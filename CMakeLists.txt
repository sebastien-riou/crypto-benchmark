cmake_minimum_required(VERSION 3.22)

project(lbmk-test)

if(NOT DEFINED RAW_COM)
set(RAW_COM 0)
ENDIF()
MESSAGE("RAW_COM=" ${RAW_COM})
ADD_DEFINITIONS(-DRAW_COM=${RAW_COM})

#OPTION(CRYPTO_LIB "Crypto library to benchmark [OPEN_SOURCE,PQSHIELD]" "OPEN_SOURCE") 
if(NOT DEFINED CRYPTO_LIB)
set(CRYPTO_LIB OPEN_SOURCE)
ENDIF()
MESSAGE("CRYPTO_LIB=" ${CRYPTO_LIB})
ADD_DEFINITIONS(-DCRYPTO_LIB=${CRYPTO_LIB})

#OPTION(ALGO "Cryptographic algorithm to benchmark [mldsa,mlkem,sha2,aes]" "mldsa")
if(NOT DEFINED ALGO)
set(ALGO mldsa)
ENDIF()
MESSAGE("ALGO=" ${ALGO})
ADD_DEFINITIONS(-DALGO=${ALGO})

# Optimization goal: one of the standard goals (README.md "Optimization goals", goals.py)
if(NOT DEFINED GOAL)
set(GOAL smallram)
ENDIF()
set(STANDARD_GOALS smallram smallcode balanced fast)
IF ( NOT GOAL IN_LIST STANDARD_GOALS )
	MESSAGE( FATAL_ERROR "GOAL=${GOAL} is not a goal. The goals are: smallram, smallcode, balanced, fast. A variant of a library is an option (GOAL_OPTS), not a goal" )
ENDIF()
MESSAGE("GOAL=" ${GOAL})
ADD_DEFINITIONS(-DGOAL=${GOAL})

# Options of the library on top of the goal, "k=v,k=v" (README.md "Tuning a goal"). A build with options is not
# the goal anymore: it is identified as custom_<hash> (the same value as goal_id() of goals.py) and its
# implementation checks (impl_*.h) of the goal's configuration are skipped (GOAL_CUSTOM).
if(NOT DEFINED GOAL_OPTS)
set(GOAL_OPTS "")
ENDIF()
IF ( "${GOAL_OPTS}" STREQUAL "" )
	set(GOAL_ID ${GOAL})
	set(GOAL_CUSTOM 0)
ELSE()
	IF ( NOT "${GOAL_OPTS}" MATCHES "^[a-z][a-z0-9_]*=[A-Za-z0-9_.+=:/@-]*(,[a-z][a-z0-9_]*=[A-Za-z0-9_.+=:/@-]*)*$" )
		MESSAGE( FATAL_ERROR "GOAL_OPTS=${GOAL_OPTS} is not <key>=<value>[,<key>=<value>...]" )
	ENDIF()
	# the options in one order whatever the order they were given in (the same as opts_string() of goals.py)
	string(REPLACE "," ";" GOAL_OPTS_LIST "${GOAL_OPTS}")
	list(SORT GOAL_OPTS_LIST)
	list(JOIN GOAL_OPTS_LIST "," GOAL_OPTS)
	string(SHA256 GOAL_OPTS_HASH "${GOAL} ${GOAL_OPTS}")
	string(SUBSTRING ${GOAL_OPTS_HASH} 0 8 GOAL_OPTS_HASH)
	set(GOAL_ID custom_${GOAL_OPTS_HASH})
	set(GOAL_CUSTOM 1)
ENDIF()
MESSAGE("GOAL_OPTS=" "${GOAL_OPTS}")
MESSAGE("GOAL_ID=" ${GOAL_ID})
ADD_DEFINITIONS(-DGOAL_CUSTOM=${GOAL_CUSTOM})
add_compile_definitions(GOAL_OPTS_STR="${GOAL_OPTS}")

# goal_opt(<variable> <key> <default>): the value of the option <key> of GOAL_OPTS, <default> when it is not given
function(goal_opt var key default)
	set(value "${default}")
	string(REPLACE "," ";" opts "${GOAL_OPTS}")
	foreach(opt ${opts})
		IF ( "${opt}" MATCHES "^${key}=(.*)$" )
			set(value "${CMAKE_MATCH_1}")
		ENDIF()
	endforeach()
	set(${var} "${value}" PARENT_SCOPE)
endfunction()

# Core set: the cores the library may use, the first one being the caller (README.md "Core sets", cores.py).
# By default the one core of the toolchain file.
get_filename_component(TARGET_CPU ${TARGET_DIR} NAME)
if(NOT DEFINED CORES)
set(CORES ${TARGET_CPU})
ENDIF()
set(N_CORES 0)
string(REPLACE "+" ";" CORES_LIST "${CORES}")
foreach(core ${CORES_LIST})
	IF ( "${core}" MATCHES "^([1-9][0-9]*)x[A-Za-z][A-Za-z0-9_.-]*$" )
		math(EXPR N_CORES "${N_CORES}+${CMAKE_MATCH_1}")
	ELSEIF ( "${core}" MATCHES "^[A-Za-z][A-Za-z0-9_.-]*$" )
		math(EXPR N_CORES "${N_CORES}+1")
	ELSE()
		MESSAGE( FATAL_ERROR "CORES=${CORES} is not a core set: <core>[+<core>...], each optionally <count>x<core>" )
	ENDIF()
endforeach()
MESSAGE("CORES=" ${CORES} " (" ${N_CORES} ")")
# where the ELF file named after the build goes, for the footprint: one folder per core set
if(NOT DEFINED ELF_DIR)
set(ELF_DIR ${CMAKE_BINARY_DIR}/../..)
ENDIF()
ADD_DEFINITIONS(-DN_CORES=${N_CORES})
add_compile_definitions(CORES_STR="${CORES}")

# The library must have this goal for this algorithm, and these options (its manifest, see goals.py)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
execute_process(
	COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/goals.py check ${CRYPTO_LIB} ${ALGO} ${GOAL} "${GOAL_OPTS}"
	RESULT_VARIABLE GOAL_CHECK_ERROR_CODE
	ERROR_VARIABLE GOAL_CHECK_ERROR
	ERROR_STRIP_TRAILING_WHITESPACE
)
IF ( NOT GOAL_CHECK_ERROR_CODE EQUAL 0 )
	MESSAGE( FATAL_ERROR "${GOAL_CHECK_ERROR}" )
ENDIF()

# Revision of the library, reported by the firmware (see goals.py)
execute_process(
	COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/goals.py rev ${CRYPTO_LIB}
	OUTPUT_VARIABLE LIB_REV
	RESULT_VARIABLE LIB_REV_ERROR_CODE
	OUTPUT_STRIP_TRAILING_WHITESPACE
)
IF ( NOT LIB_REV_ERROR_CODE EQUAL 0 OR "${LIB_REV}" STREQUAL "" )
	set(LIB_REV "?")
ENDIF()
MESSAGE("LIB_REV=" ${LIB_REV})
add_compile_definitions(LIB_REV_STR="${LIB_REV}")

# Libraries with one build per goal are linked by link_ext.py in a folder per algorithm and goal (custom_<hash>
# for a goal built with options)
set(GOAL_DIR ${TARGET_DIR}/goals/${ALGO}/${GOAL_ID})

option(DEBUG_INFO "add -g (debug info only, the generated code is unchanged)" OFF)
if(DEBUG_INFO)
add_compile_options(-g)
# LTO: the final code generation, and so the line information, happens at link time
add_link_options(-g)
ENDIF()

if(NOT DEFINED LARGE_TV)
set(LARGE_TV 0)
ENDIF()
MESSAGE("LARGE_TV=" ${LARGE_TV})
ADD_DEFINITIONS(-DLARGE_TV=${LARGE_TV})

# ML-KEM: 1 compiles in the sanity check test vectors (libmlkem-lbmk/gen-tv.py) instead of those of BTVG-MLKEM
if(NOT DEFINED SANITY_TV)
set(SANITY_TV 0)
ENDIF()
MESSAGE("SANITY_TV=" ${SANITY_TV})
ADD_DEFINITIONS(-DSANITY_TV=${SANITY_TV})

IF ( ${CRYPTO_LIB} STREQUAL "OPEN_SOURCE" )
	set( MLDSA_LIB "PQCRYSTALS_LOWRAM" )
	set( SHA2_LIB  "LIBTOMCRYPT" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "PQSHIELD" )
	set( MLDSA_LIB "PQCLE" )
	set( MLKEM_LIB "PQCLE" )
	set( SHA2_LIB  "PQCLE" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "STM32PQC" )
	set( MLDSA_LIB "STM32PQC" )
	set( MLKEM_LIB "STM32PQC" )
	#set( SHA2_LIB  "" )
	set( AES_LIB   "STM32PQC" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "WOLFSSL" )
	set( MLDSA_LIB "WOLFSSL" )
	set( MLKEM_LIB "WOLFSSL" )
	#set( SHA2_LIB  "" )
	set( AES_LIB   "WOLFSSL" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "PQRV" )
	set( MLDSA_LIB "PQRV" )
	set( MLKEM_LIB "PQRV" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "MLDSA_NATIVE" )
	set( MLDSA_LIB "MLDSA_NATIVE" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "MLKEM_NATIVE" )
	set( MLKEM_LIB "MLKEM_NATIVE" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "PQM4" )
	set( MLDSA_LIB "PQM4" )
	set( MLKEM_LIB "PQM4" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "STUB" )
	set( MLDSA_LIB "STUB" )
	set( MLKEM_LIB "STUB" )
	set( SHA2_LIB  "STUB" )
	set( AES_LIB   "STUB" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()

# External library: a folder outside of version control, see "External libraries" in README.md
if(NOT DEFINED EXTERNAL_LIBS_DIR)
set(EXTERNAL_LIBS_DIR ${CMAKE_SOURCE_DIR}/external-libs_git_ignore)
ENDIF()
IF ( NOT DEFINED CRYPTO_LIB_SUPPORTED )
	string( TOLOWER ${CRYPTO_LIB} EXTERNAL_LIB_NAME )
	set( EXTERNAL_LIB_DIR ${EXTERNAL_LIBS_DIR}/${EXTERNAL_LIB_NAME} )
	# one <algo>.cmake per algorithm the external library implements
	IF ( EXISTS ${EXTERNAL_LIB_DIR}/mldsa.cmake )
		set( MLDSA_LIB "EXTERNAL" )
		set( CRYPTO_LIB_SUPPORTED TRUE )
	ENDIF()
	IF ( EXISTS ${EXTERNAL_LIB_DIR}/mlkem.cmake )
		set( MLKEM_LIB "EXTERNAL" )
		set( CRYPTO_LIB_SUPPORTED TRUE )
	ENDIF()
	IF ( DEFINED CRYPTO_LIB_SUPPORTED )
		MESSAGE("External library: " ${EXTERNAL_LIB_DIR})
	ENDIF()
ENDIF()

IF ( NOT DEFINED CRYPTO_LIB_SUPPORTED )
	MESSAGE( FATAL_ERROR "CRYPTO_LIB=${CRYPTO_LIB} is not supported. Supported: MLDSA_NATIVE, MLKEM_NATIVE, OPEN_SOURCE, PQM4, PQSHIELD, PQRV, STUB, STM32PQC, WOLFSSL, or an external library in ${EXTERNAL_LIBS_DIR}/<lower case CRYPTO_LIB>" )
ENDIF()

add_subdirectory(lib${ALGO}-lbmk)

# Sources
set(sources_SRCS
	${CMAKE_CURRENT_SOURCE_DIR}/test/source/main.c
	${CMAKE_CURRENT_SOURCE_DIR}/common/lbmk_heap.c
)

# Include directories
set(include_c_DIRS
	${CMAKE_CURRENT_SOURCE_DIR}/test/include
	${CMAKE_CURRENT_SOURCE_DIR}/lib${ALGO}-lbmk/include
)

# libs
set(link_DIRS
	${CMAKE_CURRENT_BINARY_DIR}/lib${ALGO}-lbmk
)

set(link_LIBS ${ALGO}-lbmk)

# Heap use (common/lbmk_heap.c): the allocation functions are wrapped, and the count and its table are kept in every
# build, the STUB included, so that the footprint of a library leaves them out
list(APPEND linker_OPTS
	-Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc,--wrap=free
	-Wl,--undefined=lbmk_heap_allocated,--undefined=lbmk_heap_reallocated,--undefined=lbmk_heap_freed
)

include("cmake/generic_binary.cmake")

include(CTest)
add_test(NAME lbmk-test
					COMMAND lbmk-test)

