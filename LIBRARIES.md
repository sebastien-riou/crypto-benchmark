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
| [wolfSSL](#wolfssl) | `wolfssl` | `WOLFSSL` | `smallram`, `balanced`, `fast` | `smallram`, `fast` | AES: `smallcode`, `fast` | every Cortex-M and RISC-V target |

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
`crypto-benchmark`), in the sibling `../wolfssl` repository. Each goal is built by one of its scripts.

| Algorithm | Goal | Configuration | Built by |
|---|---|---|---|
| ML-DSA | `smallram` | `WOLFSSL_DILITHIUM_SMALL`, `WOLFSSL_DILITHIUM_SIGN_SMALL_MEM`, `WOLFSSL_DILITHIUM_VERIFY_SMALL_MEM` | `buildit-mldsa-small` |
| ML-DSA | `balanced` | `WOLFSSL_DILITHIUM_SMALL` | `buildit-mldsa-balanced` |
| ML-DSA | `fast` | default | `buildit-mldsa-fast` |
| ML-KEM | `smallram` | `WOLFSSL_MLKEM_SMALL`, `WOLFSSL_MLKEM_MAKEKEY_SMALL_MEM`, `WOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM` | `buildit-mlkem-small` |
| ML-KEM | `fast` | default | `buildit-mlkem-fast` |
| AES | `smallcode` | `WOLFSSL_AES_SMALL_TABLES` | `buildit-aes-small` |
| AES | `fast` | default tables | `buildit-aes-fast` |

- On the Cortex-M targets, every ML-DSA and ML-KEM goal uses wolfSSL's Thumb-2 assembly (`--enable-armasm`). For
  ML-DSA only Keccak is assembly, the ML-DSA arithmetic stays C.
- AES is C on every target: wolfSSL's Thumb-2 AES assembly ignores `WOLFSSL_AES_SMALL_TABLES`.
- ML-KEM input checks: done by the library (in `wc_MlKemKey_DecodePublicKey` and `wc_MlKemKey_DecodePrivateKey`).
