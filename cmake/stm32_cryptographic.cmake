# STM32 Cryptographic middleware (V5 and later): one library per core, libSTM32Cryptographic_CM<n>.a, which also
# contains ML-KEM and ML-DSA. target/<cpu>/stm32pqc links to STM32_Cryptographic/ at the repository root.
# Sets STM32_CRYPTO_LIB to the library of TARGET_DIR's core, or stops when there is none.
get_filename_component(STM32_CRYPTO_CPU ${TARGET_DIR} NAME)
string(REGEX REPLACE "^cortex-m([0-9]+)$" "CM\\1" STM32_CRYPTO_CORE ${STM32_CRYPTO_CPU})
set(STM32_CRYPTO_LIB ${TARGET_DIR}/stm32pqc/lib/libSTM32Cryptographic_${STM32_CRYPTO_CORE}.a)
IF ( NOT EXISTS ${STM32_CRYPTO_LIB} )
	MESSAGE( FATAL_ERROR "STM32PQC is not available for ${STM32_CRYPTO_CPU}: ${STM32_CRYPTO_LIB} is missing. ST ships libraries for cortex-m0plus, m3, m4, m7, m33, m55 and m85, and target/${STM32_CRYPTO_CPU}/stm32pqc must link to STM32_Cryptographic/ (see Setup.md)" )
ENDIF()
MESSAGE("STM32_CRYPTO_LIB=" ${STM32_CRYPTO_LIB})

# cmox_ll_init/cmox_ll_deInit: they switch on the CRC unit's clock of the STM32 family STM32PQC_FAMILY names, which
# benchmark.py passes when it builds for a board. Without it, cmox_ll_init never returns (see common/stm32pqc_ll.c).
# Compiled without LTO, so that an application's own definitions still take precedence over these weak ones.
set(STM32PQC_FAMILIES U5)
target_sources(${LIB} PRIVATE ${CMAKE_SOURCE_DIR}/common/stm32pqc_ll.c)
set_source_files_properties(${CMAKE_SOURCE_DIR}/common/stm32pqc_ll.c PROPERTIES COMPILE_OPTIONS -fno-lto)
IF ( DEFINED STM32PQC_FAMILY AND NOT STM32PQC_FAMILY STREQUAL "" )
	IF ( NOT STM32PQC_FAMILY IN_LIST STM32PQC_FAMILIES )
		MESSAGE( FATAL_ERROR "STM32PQC_FAMILY=${STM32PQC_FAMILY}: common/stm32pqc_ll.c cannot switch on the CRC unit of this family, it knows ${STM32PQC_FAMILIES}" )
	ENDIF()
	set_property(SOURCE ${CMAKE_SOURCE_DIR}/common/stm32pqc_ll.c APPEND PROPERTY COMPILE_DEFINITIONS STM32PQC_FAMILY_${STM32PQC_FAMILY})
	MESSAGE("STM32PQC_FAMILY=" ${STM32PQC_FAMILY})
ENDIF()
