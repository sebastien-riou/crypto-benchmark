# crypto-benchmark
Benchmarking of various cryptographic primitives on embedded devices using:
- Framework from https://github.com/sebastien-riou/lean-benchmark
- Renode and/or various develpment boards
- Test vectors for ML-DSA from https://github.com/sebastien-riou/BTVG-MLDSA/tree/v0.0.6
- Test vectors for ML-KEM from https://github.com/sebastien-riou/BTVG-MLKEM/tree/v0.0.2

It benchmarks the performances as well as the various memory footprints.

It also produce self contained benchmarking libraries which can be easily integrated in STMCube-IDE projects and other vendors IDEs.

Results can be retrieved using Python or displayed using the provided script `show-results-pickle`.

## Results
The latest measures were made in November 2026 on the STM32U5A5 (NUCLEO-U5A5ZJ-Q board, Arm Cortex-M33 at 160 MHz), with wolfSSL, the STM32 Cryptographic library, pqm4, mldsa-native and mlkem-native, and every [optimization goal](#optimization-goals) each of them has.

The two figures show ML-DSA-87 and ML-KEM-768. The libraries are grouped by goal, and sorted by what the goal optimizes.
Times are in milliseconds, at the board's 160 MHz. RAM is the sum of stack, heap and static RAM.
For ML-DSA, the signature is given twice: the average, and the slowest of the 100 messages signed. For ML-KEM, the bar is the average and the dot is the worst-case key.
Each column has its own scale.

![ML-DSA-87 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: signature in milliseconds (average, then the slowest message), RAM in KiB, flash in KiB. Goal smallram: pqm4 234 and 4580, 15, 33; mldsa-native 248 and 5173, 22, 12; stm32pqc 209 and 4264, 28, 17; wolfssl 221 and 4628, 101, 18. Goal balanced: wolfssl 88 and 1034, 208, 19; stm32pqc 188 and 3782, 65, 17. Goal fast: pqm4 65 and 776, 114, 29; wolfssl 72 and 762, 209, 24; mldsa-native 124 and 1557, 117, 12.](results/stm32u5a5-20261123/mldsa87.svg)

![ML-KEM-768 on the STM32U5A5 (Cortex-M33, 160 MHz). For each library: decapsulation in milliseconds (average keys, then the worst-case key), RAM in KiB, flash in KiB. Goal smallram: pqm4 6.4 and 6.9, 3.2, 22; wolfssl 8.1 and 8.5, 13, 21. Goal balanced: stm32pqc 22.9 and 23.3, 5.6, 13. Goal fast: pqm4 6.3 and 6.7, 6.8, 25; wolfssl 8.0 and 8.5, 24, 24; mlkem-native 11.6 and 12.2, 19, 8.1.](results/stm32u5a5-20261123/mlkem768.svg)

The other parameter sets, every operation, the split of the RAM, the versions of the libraries and how all this was measured are in [results/stm32u5a5-20261123](results/stm32u5a5-20261123/README.md).
The figures are drawn by `plot_results.py` from the tables that `format_results.py` prints.

## Current status
- Boards:
  - STMicroelectronics [STM32U5A5](https://github.com/sebastien-riou/crypto-benchmark-stm32u5)
  - Nuvoton [M5531](https://github.com/sebastien-riou/crypto-benchmark-m5531)
  - Raspberry Pi [RP2350](https://github.com/sebastien-riou/crypto-benchmark-rp2350)
  - the CPUs Renode emulates
- Algorithms ([ALGORITHMS.md](ALGORITHMS.md)):
  - [ML-DSA](ALGORITHMS.md#ml-dsa)
  - [ML-KEM](ALGORITHMS.md#ml-kem)
  - [AES](ALGORITHMS.md#aes), work in progress
  - [SHA-2](ALGORITHMS.md#sha-2), work in progress
- Libraries ([LIBRARIES.md](LIBRARIES.md)):
  - [dilithium-lowram](LIBRARIES.md#dilithium-lowram)
  - [mldsa-native](LIBRARIES.md#mldsa-native)
  - [mlkem-native](LIBRARIES.md#mlkem-native)
  - [pqm4](LIBRARIES.md#pqm4)
  - [PQMicroLib-Core](LIBRARIES.md#pqmicrolib-core)
  - [PQRV](LIBRARIES.md#pqrv)
  - [STM32 Cryptographic library](LIBRARIES.md#stm32-cryptographic-library)
  - [wolfSSL](LIBRARIES.md#wolfssl)
  - others can be added without changing this repository: [External libraries](#external-libraries)
- Tools it is tested with: [Setup.md](Setup.md#tested-with)

## Setup 
See [Setup.md](Setup.md).

## Benchmarking on a board
To benchmark PQRV's ML-KEM-512 on rp2350 MCU (pico2 board):
````
pipenv run python benchmark.py --hw-platform rp2350 --lib pqrv --algo mlkem --pset 512
````

You can view the results in terminal using:
````
./show-all-results
````

`--lib`, `--algo`, `--pset`, `--goal` and `--cores` select what is benchmarked; without them, everything the hardware platform and the libraries support.

## Optimization goals
A library is benchmarked for one or several goals. A goal names what an application needs most; it has the same meaning for every library and algorithm:

| Goal | Use case | What the library is configured for |
|---|---|---|
| `smallram` | RAM is the scarce resource | Least RAM (static, stack and heap), then least flash; speed last |
| `smallcode` | Flash is the scarce resource | Least flash (code, constants, initial values of data), then least RAM; speed last |
| `balanced` | No dominant constraint | What one would ship by default on a typical MCU: no extreme in any of the three |
| `fast` | Time or energy per operation matters most | Fewest cycles; RAM and flash unconstrained |

For every goal the library runs in constant time with respect to secrets where it offers that, with its standard API.

Which options of a library, compiler flags included, serve a goal best on a target is the choice of whoever integrates the library: it is written in its manifest ([crypto-libraries](crypto-libraries)), its build and its glue (`impl_*.h`).
A library provides only the goals it has a distinct configuration for. `python3 goals.py list` shows the goals of every library.

`benchmark.py --goal fast smallram` benchmarks each library with those of these goals it has; without `--goal`, with all its goals.
The scripts that take one goal (`buildit`, `build-all-targets`, `renode-benchmark*`) use the library's `balanced` goal when none is given, or its first goal when it has no `balanced`.

Results made before these goals keep the names they had: `small` meant `smallram` or `smallcode` depending on the library and the algorithm.

### Tuning a goal
This is for whoever integrates a library, to find out what should go into a goal.
A manifest can declare options (`options(algo)`): the knobs of the library that a goal sets, and the variants it does not use.
`--opt` overrides them for one library and one goal:
````
pipenv run python benchmark.py --hw-platform rp2350 --lib mldsa-native --algo mldsa --goal fast --opt opt=-O3
````

Such a build is not the goal anymore. Its results are reported as `<library>-custom[n]`, with a note giving the goal it starts from and the options, and they are kept apart from the results of the goal itself, footprint included.
Once the best options are known, they belong in the goal's definition in the manifest: `custom` is for experiments, not for results to publish.

An option is `<key>=<value>`, the value without space, comma or quote. `python3 goals.py list` shows the options of every library.
A manifest that knows the values its options take checks them before anything is built (`check_options(algo, opts)`, which raises `ValueError`).
With `buildit`, the options are one argument: `GOAL_OPTS=opt=-O3,reduce_ram=1`.
A library built in its own repository is built first, with the same options: `python3 goals.py build <CRYPTO_LIB> <target> <algo> <pset> <goal> [<options>]`, then `python3 link_ext.py` (`benchmark.py` does both).

## Core sets
A benchmark runs on a core set: the cores of the board that the library may use. `--cores` selects it:

| Core set | Meaning |
|---|---|
| `cortex-m33` | One core, a Cortex-M33 |
| `2xcortex-m33` | Two Cortex-M33 |
| `cortex-m7+cortex-m4` | A Cortex-M7 and a Cortex-M4 |

The first core is the caller: the library is called there and time is measured there; the others help.
A core is named by its software target, i.e., the name of its toolchain file in [on](on), unless the board gives it a name of its own.
Each hardware platform declares its core sets (`core_sets()` in [hardware-platforms](hardware-platforms)); without `--cores`, the sets of one core are benchmarked.
A core set is independent of the goal: `fast` on one core and `fast` on two are two different results.

With several cores:
- Time is the elapsed cycles of the caller: latency, not the work of all the cores. When the cores have different clocks, it depends on their ratio.
- A library must declare that it can use the set (`supports_cores(cores, algo)` in its manifest). A library that uses one core has the same results on a larger set as on its first core alone: it is not benchmarked again.
- The results are reported apart from those on one core, in `build/<core set>/` and in a CSV file named after the core set.

So far the only set of several cores is `2xcortex-m33` (and `2xrv32imcb`) on the RP2350, and no supported library uses it; the library's glue starts the second core itself.
A general way for a library to run on helper cores, the RAM of the helper cores in the reported footprint, and cores that need an image of their own are planned with the move of the hardware platforms to lean-bsp.

## External libraries
An ML-DSA or ML-KEM library which shall not be part of this repository (e.g. not public) can be benchmarked from a folder `external-libs_git_ignore/<name>/` (`<name>` in lower case, git ignores that folder), containing:
- `<name>.py`: the manifest used by `benchmark.py`, same interface as the files in `crypto-libraries`. Its `codename` is the `CRYPTO_LIB` value, i.e., `<name>` in upper case.
- for ML-DSA:
  - `mldsa.cmake`: sets `EXTERNAL_MLDSA_ARCHIVES` to the list of archives to link (`TARGET_CPU` gives the target, e.g. `rv32imcb`) and optionally `EXTERNAL_INCLUDE_DIRS`. Like `libpqrv.a`, the archives must contain only `.obj` members.
  - `impl_mldsa.h`: the glue between [libmldsa-lbmk/source/core.c](libmldsa-lbmk/source/core.c) and the library, same interface as [libmldsa-lbmk/source/impl_pqrv.h](libmldsa-lbmk/source/impl_pqrv.h). `IMPL_NAME` is `<name>-<goal>`.
  - Prepared keys (optional, any ML-DSA implementation): a library that can prepare a key once (expand the matrix, transform the key vectors) and sign or verify with it many times defines `DSA_PREPARED_KEYS` to 1 and provides `dsa_sk_prepare(pset)` and `dsa_pk_prepare(pset)` (prepare the key pair of the last `dsa_gen_key_from_seed`), `dsa_sign_prepared` and `dsa_verify_prepared` (same arguments as `dsa_sign` and `dsa_verify`). The harness then also benchmarks both preparations after each key generation (operations `sk-prepare` and `pk-prepare`), and signs and verifies every message with the prepared keys as well (`sign-prepared`, `verify-prepared`). Signing is deterministic, so a prepared-key signature must equal the plain one (error `0x20000003` otherwise). Prepared keys kept in static variables of `impl_mldsa.h` count in the static RAM reported for the library.
- for ML-KEM: the same with `mlkem.cmake` (setting `EXTERNAL_MLKEM_ARCHIVES`) and `impl_mlkem.h` (same interface as [libmlkem-lbmk/source/impl_pqrv.h](libmlkem-lbmk/source/impl_pqrv.h)). Its `kem_encaps` must include the FIPS 203 section 7.2 modulus check and its `kem_decaps` the section 7.3 hash check, in the library or in `impl_mlkem.h` ([libmlkem-lbmk/source/core.c](libmlkem-lbmk/source/core.c) provides `kem_ek_modulus_ok` and `ERROR_EK_CHECK`, `KEM_DK_EK_OFFSET`, `kem_dk_hash_matches` and `ERROR_DK_CHECK` for the latter).

The goals of an external library are those its manifest lists in `algorithms()`, among the [optimization goals](#optimization-goals): the manifest says which variant of the library serves each of them.
The other variants and the build options of the library are options (`options(algo)`, see [Tuning a goal](#tuning-a-goal)), not goals of their own.

What a build is for reaches every part of the integration:
- The manifest's `build_cmd(sw_target, goal, pset, algo)` may take more arguments, by name: `opts` (the options, a dictionary), `cores` (the core set) and `hw_platform`.
- In the `.cmake` files: `PSET`, `GOAL`, `GOAL_OPTS` (`k=v,k=v`; `goal_opt(<variable> <key> <default>)` reads one option), `GOAL_ID` (the goal, or `custom_<hash>` when there are options: a name for the folder of a build), `CORES` and `TARGET_CPU`.
- In the glue: `GOAL`, `GOAL_CUSTOM` (1 when there are options) and `N_CORES` (the number of cores of the set).
- Optional in the manifest: `supports_cores(cores, algo)` for a library that can use several cores, and `revision()` when the library is not the git repository at the manifest's `path` (the firmware reports the library's revision with the results).

The library is then selected like the others, e.g. `./buildit on/rv32imcb mldsa 44 <NAME> minSizeRel GOAL=<goal>` or `pipenv run python benchmark.py --hw-platform rp2350 --lib <name> --algo mldsa`.
Use `-DEXTERNAL_LIBS_DIR=<path>` to look for external libraries in another folder.

## Benchmarking using Renode

Using renode is like using a physical board except that the communication is strictly one way (Renode -> uart log file).
To achieve this, build must be done with `-DRAW_COM=1`.

### Single algorithm and parameter set
````
./build-all-targets mldsa 44 OPEN_SOURCE smallram minSizeRel -DRAW_COM=1
./test-renode
./show-all-uart-results --details=0
````

This benchmark a default aglorithm with its default parameter set (ML-DSA-44). 
It try to run the following simulations:
- cortex-m3
- cortex-m33
- rv32imc
- rv64imc

You can tweak that by editing [renode.robot](renode.robot).

It uses the latest binaries built for those target CPUs.

### ML-DSA, all parameter sets
````
./renode-benchmark-mldsa
````

This successively build and benchmark all parameter sets for ML-DSA.
You can optionally specify:

- a crypto-library
  - `MLDSA_NATIVE`
  - `OPEN_SOURCE`
  - `PQSHIELD`
  - `STM32PQC`
  - `WOLFSSL`
- an [optimization goal](#optimization-goals), by default the library's `balanced` goal, or its first goal when it has none

The output is a set of files `renode-mldsa-benchmark-*-*-*.csv`. You can display them in terminal using:
````
./show-all-results
````

You should get something like:
````
renode-mldsa-benchmark-cortex-m33-OPEN_SOURCE-smallram.csv
Performance for a 69-byte message and zero-length context (in million cycles).                                                                       
Implementation                                                                  Level                                Operation  Minimum  Average(a)  Worst observed(b)
pqcrystals-lowram-smallram                                                       44                                   key-exp     1.92     1.97        2.01
pqcrystals-lowram-smallram                                                       44                                   sign        3.47    11.23       230.40
pqcrystals-lowram-smallram                                                       44                                   verify      2.76     2.77        2.78
pqcrystals-lowram-smallram                                                       65                                   key-exp     3.74     3.74        3.74
pqcrystals-lowram-smallram                                                       65                                   sign        5.68    20.98       444.43
pqcrystals-lowram-smallram                                                       65                                   verify      4.91     4.92        4.93
pqcrystals-lowram-smallram                                                       87                                   key-exp     6.13     6.26        6.38
pqcrystals-lowram-smallram                                                       87                                   sign        9.23    27.56       550.51
pqcrystals-lowram-smallram                                                       87                                   verify      8.50     8.52        8.54
(a): Match long term average for sign.                                                                                                               
(b): Probability of occurrence is 2^-37 for sign.                                                                                                    
Memory footprint for key generation                                              signing and verification (in KiB).                                  
Implementation                                                                  Level                                Stack      Heap     Static RAM      Flash
pqcrystals-lowram-smallram                                                       44                                    5.19       0.00     3.77       12.52 
pqcrystals-lowram-smallram                                                       65                                    6.69       0.00     5.84       11.96 
pqcrystals-lowram-smallram                                                       87                                    8.19       0.00     7.30       12.21 
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------renode-mldsa-benchmark-cortex-m3-OPEN_SOURCE-smallram.csv
Performance for a 69-byte message and zero-length context (in million cycles).                                                                       
Implementation                                                                  Level                                Operation  Minimum  Average(a)  Worst observed(b)
pqcrystals-lowram-smallram                                                       44                                   key-exp     1.92     1.97        2.01
pqcrystals-lowram-smallram                                                       44                                   sign        3.51    11.33       232.38
pqcrystals-lowram-smallram                                                       44                                   verify      2.76     2.77        2.78
...
````


----
**NOTE**

- PQSHIELD, STM32PQC and WOLFSSL require additional setup.
----

### ML-KEM
````
./renode-benchmark-mlkem
````

Same as above for ML-KEM, limited to ML-KEM-512 for now.
You can optionally specify:

- a crypto-library
  - `MLKEM_NATIVE` (goal `fast`)
  - `PQSHIELD` (default, goal `balanced` or `fast`)
  - `WOLFSSL` (goal `smallram`, `smallcode`, `balanced` or `fast`)
- an optimization goal

The external library must be built for each target beforehand (for WolfSSL: `python3 goals.py build WOLFSSL <target> mlkem 768 <goal>`, then `python3 link_ext.py`), targets for which it is not available are skipped.
`STM32PQC` is not supported: it runs only on STM32 hardware.

The output is a set of files `renode-mlkem-benchmark-*-*-*.csv`.

## Display raw results

````
./show-all-uart-results --details=0
````

You should get something like:
````
$ ./show-all-uart-results --details=0
+ for i in lbmk-uart-*.log
+ pipenv run python ../lean-benchmark/lean_benchmark.py --write=0 --uart-log lbmk-uart-cortex-m33.log --details=0
hw_platform: cortex-m33
sw_target_cpu: cortex-m33
mldsa_pset: 87
impl_name: pqcrystals-mldsa-lowram
sw_version: 0.0.7-15-g4d92b8d-dirty-untracked
tv_name: mldsa87-m69-h7D444798
84 records
Consolidated stats for mldsa_gen_key-mldsa_gen_key:
        Min cycles: 6.1M
        Ave cycles: 6.3M
        Max cycles: 6.4M
        Max stack:  3.88 KiB (3976 bytes)
        Max heap:   0 bytes
Consolidated stats for mldsa_sign-mldsa_sign69:
        Min cycles: 9.2M
        Ave cycles: 27.6M
        Max cycles: 550.5M
        Max stack:  8.19 KiB (8384 bytes)
        Max heap:   0 bytes
Consolidated stats for mldsa_verify-mldsa_verify69:
        Min cycles: 8.5M
        Ave cycles: 8.5M
        Max cycles: 8.5M
        Max stack:  2.87 KiB (2936 bytes)
        Max heap:   0 bytes
Consolidated stats for mldsa_sign-mldsa_sign10K:
        Min cycles: 10.1M
        Ave cycles: 10.1M
        Max cycles: 10.1M
        Max stack:  8.19 KiB (8384 bytes)
        Max heap:   0 bytes
Consolidated stats for mldsa_verify-mldsa_verify10K:
        Min cycles: 9.4M
        Ave cycles: 9.4M
        Max cycles: 9.4M
        Max stack:  2.87 KiB (2936 bytes)
        Max heap:   0 bytes

+ for i in lbmk-uart-*.log
+ pipenv run python ../lean-benchmark/lean_benchmark.py --write=0 --uart-log lbmk-uart-cortex-m3.log --details=0
hw_platform: cortex-m3
sw_target_cpu: cortex-m3
mldsa_pset: 87
impl_name: pqcrystals-mldsa-lowram
sw_version: 0.0.7-15-g4d92b8d-dirty-untracked
tv_name: mldsa87-m69-h7D444798
...
````

## Import UART log result in Python
The following create pickle files with all data

````
./show-all-uart-results --write=1
````

The pickle files can be imported in any Python script using the `pickle` module.
See [lean-benchmarck README.md](https://github.com/sebastien-riou/lean-benchmark)

## Benchmark memory footprints
The performance benchmark is reporting the dynamic memory usage (stack, heap).
Static memory footprint is computed by the script `report_footprint.py`, as the difference with the `STUB` build (no crypto library):
- flash: what the library adds to flash, i.e. its code, its constants and the initial values of its initialized data;
- rw (the "Static RAM" column of the results): the RAM it adds, initialized and zero-initialized data.

The helper script `report-mldsa-footprint` provides an easy way to use it:

````
./report-mldsa-footprint on/cortex-m33
````

After the build of all libraries has completed, you should get something like:
````
cortex-m33 mldsa 44 OPEN_SOURCE         : flash =    12.44 KiB, rw =      0 bytes
cortex-m33 mldsa 44 STM32PQC            : flash =    17.93 KiB, rw =    11.09 KiB
cortex-m33 mldsa 65 OPEN_SOURCE         : flash =    11.89 KiB, rw =      0 bytes
cortex-m33 mldsa 65 STM32PQC            : flash =    17.92 KiB, rw =    15.09 KiB
cortex-m33 mldsa 87 OPEN_SOURCE         : flash =    12.13 KiB, rw =      0 bytes
cortex-m33 mldsa 87 STM32PQC            : flash =    17.92 KiB, rw =    19.09 KiB
````

## Instructions with data-dependent timing
Each build writes `build/<target>/<algo>/<pset>/non_ct.report`.
It lists, by function, the instructions of the linked firmware whose execution time can depend on their operands:
`umull`, `smull`, `umlal`, `smlal`, `sdiv` and `udiv`.
Each one is safe only if no secret value reaches its operands, which must be checked by hand.
The report is built by `report_non_ct.py` from `objdump -d` of the linked ELF, so it covers the code that actually runs, after LTO.
Only Arm targets are checked; for the others, the report says so.

To trace an address of the report back to the source, build with debug info: `-DDEBUG_INFO=ON` adds `-g`, which does not change the generated code.
For example `./buildit on/cortex-m3 mlkem 512 WOLFSSL minSizeRel GOAL=fast -DDEBUG_INFO=ON`, then `arm-none-eabi-addr2line -f -i -e <elf> <address>`.
External libraries need debug info too; for WolfSSL: `DEBUG_INFO=yes python3 goals.py build WOLFSSL <target> mlkem 768 fast`.

## Debugging using Renode
It is setup for VSCode for the following targets:
- cortex-m3
- rv32imc
- rv32imcb (which has a bug, but we assume it is in Renode 1.16 implementation of B extension)
- rv64imc

Example debug build:
````
python3 link_ext.py --preset=debug
./testit on/cortex-m3 mldsa 44 OPEN_SOURCE debug GOAL=smallram
````

----
**NOTES**

- STM's CMake extension generates an error when launching debug, you can ignore it (or disable that extension for your workspace and restart VSCode)
- Make sure you use a debug build, launching debug on binaries without debug information does not work well in vscode: it just runs through anything without debug info.
----

## Debugging using Linux build
In one terminal:
````
python3 link_ext.py --preset=debug
./testit on/linux mldsa 44 OPEN_SOURCE debug GOAL=smallram
````

This should display a line starting with '`ptsname`:', that information is needed for next step.


On another terminal:
````
./get-results <ptsname>
````

Alternatively, if you do not need to get the benchmark results, you can use a single terminal:
````
./build/linux/mldsa/44/lbmk-test --printf
````