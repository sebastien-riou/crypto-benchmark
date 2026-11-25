# ML-DSA and ML-KEM on the STM32U5A5, November 2026, second round

Five libraries, every [optimization goal](../../README.md#optimization-goals) each of them has, and every parameter
set of ML-DSA and ML-KEM, measured with crypto-benchmark.
This round updates the [round of 23 November](../stm32u5a5-20261123/README.md) for wolfSSL, whose goals were
redefined (see [What changed](#what-changed-since-the-round-of-23-november)). wolfSSL was measured on 25 November
2026; the measures of the other libraries are those of 23 and 24 November: nothing in their code or configuration has
changed since.

## Libraries

| Library | Name in the results | Version | ML-DSA goals | ML-KEM goals |
|---|---|---|---|---|
| [wolfSSL](https://github.com/sebastien-riou/wolfssl) | wolfssl | 5.9.4, commit `a240b14dd` of the `crypto-benchmark` branch | `smallram`, `smallcode`, `balanced`, `fast` | `smallram`, `smallcode`, `balanced`, `fast` |
| STM32 Cryptographic library ([X-CUBE-CRYPTOLIB](https://www.st.com/en/embedded-software/x-cube-cryptolib.html)) | stm32pqc | V5.0.0 | `smallram`, `balanced` | `balanced` |
| [pqm4](https://github.com/mupq/pqm4) | pqm4 | commit `0dd10ee5` | `smallram`, `fast` | `smallram`, `fast` |
| [mldsa-native](https://github.com/pq-code-package/mldsa-native) | mldsa-native | commit `ea97cc79` | `smallram`, `fast` | |
| [mlkem-native](https://github.com/pq-code-package/mlkem-native) | mlkem-native | commit `def37022` | | `fast` |

What each goal selects in each library:

| Library | Algorithm | Goal | Configuration |
|---|---|---|---|
| wolfssl | ML-DSA | `smallram` | `WOLFSSL_DILITHIUM_SMALL`, `WOLFSSL_DILITHIUM_MAKE_KEY_SMALL_MEM`, `WOLFSSL_DILITHIUM_SIGN_SMALL_MEM`, `WOLFSSL_DILITHIUM_VERIFY_SMALL_MEM`, compiled with `-Os` |
| wolfssl | ML-DSA | `smallcode` | `smallram`, with the compact C Keccak (`WC_SHA3_NO_ASM`, `WOLFSSL_SHA3_SMALL`) |
| wolfssl | ML-DSA | `balanced` | `smallram`, with the signature that expands the matrix A once per signature instead of once per attempt (`WOLFSSL_DILITHIUM_SIGN_SMALL_MEM_PRECALC_A=8`) |
| wolfssl | ML-DSA | `fast` | default, with `WOLFSSL_DILITHIUM_VERIFY_SMALL_MEM` |
| wolfssl | ML-KEM | `smallram` | `WOLFSSL_MLKEM_SMALL`, `WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM`, `WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM`, compiled with `-Os` |
| wolfssl | ML-KEM | `smallcode` | `smallram` without allocator (`WOLFSSL_NO_MALLOC`), with C arithmetic (`WC_MLKEM_NO_ASM`) and the compact C Keccak |
| wolfssl | ML-KEM | `balanced` | `smallram` without allocator (`WOLFSSL_NO_MALLOC`): the buffers are on the stack |
| wolfssl | ML-KEM | `fast` | default, compiled with `-Os` |
| stm32pqc | ML-DSA | `smallram` | the library's low RAM signing (`CMOX_PQC_ML_DSA_<n>_DET_SIGN_LOWRAM_ALGO`), with the smaller working buffer it allows |
| stm32pqc | ML-DSA | `balanced` | default |
| stm32pqc | ML-KEM | `balanced` | default, the only configuration |
| pqm4 | ML-DSA | `smallram` / `fast` | implementation `m4fstack` / `m4f`, compiled with `-O3` |
| pqm4 | ML-KEM | `smallram` / `fast` | implementation `m4fstack` / `m4fspeed`, compiled with `-O3` |
| mldsa-native | ML-DSA | `smallram` / `fast` | `MLD_CONFIG_REDUCE_RAM` / default memory mode, compiled with `-Os` |
| mlkem-native | ML-KEM | `fast` | `MLK_CONFIG_SERIAL_FIPS202_ONLY`, compiled with `-Os` |

wolfSSL is built with its Thumb-2 assembly (for ML-DSA, Keccak only) where `smallcode` does not replace it, and at
`-O2`, which its configure chooses, where `-Os` is not listed. [LIBRARIES.md](../../LIBRARIES.md#wolfssl) says why.
pqm4's implementations use Cortex-M4 assembly; mldsa-native and mlkem-native are C on this CPU.

## What changed since the round of 23 November

Only wolfSSL's rows. Its goals were redefined from the sizes of the firmware, runs in Renode and runs on this board.
The main effects, at ML-DSA-87 and ML-KEM-768 (time in million cycles, memory in KiB):

- ML-DSA `smallram`: static RAM 8.9 instead of 20.2, heap 50 instead of 79, 1.8 KiB less flash. Signing is 6 %
  slower (37.36 instead of 35.39), because of `-Os`.
- ML-DSA `balanced`: heap 106 instead of 197, for signing 16 % slower (16.31 instead of 14.10).
- ML-DSA `fast`: verification 6 % faster (6.05 instead of 6.44), for 0.75 KiB more flash.
- ML-KEM `smallram` and `fast`: 3 to 8 % faster, about 2.1 KiB less flash each. `fast` decapsulates in 1.184
  instead of 1.276.
- New: `smallcode` for both algorithms, `balanced` for ML-KEM.

## How it was measured

- **Board:** NUCLEO-U5A5ZJ-Q. STM32U5A5, one Arm Cortex-M33 at 160 MHz, code in internal flash, instruction and
  data caches (ICACHE, DCACHE) enabled, stack at the top of the RAM (in SRAM5).
- **Software:** the harness, the firmware of the board, the libraries and the tools are listed with their commits
  in [Versions](#versions). The harness is built with `-Os` and link time optimization.
- **Time:** each operation runs 5 times on each test case, between two readings of the CPU's cycle counter. The
  outputs are checked against the test vectors, outside the timed code.
- **Memory:**
  - Stack: the deepest use over all the operations, found by filling the stack with a pattern beforehand.
  - Heap: how much the heap grows over all the operations. For wolfSSL, which allocates, this adds up blocks that
    are not in use at the same time: key generation then signature, 50 KiB for ML-DSA-87 `smallram` where the
    largest block is 26 KiB ([LIBRARIES.md](../../LIBRARIES.md#wolfssl) has the sizes of the blocks).
  - Static RAM and flash: what the library adds to a firmware built without it. Flash is code, constants and the
    initial values of data.
  - For ML-DSA, the static RAM includes the key pair, which the benchmark keeps for the library: 3.8, 5.8 and
    7.3 KiB for ML-DSA-44, -65 and -87.
- **Test vectors:**
  - ML-DSA: [BTVG-MLDSA](https://github.com/sebastien-riou/BTVG-MLDSA/tree/v0.0.6) v0.0.6. For each parameter set,
    one key pair and 100 messages of 69 bytes, signed deterministically with an empty context. A signature takes
    4.36, 5.14 and 3.91 attempts on average for ML-DSA-44, -65 and -87 (FIPS 204 expects 4.25, 5.1 and 3.85); the
    slowest message takes 96, 116 and 85 attempts.
  - ML-KEM: [BTVG-MLKEM](https://github.com/sebastien-riou/BTVG-MLKEM/tree/v0.0.2) 0.0.2: 32, 42 and 17 key pairs
    for ML-KEM-512, -768 and -1024. Each set has a best case, keys whose cost matches the long term average, and
    worst cases, whose matrix A needs 4, 5 and 6 extra SHAKE128 blocks (a probability of about 2^-28).
- **Runs:** 54 configurations (library, goal, parameter set), one run on the board for each, all completed with
  correct outputs.
  - wolfSSL's 24 on 25 November. Its two `fast` goals were measured twice, first as options on top of the earlier
    definitions, then under their new definitions: the cycle counts were identical.
  - The other 30 on 23 November, the 3 of the STM32 Cryptographic library's ML-KEM again on 24 November: their rows
    are those of the round of 23 November, unchanged.

## Reading the figures and the tables

- There is one figure and one table per parameter set. Their rows are grouped by goal, and sorted by what the goal
  optimizes: RAM for `smallram`, flash for `smallcode`, time otherwise.
- In the figures, times are in milliseconds, at the board's 160 MHz. In the tables, they are in millions of CPU
  cycles, as measured: one million cycles is 6.25 ms on this board.
- Memory is in KiB. In the figures, RAM is the sum of stack, heap and static RAM.
- The figures print rounded values, without decimal places from 10. The tables have them in full.
- In the figures, each column has its own scale from zero: compare bars inside a column of one figure, not across
  columns or figures.

## ML-DSA

In the figures, the signature has two columns: the average, and the slowest of the 100 messages. The slowest has
its own scale because it takes 11 to 22 times the average: on one scale, the averages could not be told apart.
In the tables, key generation and verification are averages. Signature gives the fastest, the average and the
slowest of the 100 messages.

### ML-DSA-44

![ML-DSA-44 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 90 and 1838, 8.9, 33; mldsa-native 106 and 2253, 15, 12; stm32pqc 92 and 1921, 16, 17; wolfssl 91 and 1930, 39, 16. Goal smallcode: wolfssl 131 and 2810, 39, 14. Goal balanced: wolfssl 50 and 849, 55, 17; stm32pqc 80 and 1609, 35, 17. Goal fast: pqm4 31 and 479, 49, 28; wolfssl 35 and 491, 89, 25; mldsa-native 60 and 961, 53, 12.](mldsa44.svg)

| Goal | Library | Key generation | Signature, fastest | Signature, average | Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 2.30 | 4.40 | 14.37 | 294.13 | 3.53 | 5.09 | 0.00 | 3.80 | 33.20 |
| `smallram` | mldsa-native | 2.92 | 4.55 | 16.95 | 360.53 | 3.04 | 11.05 | 0.00 | 3.79 | 11.81 |
| `smallram` | stm32pqc | 2.26 | 4.18 | 14.66 | 307.37 | 2.49 | 1.20 | 0.00 | 14.88 | 17.00 |
| `smallram` | wolfssl | 2.30 | 3.84 | 14.49 | 308.85 | 2.42 | 1.84 | 28.34 | 8.89 | 16.42 |
| `smallcode` | wolfssl | 3.71 | 5.34 | 20.91 | 449.58 | 3.76 | 1.70 | 28.34 | 8.89 | 13.60 |
| `balanced` | wolfssl | 2.30 | 3.43 | 7.97 | 135.79 | 2.42 | 1.87 | 44.34 | 8.89 | 16.97 |
| `balanced` | stm32pqc | 2.26 | 3.87 | 12.75 | 257.42 | 2.49 | 1.22 | 0.00 | 33.88 | 17.13 |
| `fast` | pqm4 | 1.85 | 2.30 | 4.90 | 76.71 | 1.84 | 44.77 | 0.00 | 3.80 | 28.38 |
| `fast` | wolfssl | 2.19 | 2.92 | 5.58 | 78.52 | 2.09 | 2.82 | 77.02 | 8.89 | 25.14 |
| `fast` | mldsa-native | 3.01 | 4.51 | 9.68 | 153.72 | 3.12 | 48.99 | 0.00 | 3.79 | 12.06 |

### ML-DSA-65

![ML-DSA-65 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 174 and 3594, 12, 33; mldsa-native 196 and 4254, 19, 11; stm32pqc 165 and 3528, 22, 17; wolfssl 176 and 3850, 49, 16. Goal smallcode: wolfssl 256 and 5651, 49, 14. Goal balanced: wolfssl 80 and 1324, 79, 17; stm32pqc 146 and 3069, 49, 17. Goal fast: pqm4 49 and 736, 74, 28; wolfssl 55 and 742, 135, 25; mldsa-native 95 and 1459, 79, 12.](mldsa65.svg)

| Goal | Library | Key generation | Signature, fastest | Signature, average | Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 4.38 | 7.46 | 27.88 | 575.08 | 6.17 | 6.60 | 0.00 | 5.86 | 32.76 |
| `smallram` | mldsa-native | 5.06 | 7.06 | 31.29 | 680.68 | 5.06 | 12.88 | 0.00 | 5.84 | 11.34 |
| `smallram` | stm32pqc | 3.88 | 6.36 | 26.43 | 564.46 | 4.11 | 1.20 | 0.00 | 20.95 | 16.58 |
| `smallram` | wolfssl | 3.99 | 6.27 | 28.21 | 615.96 | 4.02 | 1.84 | 38.34 | 8.88 | 16.42 |
| `smallcode` | wolfssl | 6.53 | 8.79 | 41.01 | 904.23 | 6.38 | 1.70 | 38.34 | 8.88 | 13.60 |
| `balanced` | wolfssl | 3.99 | 5.41 | 12.83 | 211.89 | 4.02 | 1.87 | 68.34 | 8.88 | 16.97 |
| `balanced` | stm32pqc | 3.88 | 5.96 | 23.42 | 491.03 | 4.11 | 1.22 | 0.00 | 47.95 | 16.71 |
| `fast` | pqm4 | 3.25 | 3.71 | 7.82 | 117.78 | 3.14 | 68.27 | 0.00 | 5.86 | 28.30 |
| `fast` | wolfssl | 3.72 | 4.62 | 8.73 | 118.64 | 3.50 | 2.82 | 123.02 | 8.88 | 25.15 |
| `fast` | mldsa-native | 5.20 | 7.07 | 15.21 | 233.41 | 5.20 | 73.06 | 0.00 | 5.84 | 11.98 |

### ML-DSA-87

![ML-DSA-87 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 234 and 4580, 15, 33; mldsa-native 248 and 5173, 22, 12; stm32pqc 209 and 4264, 28, 17; wolfssl 234 and 4904, 61, 16. Goal smallcode: wolfssl 342 and 7248, 61, 14. Goal balanced: wolfssl 102 and 1406, 117, 17; stm32pqc 188 and 3782, 65, 17. Goal fast: pqm4 65 and 776, 114, 29; wolfssl 72 and 764, 209, 25; mldsa-native 124 and 1557, 117, 12.](mldsa87.svg)

| Goal | Library | Key generation | Signature, fastest | Signature, average | Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 7.31 | 12.32 | 37.44 | 732.79 | 10.71 | 8.10 | 0.00 | 7.33 | 33.04 |
| `smallram` | mldsa-native | 8.51 | 11.29 | 39.74 | 827.75 | 8.55 | 15.13 | 0.00 | 7.32 | 11.68 |
| `smallram` | stm32pqc | 6.50 | 9.99 | 33.45 | 682.32 | 6.91 | 1.20 | 0.00 | 26.41 | 16.82 |
| `smallram` | wolfssl | 6.63 | 10.46 | 37.36 | 784.56 | 6.81 | 1.84 | 50.34 | 8.89 | 16.42 |
| `smallcode` | wolfssl | 11.02 | 14.90 | 54.64 | 1159.68 | 11.03 | 1.70 | 50.34 | 8.89 | 13.60 |
| `balanced` | wolfssl | 6.63 | 8.75 | 16.31 | 224.88 | 6.81 | 1.87 | 106.34 | 8.89 | 16.97 |
| `balanced` | stm32pqc | 6.50 | 9.43 | 30.12 | 605.14 | 6.89 | 1.22 | 0.00 | 63.41 | 16.95 |
| `fast` | pqm4 | 5.52 | 6.24 | 10.33 | 124.20 | 5.46 | 106.27 | 0.00 | 7.33 | 28.52 |
| `fast` | wolfssl | 6.30 | 7.55 | 11.51 | 122.16 | 6.05 | 2.82 | 197.02 | 8.89 | 25.14 |
| `fast` | mldsa-native | 8.81 | 11.50 | 19.79 | 249.09 | 8.84 | 109.49 | 0.00 | 7.32 | 12.03 |

## ML-KEM

In the figures, the bar is the mean over the average keys and the dot is the worst-case key. In the tables, each
time is given as "average keys / worst-case key". Decapsulating an invalid ciphertext (implicit rejection) takes
the same time as a valid one: the two are equal at the precision of the tables.

### ML-KEM-512

![ML-KEM-512 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 3.9 and 4.3, 2.9, 22; wolfssl 4.8 and 5.2, 11, 19. Goal smallcode: wolfssl 9.4 and 10.2, 14, 8.8. Goal balanced: wolfssl 4.9 and 5.3, 14, 15; stm32pqc 15.9 and 16.3, 4.8, 13. Goal fast: pqm4 3.9 and 4.2, 5.8, 24; wolfssl 4.7 and 5.1, 17, 22; mlkem-native 7.4 and 7.8, 13, 8.4.](mlkem512.svg)

| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 0.507 / 0.564 | 0.505 / 0.563 | 0.627 / 0.685 | 2.87 | 0.00 | 0.01 | 21.67 |
| `smallram` | wolfssl | 0.568 / 0.630 | 0.600 / 0.662 | 0.771 / 0.834 | 1.31 | 4.02 | 6.06 | 18.61 |
| `smallcode` | wolfssl | 1.072 / 1.192 | 1.160 / 1.281 | 1.504 / 1.624 | 8.70 | 0.00 | 4.98 | 8.78 |
| `balanced` | wolfssl | 0.571 / 0.634 | 0.610 / 0.673 | 0.786 / 0.848 | 8.84 | 0.00 | 4.98 | 15.20 |
| `balanced` | stm32pqc | 0.731 / 0.790 | 2.174 / 2.232 | 2.546 / 2.605 | 4.79 | 0.00 | 0.03 | 13.36 |
| `fast` | pqm4 | 0.503 / 0.561 | 0.499 / 0.557 | 0.619 / 0.676 | 5.74 | 0.00 | 0.01 | 24.48 |
| `fast` | wolfssl | 0.570 / 0.633 | 0.581 / 0.643 | 0.745 / 0.808 | 1.24 | 9.52 | 6.06 | 21.67 |
| `fast` | mlkem-native | 0.806 / 0.881 | 0.932 / 1.008 | 1.179 / 1.254 | 13.27 | 0.00 | 0.00 | 8.36 |

### ML-KEM-768

![ML-KEM-768 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 6.4 and 6.9, 3.2, 22; wolfssl 7.7 and 8.2, 13, 19. Goal smallcode: wolfssl 15.0 and 15.9, 14, 8.8. Goal balanced: wolfssl 7.8 and 8.3, 14, 15; stm32pqc 22.9 and 23.3, 5.6, 13. Goal fast: pqm4 6.3 and 6.7, 6.8, 25; wolfssl 7.4 and 7.9, 24, 22; mlkem-native 11.6 and 12.2, 19, 8.1.](mlkem768.svg)

| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 0.828 / 0.899 | 0.852 / 0.924 | 1.026 / 1.098 | 3.23 | 0.00 | 0.01 | 21.59 |
| `smallram` | wolfssl | 0.936 / 1.014 | 0.991 / 1.069 | 1.232 / 1.310 | 1.31 | 6.02 | 6.06 | 18.62 |
| `smallcode` | wolfssl | 1.755 / 1.905 | 1.912 / 2.061 | 2.393 / 2.543 | 8.70 | 0.00 | 4.98 | 8.79 |
| `balanced` | wolfssl | 0.942 / 1.020 | 1.003 / 1.081 | 1.247 / 1.325 | 8.84 | 0.00 | 4.98 | 15.21 |
| `balanced` | stm32pqc | 1.200 / 1.273 | 3.146 / 3.219 | 3.661 / 3.734 | 5.60 | 0.00 | 0.03 | 13.36 |
| `fast` | pqm4 | 0.818 / 0.889 | 0.836 / 0.907 | 1.007 / 1.078 | 6.76 | 0.00 | 0.01 | 24.73 |
| `fast` | wolfssl | 0.910 / 0.988 | 0.953 / 1.031 | 1.184 / 1.262 | 1.24 | 16.52 | 6.06 | 21.68 |
| `fast` | mlkem-native | 1.320 / 1.414 | 1.520 / 1.614 | 1.858 / 1.952 | 19.34 | 0.00 | 0.00 | 8.12 |

### ML-KEM-1024

![ML-KEM-1024 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 9.8 and 10.4, 3.9, 23; wolfssl 11.5 and 12.1, 15, 19. Goal smallcode: wolfssl 22.3 and 23.4, 14, 8.8. Goal balanced: wolfssl 11.6 and 12.2, 14, 15; stm32pqc 31.1 and 31.7, 6.6, 14. Goal fast: pqm4 9.6 and 10.1, 7.9, 25; wolfssl 11.1 and 11.7, 33, 22; mlkem-native 17.0 and 17.7, 26, 8.4.](mlkem1024.svg)

| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 1.318 / 1.402 | 1.342 / 1.426 | 1.573 / 1.658 | 3.90 | 0.00 | 0.01 | 22.59 |
| `smallram` | wolfssl | 1.457 / 1.549 | 1.529 / 1.622 | 1.844 / 1.936 | 1.31 | 8.02 | 6.06 | 18.62 |
| `smallcode` | wolfssl | 2.754 / 2.932 | 2.944 / 3.122 | 3.567 / 3.745 | 8.70 | 0.00 | 4.98 | 8.79 |
| `balanced` | wolfssl | 1.467 / 1.560 | 1.545 / 1.637 | 1.861 / 1.954 | 8.84 | 0.00 | 4.98 | 15.21 |
| `balanced` | stm32pqc | 1.882 / 1.969 | 4.308 / 4.394 | 4.980 / 5.066 | 6.57 | 0.00 | 0.03 | 13.59 |
| `fast` | pqm4 | 1.294 / 1.379 | 1.310 / 1.395 | 1.538 / 1.623 | 7.90 | 0.00 | 0.01 | 25.06 |
| `fast` | wolfssl | 1.423 / 1.515 | 1.469 / 1.561 | 1.772 / 1.865 | 1.24 | 25.52 | 6.06 | 21.69 |
| `fast` | mlkem-native | 2.049 / 2.160 | 2.286 / 2.398 | 2.722 / 2.833 | 26.36 | 0.00 | 0.00 | 8.45 |

## Versions

Commits are those of the measures. The third column says what `./initial-setup` installs, since it checks out the
versions pinned in [setup_manifest.py](../../setup_manifest.py).

| Component | Measured with | `./initial-setup` gives |
|---|---|---|
| [crypto-benchmark](https://github.com/sebastien-riou/crypto-benchmark) | wolfSSL: the working tree that became commit `c8f5d395ca03d6fd533ab769d4d61853960b195f` (`7ec987c` with the changes of that commit, which defines wolfSSL's goals as measured). The other libraries: commit `ba9492fafef4c26bebdf36284c62a1717499047c`, and `140ac9e1df709c5c9381bfe7737e656e4933c998` for the STM32 Cryptographic library's ML-KEM, as in the round of 23 November; the commits since change neither their code nor their configuration | this repository |
| [lean-benchmark](https://github.com/sebastien-riou/lean-benchmark) | commit `5e3e88ff11494691d8e741ec852af7d2258cf265` (`v0.0.11` + 1 commit) | tag `v0.0.11`. Same code on the board: the extra commit changes only the program that reads the results on the host |
| [crypto-benchmark-stm32u5](https://github.com/sebastien-riou/crypto-benchmark-stm32u5), the firmware of the board | wolfSSL: commit `5dbca1e87a5bee676ea7ee166af475c215370cba` (tag `crypto-benchmark-0.0.16` + 1 commit: `LBMK_get_cpu_timestamp` returns `uint64_t`, as lean-benchmark declares it, instead of `uint32_t`). The other libraries: the tag with that same change made locally | the tag, without that change. The measures do not depend on it: lean-benchmark keeps the low 32 bits of the difference of two readings |
| [wolfSSL](https://github.com/sebastien-riou/wolfssl), fork | commit `a240b14dda5460944d67974c68993e9f3d3c3417` (tag `crypto-benchmark-0.0.16` + 1 commit, "use armasm when possible"), wolfSSL 5.9.4 | the same commit |
| [pqm4](https://github.com/mupq/pqm4) | commit `0dd10ee5c4572bcf3abb80f46b997edc3055d48c`, with its `mupq` submodule at `0a7c576923c7d00de49e4ce25b446451dc4fad3f` | the same |
| [mldsa-native](https://github.com/pq-code-package/mldsa-native) | commit `ea97cc798b85dad1662bbe9aea4e7e3ec9c4bbbb` | the same |
| [mlkem-native](https://github.com/pq-code-package/mlkem-native) | commit `def370229aa57d759e5779a27261086d5855aead` | the same |
| STM32 Cryptographic library | [X-CUBE-CRYPTOLIB](https://www.st.com/en/embedded-software/x-cube-cryptolib.html) V5.0.0 | nothing: download it from ST and extract it to `STM32_Cryptographic/` (see [Setup.md](../../Setup.md)) |
| Test vectors | BTVG-MLDSA v0.0.6 and BTVG-MLKEM 0.0.2 | in this repository (`libmldsa-lbmk/include`, `libmlkem-lbmk/include`) |
| Compiler | xPack GNU Arm Embedded GCC 14.2.1-1.1 (`arm-none-eabi-gcc 14.2.1 20241119`) | nothing: install it and put it first in `PATH` |
| Build and host tools | cmake 4.3.1, Python 3.12 with the packages of `Pipfile.lock` | the Python packages |
| Flashing | STM32CubeProgrammer, driven by [lean-hwbridge](https://github.com/sebastien-riou/lean-hwbridge): for wolfSSL at commit `e0d90bd4216e044d4993fce6ed21b66988ed481d`; for the other libraries at commit `491b8aeb33f084067fbaf62d010e9208bba9a834`, with STM32CubeProgrammer v2.22.0 | nothing. Without lean-hwbridge, `benchmark.py` uses the `flash` and `run` scripts of crypto-benchmark-stm32u5 |

## Reproducing

Once, to set up: the compiler in `PATH`, X-CUBE-CRYPTOLIB V5.0.0 extracted to `STM32_Cryptographic/` (see
[Setup.md](../../Setup.md)), then the dependencies, which are cloned next to crypto-benchmark:

````
./initial-setup --addons wolfssl,pqm4,mldsa-native,mlkem-native,crypto-benchmark-stm32u5 --test-renode off -y
````

Then, with the board connected, one command measures everything again and rebuilds the tables and the figures of
this folder. It takes about 85 minutes:

````
results/stm32u5a5-20261125/reproduce
git diff --stat results/stm32u5a5-20261125
````

- The script measures all the libraries in one go, where this page combines measures of two dates.
- `git diff` shows how the reproduction differs from this page's files. Cycle counts repeat within 0.02 % on this
  board, so the times should come out the same to the figures' precision. The flash of a library can differ by
  a few bytes: it is measured against a firmware without library, which holds the version string of the harness.
- The script makes one `benchmark.py` call per library, algorithm and goal, as the measures of this page were made,
  and tries a failed call again. Only the measures of its own run go in the tables, whatever the folder already
  holds. Its options are at its head: `--dry-run` lists the runs, `--tables-only` rebuilds the tables and figures
  from its last measures.
- Use a commit of crypto-benchmark that has this page: the script came with it, after the measures.
- What was checked: the script plans the same 54 runs as were measured (`--dry-run`). Its table and figure steps
  are those of the round of 23 November, which gave back that round's files byte for byte; they were not run on
  this round's measures, which come from two dates. The whole sequence, setup included, has not been replayed from
  a fresh clone.

## Files

| File | Content |
|---|---|
| `mldsa.csv`, `mlkem.csv` | The results as `format_results.py` prints them, with the best case of ML-KEM and the probabilities of its test cases |
| `mldsa<n>.svg`, `mlkem<n>.svg` | The figures, drawn from the two files above by [plot_results.py](../../plot_results.py) |
| `make-figures` | Draws the figures again and prints the tables of this page |
| `reproduce` | Measures the round again on the board, then rebuilds the two tables and the figures (see [Reproducing](#reproducing)) |

The figures are committed, although they are generated: this page is displayed as it is, without a build step.
