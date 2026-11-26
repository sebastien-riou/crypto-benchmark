# Algorithms

What crypto-benchmark measures for each algorithm, on which test vectors, and how the results are reported.
The libraries that implement them are in [LIBRARIES.md](LIBRARIES.md).

| Algorithm | Status | Parameter sets (`--pset`) | Operations | Libraries |
|---|---|---|---|---|
| [ML-DSA](#ml-dsa) | benchmarked | `44`, `65`, `87` | key generation, signature, verification | dilithium-lowram, mldsa-native, pqm4, PQMicroLib-Core, PQRV, STM32 Cryptographic library, wolfSSL |
| [ML-KEM](#ml-kem) | benchmarked | `512`, `768`, `1024` | key generation, encapsulation, decapsulation | mlkem-native, pqm4, PQMicroLib-Core, PQRV, STM32 Cryptographic library, wolfSSL |
| [AES](#aes) | work in progress | `128` | CMAC verification | STM32 Cryptographic library, wolfSSL |
| [SHA-2](#sha-2) | work in progress | `224`, `256`, `384`, `512`, `512/224`, `512/256`, `256-edge`, `512-edge` | hash | dilithium-lowram (libtomcrypt), PQMicroLib-Core |

For every operation:
- it runs 5 times on each test case, between two readings of the CPU's cycle counter;
- the harness measures its stack (the deepest use, found by filling the stack with a pattern beforehand) and its
  heap: the most bytes it had allocated at one time, counted on the sizes it asked for, so that the figure does not
  depend on the board's allocator ([common/lbmk_heap.c](common/lbmk_heap.c)). A parameter set reports the largest
  stack and heap of its operations;
- its outputs are checked, outside the timed code; a wrong output stops the run with an error code, and nothing is
  recorded.

The static RAM and the flash a library adds are measured from the firmware: see
[Benchmark memory footprints](README.md#benchmark-memory-footprints).

## ML-DSA

`ALGO=mldsa`, code in [libmldsa-lbmk](libmldsa-lbmk).

- **Test vectors:** from [BTVG-MLDSA](https://github.com/sebastien-riou/BTVG-MLDSA/tree/v0.0.6) v0.0.6, copied in
  [libmldsa-lbmk/include](libmldsa-lbmk/include) with their records (`<name>.sel.py`). For each parameter set:
  - one key pair, generated from its 32-byte seed;
  - 100 messages of 69 bytes. A signature takes 4.36, 5.14 and 3.91 attempts on average over them for ML-DSA-44,
    -65 and -87 (FIPS 204 expects 4.25, 5.1 and 3.85), and the slowest message takes 96, 116 and 85 attempts;
  - one message of 10 KiB;
  - with `-DLARGE_TV=1`, also one message of 1 MiB (it needs a board with that much memory).
- **Signing:** deterministic, with an empty context. Every signature is checked: the SHA-256 digest of all the
  signatures must equal the one of the test vectors.
- **Operations** (names in the results): `key-exp` (key generation from the seed), `sign`, `verify`, and `sign 10K`,
  `verify 10K` for the long message. The CSV tables of `format_results.py` give the operations on the 69-byte
  messages.
- **Prepared keys:** a library that can prepare a key once (expand the matrix, transform the key vectors) and sign
  or verify with it many times is also benchmarked that way: `sk-prepare`, `pk-prepare`, `sign-prepared`,
  `verify-prepared`. How a library declares it: see [External libraries](README.md#external-libraries).
- **Reported by `format_results.py`:** for each operation, the minimum, the average and the maximum over the
  messages and the trials. For `sign`, the maximum is the slowest message.

## ML-KEM

`ALGO=mlkem`, code in [libmlkem-lbmk](libmlkem-lbmk).

- **Operations** (names in the results):
  - `key-exp`: key generation from the 64-byte seed `d || z`;
  - `encaps`: encapsulation from the 32-byte `m`;
  - `decaps`: decapsulation;
  - `decaps-reject`: decapsulation of an invalid ciphertext (implicit rejection): the ciphertext with the bit
    `reject_bit` of the test case flipped. Its timing should match `decaps`.
- **Byte strings:** keys and ciphertexts are byte strings as specified by FIPS 203. Any encoding or decoding done by
  a library is part of the benchmarked operation.
- **Input checks:** the operations always include the input checks of FIPS 203. When a library does not do one, its
  wrapper (`impl_*.h`) does, with the library's own functions where it has them. Who does what, library by library,
  is in [LIBRARIES.md](LIBRARIES.md).
  - encapsulation: the encapsulation key modulus check of section 7.2 (every coefficient of `ek` below q);
  - decapsulation: the decapsulation key hash check of section 7.3 (`H(ek)` against the value stored in the key).
  - After the measurements, the firmware checks that encapsulation rejects a key with a coefficient equal to q, and
    decapsulation a key whose stored `H(ek)` is wrong. If one of them does not, the run stops with error code
    `0x50000007` or `0x50000006` and no results are recorded.
- **Test vectors:** the published sets of [BTVG-MLKEM](https://github.com/sebastien-riou/BTVG-MLKEM/tree/v0.0.2)
  0.0.2, `mlkem512-n32-h2F3BDE49`, `mlkem768-n42-h523BACDC` and `mlkem1024-n17-hFD044788` (32, 42 and 17 test
  cases), copied in [libmlkem-lbmk/include](libmlkem-lbmk/include) with their records (`<name>.py`).
  - The cost of a key depends on the generation of the matrix A, a rejection sampler: most of its entries take 3
    SHAKE128 blocks, a few take 4.
  - Each set has a best case (no extra block and few iterations of the sampler), a worst case (4, 5 and 6 extra
    blocks for ML-KEM-512, ML-KEM-768 and ML-KEM-1024, a probability of about 2^-28) and an average set (keys
    whose numbers of extra blocks and of iterations match the long-term averages).
- **Reported by `format_results.py`:** for each operation, the minimum on the best case, the mean over the average
  set and the maximum on the worst case, with the probabilities from the records.
- **Sanity check build:** with `-DSANITY_TV=1` (`benchmark.py --sanity-tv`), the firmware uses the test vectors
  generated by [libmlkem-lbmk/gen-tv.py](libmlkem-lbmk/gen-tv.py) instead (Python standard library only; it
  checks its FIPS 203 implementation against known answer tests first).
  - They are 16 test cases per parameter set on other keys, the last 2 selected so that the generation of A needs
    a 4th SHAKE128 block for some entries. They were the benchmark's test vectors before BTVG-MLKEM.
  - These runs check the implementations, they are not benchmarks: `format_results.py` reports them only with
    `--sanity-tv` (minimum, average and maximum over all the test cases), and never mixes them with the runs on the
    sets of BTVG-MLKEM.

## AES

`ALGO=aes`, `PSET=128` (the key size), code in [libaes-lbmk](libaes-lbmk), on the test vectors of NIST SP 800-38B.
A work in progress.

- **Operations:**
  - `aes_cmac_verify64`: AES-128 CMAC verification of a 64-byte message, with the correct tag;
  - the verification of a 16-byte message with 17 tags: the correct one, and the correct one with one byte changed,
    for each of its 16 bytes. Comparing them shows whether the time depends on where the tag differs.

## SHA-2

`ALGO=sha2`, code in [libsha2-lbmk](libsha2-lbmk). A work in progress.

- **Operation:** the hash of a 1-byte message, one block.
- **Parameter sets:** the SHA-2 functions SHA-224, SHA-256, SHA-384, SHA-512, SHA-512/224 and SHA-512/256.
  `256-edge` and `512-edge` measure PQMicroLib-Core's secure SHA-256 and SHA-512 instead, which take the message as
  two shares.
- PQMicroLib-Core is benchmarked on the Arm targets only: its secure SHA-2 is built by its Arm presets only.
- libtomcrypt's SHA-2 (`CRYPTO_LIB=OPEN_SOURCE`) is benchmarked with `buildit` only: `benchmark.py` runs
  `dilithium-lowram` for ML-DSA.
