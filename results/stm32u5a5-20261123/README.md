# ML-DSA and ML-KEM on the STM32U5A5, November 2026

Measured on 23 and 24 November 2026 with crypto-benchmark: five libraries, every
[optimization goal](../../README.md#optimization-goals) each of them has, and every parameter set of ML-DSA and ML-KEM.

## Libraries

| Library | Name in the results | Version | ML-DSA goals | ML-KEM goals |
|---|---|---|---|---|
| [wolfSSL](https://github.com/sebastien-riou/wolfssl) | wolfssl | 5.9.4, commit `a240b14dd` of the `crypto-benchmark` branch | `smallram`, `balanced`, `fast` | `smallram`, `fast` |
| STM32 Cryptographic library ([X-CUBE-CRYPTOLIB](https://www.st.com/en/embedded-software/x-cube-cryptolib.html)) | stm32pqc | V5.0.0 | `smallram`, `balanced` | `balanced` |
| [pqm4](https://github.com/mupq/pqm4) | pqm4 | commit `0dd10ee5` | `smallram`, `fast` | `smallram`, `fast` |
| [mldsa-native](https://github.com/pq-code-package/mldsa-native) | mldsa-native | commit `ea97cc79` | `smallram`, `fast` | |
| [mlkem-native](https://github.com/pq-code-package/mlkem-native) | mlkem-native | commit `def37022` | | `fast` |

What each goal selects in each library:

| Library | Algorithm | Goal | Configuration |
|---|---|---|---|
| wolfssl | ML-DSA | `smallram` | `WOLFSSL_DILITHIUM_SMALL`, `WOLFSSL_DILITHIUM_SIGN_SMALL_MEM`, `WOLFSSL_DILITHIUM_VERIFY_SMALL_MEM` |
| wolfssl | ML-DSA | `balanced` | `WOLFSSL_DILITHIUM_SMALL` |
| wolfssl | ML-DSA | `fast` | default |
| wolfssl | ML-KEM | `smallram` | `WOLFSSL_MLKEM_SMALL`, `WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM`, `WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM` |
| wolfssl | ML-KEM | `fast` | default |
| stm32pqc | ML-DSA | `smallram` | the library's low RAM signing (`CMOX_PQC_ML_DSA_<n>_DET_SIGN_LOWRAM_ALGO`), with the smaller working buffer it allows |
| stm32pqc | ML-DSA | `balanced` | default |
| stm32pqc | ML-KEM | `balanced` | default, the only configuration |
| pqm4 | ML-DSA | `smallram` / `fast` | implementation `m4fstack` / `m4f`, compiled with `-O3` |
| pqm4 | ML-KEM | `smallram` / `fast` | implementation `m4fstack` / `m4fspeed`, compiled with `-O3` |
| mldsa-native | ML-DSA | `smallram` / `fast` | `MLD_CONFIG_REDUCE_RAM` / default memory mode, compiled with `-Os` |
| mlkem-native | ML-KEM | `fast` | `MLK_CONFIG_SERIAL_FIPS202_ONLY`, compiled with `-Os` |

wolfSSL is built with its Thumb-2 assembly (for ML-DSA, Keccak only); its ML-DSA builds also set
`WOLFSSL_DILITHIUM_VERIFY_NO_MALLOC`.
pqm4's implementations use Cortex-M4 assembly; mldsa-native and mlkem-native are C on this CPU.

## How it was measured

- **Board:** NUCLEO-U5A5ZJ-Q. STM32U5A5, one Arm Cortex-M33 at 160 MHz, code in internal flash, instruction and
  data caches (ICACHE, DCACHE) enabled, stack at the top of the RAM (in SRAM5).
- **Software:** the harness, the firmware of the board, the libraries and the tools are listed with their commits
  in [Versions](#versions). The harness is built with `-Os` and link time optimization.
- **Time:** each operation runs 5 times on each test case, between two readings of the CPU's cycle counter. The
  outputs are checked against the test vectors, outside the timed code.
- **Memory:**
  - Stack: the deepest use over all the operations, found by filling the stack with a pattern beforehand.
  - Heap: how much the heap grows over all the operations.
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
- **Runs:** 45 configurations (library, goal, parameter set), one run on the board for each, all completed with
  correct outputs. The 3 of the STM32 Cryptographic library's ML-KEM are the runs made again at commit `140ac9e`.
  25 of the 45 configurations had been measured on this board earlier in November: they agree within 0.02 %.

## Reading the figures and the tables

- There is one figure and one table per parameter set. Their rows are grouped by goal, and sorted by what the goal
  optimizes: RAM for `smallram`, time otherwise.
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

![ML-DSA-44 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 90 and 1838, 8.9, 33; mldsa-native 106 and 2253, 15, 12; stm32pqc 92 and 1921, 16, 17; wolfssl 86 and 1820, 50, 18. Goal balanced: wolfssl 43 and 626, 88, 19; stm32pqc 80 and 1609, 35, 17. Goal fast: pqm4 31 and 479, 49, 28; wolfssl 35 and 491, 89, 24; mldsa-native 60 and 961, 53, 12.](mldsa44.svg)

| Goal | Library | Key generation | Signature, fastest | Signature, average | Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 2.30 | 4.40 | 14.37 | 294.13 | 3.53 | 5.09 | 0.00 | 3.80 | 33.20 |
| `smallram` | mldsa-native | 2.92 | 4.55 | 16.95 | 360.53 | 3.04 | 11.05 | 0.00 | 3.79 | 11.81 |
| `smallram` | stm32pqc | 2.26 | 4.18 | 14.66 | 307.37 | 2.49 | 1.20 | 0.00 | 14.88 | 17.00 |
| `smallram` | wolfssl | 2.41 | 3.71 | 13.75 | 291.26 | 2.23 | 1.94 | 28.01 | 20.18 | 18.26 |
| `balanced` | wolfssl | 2.34 | 3.44 | 6.85 | 100.23 | 2.47 | 2.15 | 77.02 | 8.89 | 18.56 |
| `balanced` | stm32pqc | 2.26 | 3.87 | 12.75 | 257.42 | 2.49 | 1.22 | 0.00 | 33.88 | 17.13 |
| `fast` | pqm4 | 1.85 | 2.30 | 4.90 | 76.71 | 1.84 | 44.77 | 0.00 | 3.80 | 28.38 |
| `fast` | wolfssl | 2.19 | 2.91 | 5.58 | 78.50 | 2.21 | 2.84 | 77.02 | 8.89 | 24.39 |
| `fast` | mldsa-native | 3.01 | 4.51 | 9.68 | 153.72 | 3.12 | 48.99 | 0.00 | 3.79 | 12.06 |

### ML-DSA-65

![ML-DSA-65 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 174 and 3594, 12, 33; mldsa-native 196 and 4254, 19, 11; stm32pqc 165 and 3528, 22, 17; wolfssl 167 and 3630, 69, 18. Goal balanced: wolfssl 68 and 973, 134, 19; stm32pqc 146 and 3069, 49, 17. Goal fast: pqm4 49 and 736, 74, 28; wolfssl 54 and 740, 135, 24; mldsa-native 95 and 1459, 79, 12.](mldsa65.svg)

| Goal | Library | Key generation | Signature, fastest | Signature, average | Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 4.38 | 7.46 | 27.88 | 575.08 | 6.17 | 6.60 | 0.00 | 5.86 | 32.76 |
| `smallram` | mldsa-native | 5.06 | 7.06 | 31.29 | 680.68 | 5.06 | 12.88 | 0.00 | 5.84 | 11.34 |
| `smallram` | stm32pqc | 3.88 | 6.36 | 26.43 | 564.46 | 4.11 | 1.20 | 0.00 | 20.95 | 16.58 |
| `smallram` | wolfssl | 4.09 | 6.02 | 26.70 | 580.76 | 3.74 | 1.94 | 47.01 | 20.18 | 18.27 |
| `balanced` | wolfssl | 4.02 | 5.39 | 10.80 | 155.62 | 4.15 | 2.15 | 123.02 | 8.88 | 18.57 |
| `balanced` | stm32pqc | 3.88 | 5.96 | 23.42 | 491.03 | 4.11 | 1.22 | 0.00 | 47.95 | 16.71 |
| `fast` | pqm4 | 3.25 | 3.71 | 7.82 | 117.78 | 3.14 | 68.27 | 0.00 | 5.86 | 28.30 |
| `fast` | wolfssl | 3.71 | 4.61 | 8.71 | 118.44 | 3.74 | 2.84 | 123.02 | 8.88 | 24.39 |
| `fast` | mldsa-native | 5.20 | 7.07 | 15.21 | 233.41 | 5.20 | 73.06 | 0.00 | 5.84 | 11.98 |

### ML-DSA-87

![ML-DSA-87 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 234 and 4580, 15, 33; mldsa-native 248 and 5173, 22, 12; stm32pqc 209 and 4264, 28, 17; wolfssl 221 and 4628, 101, 18. Goal balanced: wolfssl 88 and 1034, 208, 19; stm32pqc 188 and 3782, 65, 17. Goal fast: pqm4 65 and 776, 114, 29; wolfssl 72 and 762, 209, 24; mldsa-native 124 and 1557, 117, 12.](mldsa87.svg)

| Goal | Library | Key generation | Signature, fastest | Signature, average | Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 7.31 | 12.32 | 37.44 | 732.79 | 10.71 | 8.10 | 0.00 | 7.33 | 33.04 |
| `smallram` | mldsa-native | 8.51 | 11.29 | 39.74 | 827.75 | 8.55 | 15.13 | 0.00 | 7.32 | 11.68 |
| `smallram` | stm32pqc | 6.50 | 9.99 | 33.45 | 682.32 | 6.91 | 1.20 | 0.00 | 26.41 | 16.82 |
| `smallram` | wolfssl | 6.75 | 10.02 | 35.39 | 740.49 | 6.41 | 1.94 | 79.01 | 20.18 | 18.26 |
| `balanced` | wolfssl | 6.69 | 8.67 | 14.10 | 165.49 | 7.09 | 2.15 | 197.02 | 8.89 | 18.56 |
| `balanced` | stm32pqc | 6.50 | 9.43 | 30.12 | 605.14 | 6.89 | 1.22 | 0.00 | 63.41 | 16.95 |
| `fast` | pqm4 | 5.52 | 6.24 | 10.33 | 124.20 | 5.46 | 106.27 | 0.00 | 7.33 | 28.52 |
| `fast` | wolfssl | 6.29 | 7.53 | 11.49 | 121.96 | 6.44 | 2.84 | 197.02 | 8.89 | 24.39 |
| `fast` | mldsa-native | 8.81 | 11.50 | 19.79 | 249.09 | 8.84 | 109.49 | 0.00 | 7.32 | 12.03 |

## ML-KEM

In the figures, the bar is the mean over the average keys and the dot is the worst-case key. In the tables, each
time is given as "average keys / worst-case key". Decapsulating an invalid ciphertext (implicit rejection) takes
the same time as a valid one: the two are equal at the precision of the tables.

### ML-KEM-512

![ML-KEM-512 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 3.9 and 4.3, 2.9, 22; wolfssl 5.1 and 5.5, 11, 21. Goal balanced: stm32pqc 15.9 and 16.3, 4.8, 13. Goal fast: pqm4 3.9 and 4.2, 5.8, 24; wolfssl 5.1 and 5.5, 17, 24; mlkem-native 7.4 and 7.8, 13, 8.4.](mlkem512.svg)

| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 0.507 / 0.564 | 0.505 / 0.563 | 0.627 / 0.685 | 2.87 | 0.00 | 0.01 | 21.67 |
| `smallram` | wolfssl | 0.598 / 0.660 | 0.639 / 0.702 | 0.819 / 0.882 | 1.34 | 4.02 | 6.06 | 20.69 |
| `balanced` | stm32pqc | 0.731 / 0.790 | 2.174 / 2.232 | 2.546 / 2.605 | 4.79 | 0.00 | 0.03 | 13.36 |
| `fast` | pqm4 | 0.503 / 0.561 | 0.499 / 0.557 | 0.619 / 0.676 | 5.74 | 0.00 | 0.01 | 24.48 |
| `fast` | wolfssl | 0.599 / 0.662 | 0.640 / 0.703 | 0.813 / 0.875 | 1.25 | 9.52 | 6.06 | 23.81 |
| `fast` | mlkem-native | 0.806 / 0.881 | 0.932 / 1.008 | 1.179 / 1.254 | 13.27 | 0.00 | 0.00 | 8.36 |

### ML-KEM-768

![ML-KEM-768 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 6.4 and 6.9, 3.2, 22; wolfssl 8.1 and 8.5, 13, 21. Goal balanced: stm32pqc 22.9 and 23.3, 5.6, 13. Goal fast: pqm4 6.3 and 6.7, 6.8, 25; wolfssl 8.0 and 8.5, 24, 24; mlkem-native 11.6 and 12.2, 19, 8.1.](mlkem768.svg)

| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 0.828 / 0.899 | 0.852 / 0.924 | 1.026 / 1.098 | 3.23 | 0.00 | 0.01 | 21.59 |
| `smallram` | wolfssl | 0.966 / 1.044 | 1.039 / 1.116 | 1.290 / 1.367 | 1.34 | 6.02 | 6.06 | 20.71 |
| `balanced` | stm32pqc | 1.200 / 1.273 | 3.146 / 3.219 | 3.661 / 3.734 | 5.60 | 0.00 | 0.03 | 13.36 |
| `fast` | pqm4 | 0.818 / 0.889 | 0.836 / 0.907 | 1.007 / 1.078 | 6.76 | 0.00 | 0.01 | 24.73 |
| `fast` | wolfssl | 0.940 / 1.017 | 1.035 / 1.113 | 1.276 / 1.354 | 1.25 | 16.52 | 6.06 | 23.83 |
| `fast` | mlkem-native | 1.320 / 1.414 | 1.520 / 1.614 | 1.858 / 1.952 | 19.34 | 0.00 | 0.00 | 8.12 |

### ML-KEM-1024

![ML-KEM-1024 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 9.8 and 10.4, 3.9, 23; wolfssl 11.9 and 12.5, 15, 21. Goal balanced: stm32pqc 31.1 and 31.7, 6.6, 14. Goal fast: pqm4 9.6 and 10.1, 7.9, 25; wolfssl 11.9 and 12.5, 33, 24; mlkem-native 17.0 and 17.7, 26, 8.4.](mlkem1024.svg)

| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | Static RAM | Flash |
|---|---|---|---|---|---|---|---|---|
| `smallram` | pqm4 | 1.318 / 1.402 | 1.342 / 1.426 | 1.573 / 1.658 | 3.90 | 0.00 | 0.01 | 22.59 |
| `smallram` | wolfssl | 1.492 / 1.584 | 1.582 / 1.675 | 1.910 / 2.002 | 1.34 | 8.02 | 6.06 | 20.71 |
| `balanced` | stm32pqc | 1.882 / 1.969 | 4.308 / 4.394 | 4.980 / 5.066 | 6.57 | 0.00 | 0.03 | 13.59 |
| `fast` | pqm4 | 1.294 / 1.379 | 1.310 / 1.395 | 1.538 / 1.623 | 7.90 | 0.00 | 0.01 | 25.06 |
| `fast` | wolfssl | 1.456 / 1.549 | 1.589 / 1.682 | 1.901 / 1.993 | 1.25 | 25.52 | 6.06 | 23.83 |
| `fast` | mlkem-native | 2.049 / 2.160 | 2.286 / 2.398 | 2.722 / 2.833 | 26.36 | 0.00 | 0.00 | 8.45 |

## Versions

Commits are those of the measures. The third column says what `./initial-setup` installs, since it checks out the
versions pinned in [setup_manifest.py](../../setup_manifest.py).

| Component | Measured with | `./initial-setup` gives |
|---|---|---|
| [crypto-benchmark](https://github.com/sebastien-riou/crypto-benchmark) | commit `140ac9e1df709c5c9381bfe7737e656e4933c998` (`v0.0.19` + 19 commits). All but the STM32 Cryptographic library's ML-KEM were measured one commit earlier, at `ba9492fafef4c26bebdf36284c62a1717499047c`: the two differ only in that library's ML-KEM working buffer (4 bytes instead of an unused 32 KiB), which leaves its cycles the same within 0.004 % | this repository |
| [lean-benchmark](https://github.com/sebastien-riou/lean-benchmark) | commit `5e3e88ff11494691d8e741ec852af7d2258cf265` (`v0.0.11` + 1 commit) | tag `v0.0.11`. Same code on the board: the extra commit changes only the program that reads the results on the host |
| [crypto-benchmark-stm32u5](https://github.com/sebastien-riou/crypto-benchmark-stm32u5), the firmware of the board | tag `crypto-benchmark-0.0.16` (commit `0d679a76fbdbc076bbc7bcc78ce19e0049f5f11d`), with one local change in `Core/Src/main.c`: `LBMK_get_cpu_timestamp` returns `uint64_t`, as lean-benchmark declares it, instead of `uint32_t` | the same tag, without the local change. The measures do not depend on it: lean-benchmark keeps the low 32 bits of the difference of two readings |
| [wolfSSL](https://github.com/sebastien-riou/wolfssl), fork | commit `a240b14dda5460944d67974c68993e9f3d3c3417` (tag `crypto-benchmark-0.0.16` + 1 commit, "use armasm when possible"), wolfSSL 5.9.4 | the same commit |
| [pqm4](https://github.com/mupq/pqm4) | commit `0dd10ee5c4572bcf3abb80f46b997edc3055d48c`, with its `mupq` submodule at `0a7c576923c7d00de49e4ce25b446451dc4fad3f` | the same |
| [mldsa-native](https://github.com/pq-code-package/mldsa-native) | commit `ea97cc798b85dad1662bbe9aea4e7e3ec9c4bbbb` | the same |
| [mlkem-native](https://github.com/pq-code-package/mlkem-native) | commit `def370229aa57d759e5779a27261086d5855aead` | the same |
| STM32 Cryptographic library | [X-CUBE-CRYPTOLIB](https://www.st.com/en/embedded-software/x-cube-cryptolib.html) V5.0.0 | nothing: download it from ST and extract it to `STM32_Cryptographic/` (see [Setup.md](../../Setup.md)) |
| Test vectors | BTVG-MLDSA v0.0.6 and BTVG-MLKEM 0.0.2 | in this repository (`libmldsa-lbmk/include`, `libmlkem-lbmk/include`) |
| Compiler | xPack GNU Arm Embedded GCC 14.2.1-1.1 (`arm-none-eabi-gcc 14.2.1 20241119`) | nothing: install it and put it first in `PATH` |
| Build and host tools | cmake 4.3.1, Python 3.12 with the packages of `Pipfile.lock` | the Python packages |
| Flashing | STM32CubeProgrammer v2.22.0, driven by [lean-hwbridge](https://github.com/sebastien-riou/lean-hwbridge) at commit `491b8aeb33f084067fbaf62d010e9208bba9a834` | nothing. Without lean-hwbridge, `benchmark.py` uses the `flash` and `run` scripts of crypto-benchmark-stm32u5 |

## Reproducing

Once, to set up: the compiler in `PATH`, X-CUBE-CRYPTOLIB V5.0.0 extracted to `STM32_Cryptographic/` (see
[Setup.md](../../Setup.md)), then the dependencies, which are cloned next to crypto-benchmark:

````
./initial-setup --addons wolfssl,pqm4,mldsa-native,mlkem-native,crypto-benchmark-stm32u5 --test-renode off -y
````

Then, with the board connected, one command measures everything again and rebuilds the tables and the figures of
this folder. It takes about 70 minutes:

````
results/stm32u5a5-20261123/reproduce
git diff --stat results/stm32u5a5-20261123
````

- `git diff` shows how the reproduction differs from this page's files. Cycle counts repeat within 0.02 % on this
  board, so the times should come out the same to the figures' precision.
- The script makes one `benchmark.py` call per library, algorithm and goal, as the measures of this page were made,
  and tries a failed call again. Only the measures of its own run go in the tables, whatever the folder already
  holds. Its options are at its head: `--dry-run` lists the runs, `--tables-only` rebuilds the tables and figures
  from its last measures.
- Use a commit of crypto-benchmark that has this page: the script and `plot_results.py` came with it, after the
  measures.
- What was checked: the script plans the same 45 runs as were measured (`--dry-run`), and its table and figure
  steps give back the files of this folder, byte for byte, from the measured result files. The whole sequence,
  setup included, has not been replayed from a fresh clone.

## Files

| File | Content |
|---|---|
| `mldsa.csv`, `mlkem.csv` | The results as `format_results.py` prints them, with the best case of ML-KEM and the probabilities of its test cases |
| `mldsa<n>.svg`, `mlkem<n>.svg` | The figures, drawn from the two files above by [plot_results.py](../../plot_results.py) |
| `make-figures` | Draws the figures again and prints the tables of this page |
| `reproduce` | Measures the round again on the board, then rebuilds the two tables and the figures (see [Reproducing](#reproducing)) |

The figures are committed, although they are generated: this page is displayed as it is, without a build step.
