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

# weak placeholders for cmox_ll_init/cmox_ll_deInit, compiled without LTO so that an STM32 application's definitions
# take precedence (see common/stm32pqc_ll.c)
target_sources(${LIB} PRIVATE ${CMAKE_SOURCE_DIR}/common/stm32pqc_ll.c)
set_source_files_properties(${CMAKE_SOURCE_DIR}/common/stm32pqc_ll.c PROPERTIES COMPILE_OPTIONS -fno-lto)
