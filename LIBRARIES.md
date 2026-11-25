# Libraries

The cryptographic libraries crypto-benchmark integrates, with their goals and what each goal selects.
A goal says what a configuration of a library is for (least RAM, least flash, fastest...): see
[Optimization goals](README.md#optimization-goals). The algorithms and how they are benchmarked are in
[ALGORITHMS.md](ALGORITHMS.md).

| Library | `--lib` | `CRYPTO_LIB` | ML-DSA goals | ML-KEM goals | Other algorithms | Software targets |
|---|---|---|---|---|---|---|
| [dilithium-lowram](#dilithium-lowram) | `dilithium-lowram` | `OPEN_SOURCE` | `smallram` | | SHA-2 (libtomcrypt), with `buildit` only | every Cortex-M and RISC-V target |
| [mldsa-native](#mldsa-native) | `mldsa-native` | `MLDSA_NATIVE` | `smallram`, `fast` | | | Cortex-M3 to M55, `rv32imc`, `rv32imcb`, `rv64imc` |
| [mlkem-native](#mlkem-native) | `mlkem-native` | `MLKEM_NATIVE` | | `fast` | | Cortex-M3 to M55, `rv32imc`, `rv32imcb`, `rv64imc` |
| [pqm4](#pqm4) | `pqm4` | `PQM4` | `smallram`, `fast` | `smallram`, `fast` | | Cortex-M4, M7, M33, M52, M55 |
| [PQMicroLib-Core](#pqmicrolib-core) | `pqmicrolib` | `PQSHIELD` | `smallram`, `balanced`, `fast` | `balanced`, `fast` | SHA-2: `balanced` | Cortex-M3 to M55, `rv32imc`, `rv32imcb`, `rv64imc` |
| [PQRV](#pqrv) | `pqrv` | `PQRV` | `fast` | `fast` | | `rv32imc`, `rv32imcb` |
| [STM32 Cryptographic library](#stm32-cryptographic-library) | `stm32pqc` | `STM32PQC` | `smallram`, `balanced` | `balanced` | AES: `smallcode`, `fast` | Cortex-M3, M4, M7, M33, M55, M85, on STM32 devices only |
| [wolfSSL](#wolfssl) | `wolfssl` | `WOLFSSL` | `smallram`, `smallcode`, `balanced`, `fast` | `smallram`, `smallcode`, `balanced`, `fast` | AES: `smallcode`, `fast` | every Cortex-M and RISC-V target |

The `--lib` name is the manifest in [crypto-libraries](crypto-libraries) (for `benchmark.py`), `CRYPTO_LIB` the
value `buildit` and CMake take. `python3 goals.py list` prints the goals and options of every library.
Libraries that are not part of this repository can be added too: see
[External libraries](README.md#external-libraries).

ML-KEM requires the input checks of FIPS 203 in every implementation (see [ML-KEM](ALGORITHMS.md#ml-kem)): each
section below says who does them, the library or its wrapper (`impl_*.h`).

## dilithium-lowram

[Dilithium-lowram](https://github.com/sebastien-riou/dilithium-lowram.git), the low-RAM ML-DSA implementation of
pqcrystals, in the sibling `../dilithium-lowram` repository. It is not maintained: it stays as an open source, self
contained reference.

- ML-DSA, goal `smallram`.
- `CRYPTO_LIB=OPEN_SOURCE` also selects libtomcrypt's SHA-2, for the SHA-2 benchmark (with `buildit`, not
  `benchmark.py`).

## mldsa-native

[mldsa-native](https://github.com/pq-code-package/mldsa-native), upstream and unmodified, pinned by commit in
[setup_manifest.py](setup_manifest.py) (sibling `../mldsa-native` repository). crypto-benchmark compiles it itself
from its single-file sources, with the flags of the firmware (see
[libmldsa-lbmk/CMakeLists.txt](libmldsa-lbmk/CMakeLists.txt)).

| Goal | Configuration |
|---|---|
| `smallram` | `MLD_CONFIG_REDUCE_RAM`, `-Os` |
| `fast` | default memory mode, `-Os` |

- `-Os` was faster than `-O3` and `-O2` on the pico2 and the STM32U5A5.
- Its RV32IM assembly NTT is used on `rv32imc` and `rv32imcb`; everything else, Keccak included, is C.
- mldsa-native assumes that 32x32->64-bit multiplications take constant time, which the Cortex-M3 does not
  provide.
- Options (`--opt`): `opt` (the optimization flag), `reduce_ram` (0 or 1).

## mlkem-native

[mlkem-native](https://github.com/pq-code-package/mlkem-native), upstream and unmodified, pinned by commit in
[setup_manifest.py](setup_manifest.py) (sibling `../mlkem-native` repository). crypto-benchmark compiles it itself
from its single-file sources (see [libmlkem-lbmk/CMakeLists.txt](libmlkem-lbmk/CMakeLists.txt)).

| Goal | Configuration |
|---|---|
| `fast` | one Keccak state at a time (`MLK_CONFIG_SERIAL_FIPS202_ONLY`), `-Os` |

- This is the fastest configuration on the pico2 and the STM32U5A5: the default 4-way Keccak was 2 to 7 % slower,
  and `-O3` and `-O2` were slower too. Being also the smallest, it is the only goal.
- It has no backend for these targets: everything, Keccak included, is C.
- mlkem-native assumes that 32x32->64-bit multiplications take constant time, which the Cortex-M3 does not
  provide.
- ML-KEM input checks: done by the library (in `enc_derand` and `dec`).
- Options (`--opt`): `opt` (the optimization flag), `serial_fips202` (0 or 1).

## pqm4

[pqm4](https://github.com/mupq/pqm4), upstream and unmodified, pinned by commit in
[setup_manifest.py](setup_manifest.py) (sibling `../pqm4` repository, with its `mupq` submodule). crypto-benchmark
compiles the implementation itself (see [cmake/pqm4.cmake](cmake/pqm4.cmake)), with `-O3` like pqm4's own speed
builds.

| Algorithm | Goal | Configuration |
|---|---|---|
| ML-DSA | `smallram` / `fast` | implementation `m4fstack` / `m4f` |
| ML-KEM | `smallram` / `fast` | implementation `m4fstack` / `m4fspeed` |

- Cortex-M4, M7, M33, M52 and M55 only: the assembly needs the DSP instructions and keeps data in the FPU registers,
  so it is built with `-mfloat-abi=softfp` and the glue enables the FPU.
- pqm4 has only the randomized API: the glue hands over the test vector's seeds, and 32 zero bytes as `rnd` for
  deterministic signing.
- ML-KEM input checks: done by the wrapper (`kem_ek_modulus_ok`, and the hash check with pqm4's SHA3-256).
- Options (`--opt`): `opt` (the optimization flag), `impl` (the pqm4 implementation folder).

## PQMicroLib-Core

[PQShield's PQMicroLib-Core](https://pqshield.com/products/pqm-cor/), in the sibling `../pqmicrolib-library`
repository, which is PQShield-internal. Built from the presets `<target>-<tier>` of its `crypto-benchmark` branch
(`presets/crypto-benchmark.json`).

| Algorithm | Goal | Configuration |
|---|---|---|
| ML-DSA | `smallram` / `balanced` / `fast` | its ML-DSA tiers small, balanced and fast |
| ML-KEM | `balanced` / `fast` | its single ML-KEM implementation, from the `<target>-balanced` / `<target>-fast` preset |
| SHA-2 | `balanced` | from the `<target>-balanced` preset, with its secure SHA-2; Arm targets only |

- ML-KEM input checks: done by the wrapper (`pqs_mlkem_public_key_validate`, `pqs_mlkem_secret_key_validate`).

## PQRV

[PQRV](https://github.com/Ji-Peng/PQRV), from the fork [sebastien-riou/PQRV](https://github.com/sebastien-riou/PQRV)
(branch `crypto-benchmark`, which adds its `libpqrv` folder), in the sibling `../PQRV` repository. The library is
built by `./buildit <target>` in `libpqrv`.

- RISC-V targets `rv32imc` and `rv32imcb` only.
- ML-DSA and ML-KEM, goal `fast`.
- ML-DSA keeps the expanded matrix on the stack: signing needs up to 124 KiB (ML-DSA-87).
- ML-KEM input checks: done by the wrapper (`pqrv_mlkem<k>_check_pk`, `pqrv_mlkem<k>_check_sk`).

## STM32 Cryptographic library

ST Microelectronics's [X-CUBE-CRYPTOLIB](https://www.st.com/en/embedded-software/x-cube-cryptolib.html), V5.0.0 or
later, which includes ML-KEM and ML-DSA. It is a binary library: download it from ST and extract it to
`STM32_Cryptographic/` (see [Setup.md](Setup.md)). It runs on STM32 devices only, so it cannot be benchmarked with
Renode. There is no library for the Cortex-M52.

| Algorithm | Goal | Configuration |
|---|---|---|
| ML-DSA | `smallram` | the library's low RAM signing (`CMOX_PQC_ML_DSA_<n>_DET_SIGN_LOWRAM_ALGO`), with the smaller working buffer it allows |
| ML-DSA | `balanced` | default |
| ML-KEM | `balanced` | default, the only configuration |
| AES | `smallcode` / `fast` | its small / fast AES implementation |

- ML-KEM input checks: the library does the modulus check, the wrapper the hash check (`cmox_hash_compute`,
  SHA3-256).
- ML-KEM working buffer: ST does not document the size it needs, and the library does not count what its ML-KEM
  code uses, so the wrapper measures it. It fills the buffer with a pattern and, after each operation (outside the
  timed code), reports the highest byte changed as extra data `membuf peak` (visible with `--details=1`).
  - On the STM32U5A5 (2026-11-23, with a 32 KiB buffer) the peak was 0 for every operation and parameter set: the
    ML-KEM code does not use the buffer.
  - Its default size (`STM32PQC_MLKEM_MEMBUF_SIZE`) is therefore 4 bytes, so that the static RAM reported is the
    library's own.
  - If an operation reaches the end of the buffer, the run stops with error code `0xFFFB0000`: rebuild with a
    larger `-DSTM32PQC_MLKEM_MEMBUF_SIZE=<bytes>`, then set it to the largest peak reported.

## wolfSSL

[wolfSSL](https://github.com/sebastien-riou/wolfssl), a fork with the build scripts crypto-benchmark uses (branch
`crypto-benchmark`), in the sibling `../wolfssl` repository.
What each goal is made of is defined in [crypto-libraries/wolfssl.py](crypto-libraries/wolfssl.py), as the values of
the options listed below. The library is built with them by the fork's scripts (`buildit-mldsa`, `buildit-mlkem`,
`buildit-aes`), into `build/<target>-<algo>-<goal>` of the wolfssl repository: `benchmark.py` does it, or
`python3 goals.py build WOLFSSL <target> <algo> <pset> <goal>`.

| Algorithm | Goal | Configuration |
|---|---|---|
| ML-DSA | `smallram` | small code (`WOLFSSL_DILITHIUM_SMALL`); small memory key generation, signature and verification (`..._MAKE_KEY_SMALL_MEM`, `..._SIGN_SMALL_MEM`, `..._VERIFY_SMALL_MEM`); `-Os` |
| ML-DSA | `smallcode` | `smallram`, with the compact C Keccak (`WOLFSSL_SHA3_SMALL`) instead of the assembly |
| ML-DSA | `balanced` | `smallram`, with the signature that expands the matrix A once per signature instead of once per attempt (`..._SIGN_SMALL_MEM_PRECALC_A`) |
| ML-DSA | `fast` | wolfSSL's defaults, with the small memory verification (`..._VERIFY_SMALL_MEM`) |
| ML-KEM | `smallram` | small code (`WOLFSSL_MLKEM_SMALL`); small memory key generation and encapsulation (`WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM`, `WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM`); `-Os` |
| ML-KEM | `balanced` | `smallram` without allocator (`WOLFSSL_NO_MALLOC`): the buffers are on the stack |
| ML-KEM | `smallcode` | `balanced`, with C arithmetic (`WC_MLKEM_NO_ASM`) and the compact C Keccak instead of the assembly |
| ML-KEM | `fast` | wolfSSL's defaults, at `-Os` |
| AES | `smallcode` | `WOLFSSL_AES_SMALL_TABLES`, `WOLFSSL_AES_NO_UNROLL`, `-Os` |
| AES | `fast` | wolfSSL's defaults (full tables) |

What the goals give on the STM32U5A5 (Cortex-M33, measured on 2026-11-25), for ML-DSA-87 and ML-KEM-768: time in
million cycles (the signature's is the average), sizes in KiB. Flash and static RAM are from the firmware (as in
[Benchmark memory footprints](README.md#benchmark-memory-footprints)), the stack as measured, and the heap column
gives the largest block the library allocates, from the source (the harness reports the growth of the heap area,
which adds up the blocks of key generation and signature: 50 KiB for `smallram`, 197 for `fast`).

| ML-DSA-87 | Key generation | Signature | Verification | Flash | Static RAM | Stack | Largest block on the heap |
|---|---|---|---|---|---|---|---|
| `smallram` | 6.63 | 37.36 | 6.81 | 16.4 | 8.9 | 1.8 | 26 (a signature) |
| `smallcode` | 11.02 | 54.64 | 11.03 | 13.6 | 8.9 | 1.7 | 26 |
| `balanced` | 6.63 | 16.31 | 6.81 | 17.0 | 8.9 | 1.9 | 82 |
| `fast` | 6.30 | 11.51 | 6.05 | 25.1 | 8.9 | 2.8 | 118 |

| ML-KEM-768 | Key generation | Encapsulation | Decapsulation | Flash | Static RAM | Stack | Largest block on the heap |
|---|---|---|---|---|---|---|---|
| `smallram` | 0.936 | 0.991 | 1.232 | 18.6 | 6.1 | 1.3 | 4.5 (an encapsulation) |
| `balanced` | 0.942 | 1.003 | 1.247 | 15.2 | 5.0 | 8.8 | none |
| `smallcode` | 1.755 | 1.912 | 2.393 | 8.8 | 5.0 | 8.7 | none |
| `fast` | 0.910 | 0.953 | 1.184 | 21.7 | 6.1 | 1.2 | 10.5 |

The goals were chosen from sizes and Renode runs, then timed on the board, which reversed two of Renode's rankings
(Renode does not model the cache or the flash wait states): `-Os` for ML-KEM, 1 % slower in Renode and 3 to 8 % faster on the board,
and the small memory verification of ML-DSA, 2 % slower in Renode and 5 to 6 % faster on the board.

- **Assembly:** on the Cortex-M targets wolfSSL is configured with its Thumb-2 assembly (`--enable-armasm`).
  - ML-DSA: only Keccak is assembly, the ML-DSA arithmetic stays C.
  - ML-KEM: Keccak, the NTT, the inverse NTT, the base multiplication and the rejection sampler.
  - The `smallcode` goals do not use it: the compact Keccak is 2.8 KiB smaller, the C arithmetic of ML-KEM 3.6 KiB.
  - AES is C on every target: wolfSSL's Thumb-2 AES assembly ignores `WOLFSSL_AES_SMALL_TABLES`.
- **Optimization level:** wolfSSL's configure picks `-O2` for these builds; every goal but ML-DSA `fast` is built at
  `-Os`. On the board `-Os` makes ML-KEM 3 to 8 % faster and ML-DSA about 6 % slower; it saves 10 % of the flash of
  the small configurations. `-O3` was no faster in Renode, and 4 to 12 KiB larger.
- **Parameter sets:** one library holds the three of them, so the key structure, which is the static RAM, has the
  size of the largest whatever the parameter set benchmarked.
- **ML-DSA memory:** the heap blocks are, in polynomials of 1 KiB, for a matrix of `k` rows and `l` columns
  (4 and 4, 6 and 5, 8 and 7 for ML-DSA-44, -65 and -87):
  - small memory: `l + 2k + 1` for a key generation, `l + 2k + 3` for a signature, `l + 4` for a verification;
  - `balanced`: `l + 2k + 3 + kl` for a signature;
  - `fast`: `l + 2k + kl` for a key generation, `3l + 5k + 1 + kl` for a signature, and the small memory
    verification; wolfSSL's default verification takes `1 + l + 2k + kl`.
- **AES:** both goals index tables with secret bytes. wolfSSL's bitsliced AES (`WC_AES_BITSLICED`) does not, but is
  not offered: tried on 2026-11-25, a CMAC of 16 bytes took about 700 times the cycles of the table-based code and
  more stack than the 40 KiB the harness measures.
- **ML-KEM input checks:** done by the library (in `wc_MlKemKey_DecodePublicKey` and
  `wc_MlKemKey_DecodePrivateKey`).
- **Options** (`--opt`), the first value being wolfSSL's default:
  - every algorithm: `opt` (`default`, `-Os`, `-O2`, `-O3`), `sha3` (`asm`, `c`, `small`);
  - ML-DSA: `code` (`large`, `nolarge`, `small`), `keygen` (`full`, `small`), `sign` (`full`, `small`, `precalc`,
    `precalc_a`), `verify` (`full`, `small`, `small_nomalloc`, `smallest`), `poly64` (`0`, `1`);
  - ML-KEM: `code` (`large`, `nolarge`, `small`), `keygen` (`full`, `small`), `encaps` (`full`, `small`), `asm`
    (`1`, `0`), `nomalloc` (`0`, `1`);
  - AES: `tables` (`full`, `small`), `unroll` (`1`, `0`).
- **Values no goal uses**, and why (sizes and Renode runs of 2026-11-25):
  - `sign=precalc` (the decoded key vectors are kept during a signature): 3 % faster than `sign=small` for nearly
    twice its memory;
  - `verify=small_nomalloc` and `smallest`: the verification buffers move from the heap, where they reuse the
    memory of a signature, to the key structure, 11.3 and 5.3 KiB more static RAM. They suit a device that only
    verifies;
  - `code=nolarge`: nearly the size of `large`;
  - `sha3=c`: the size of the assembly, and slower;
  - `poly64`: 1 % faster for 2 KiB more.
- **Earlier definitions:** until 2026-11-25 `smallram` for ML-DSA had the default key generation and
  `verify=small_nomalloc`, `balanced` was `fast` with `code=small`, `fast` was wolfSSL's defaults for both algorithms,
  and nothing was built at `-Os`. The round of
  2026-11-23 measured those: its page lists them.
