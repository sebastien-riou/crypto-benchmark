cmake_minimum_required(VERSION 3.22)

project(lbmk-test)

#OPTION(CRYPTO_LIB "Crypto library to benchmark [OPEN_SOURCE,PQSHIELD]" "OPEN_SOURCE") 
if(NOT DEFINED CRYPTO_LIB)
set(CRYPTO_LIB OPEN_SOURCE)
ENDIF()
MESSAGE("CRYPTO_LIB=" ${CRYPTO_LIB})
ADD_DEFINITIONS(-DCRYPTO_LIB=${CRYPTO_LIB})

#OPTION(ALGO "Cryptographic algorithm to benchmark [mldsa,sha2]" "mldsa")
if(NOT DEFINED ALGO)
set(ALGO mldsa)
ENDIF()
MESSAGE("ALGO=" ${ALGO})
ADD_DEFINITIONS(-DALGO=${ALGO})

if(NOT DEFINED GOAL)
set(GOAL small)
ENDIF()
MESSAGE("GOAL=" ${GOAL})
ADD_DEFINITIONS(-DGOAL=${GOAL})

if(NOT DEFINED LARGE_TV)
set(LARGE_TV 0)
ENDIF()
MESSAGE("LARGE_TV=" ${LARGE_TV})
ADD_DEFINITIONS(-DLARGE_TV=${LARGE_TV})

IF ( ${CRYPTO_LIB} STREQUAL "OPEN_SOURCE" )
	set( MLDSA_LIB "PQCRYSTALS_LOWRAM" )
	set( SHA2_LIB  "LIBTOMCRYPT" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "PQSHIELD" )
	set( MLDSA_LIB "PQCLE" )
	set( SHA2_LIB  "PQCLE" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "STM32PQC" )
	set( MLDSA_LIB "STM32PQC" )
	#set( SHA2_LIB  "" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "WOLFSSL" )
	set( MLDSA_LIB "WOLFSSL" )
	#set( SHA2_LIB  "" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()
IF ( ${CRYPTO_LIB} STREQUAL "STUB" )
	set( MLDSA_LIB "STUB" )
	set( SHA2_LIB  "STUB" )
	set( CRYPTO_LIB_SUPPORTED TRUE )
ENDIF()

IF ( NOT DEFINED CRYPTO_LIB_SUPPORTED )
	MESSAGE( FATAL_ERROR "CRYPTO_LIB=${CRYPTO_LIB} is not supported. Supported: OPEN_SOURCE, PQSHIELD, STUB, STM32PQC, WOLFSSL" )
ENDIF()

add_subdirectory(lib${ALGO}-lbmk)

# Sources
set(sources_SRCS
	${CMAKE_CURRENT_SOURCE_DIR}/test/source/main.c
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

include("cmake/generic_binary.cmake")

include(CTest)
add_test(NAME lbmk-test
					COMMAND lbmk-test)

