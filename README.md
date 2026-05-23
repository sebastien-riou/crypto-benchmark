# crypto-benchmark
Benchmarking of various cryptographic primitives on embedded devices using:
- Framework from https://github.com/sebastien-riou/lean-benchmark
- Renode
- Test vectors from https://github.com/sebastien-riou/BTVG-MLDSA/releases/tag/v0.0.3

It benchmarks the performances as well as the various memory footprints.

It also produce self contained benchmarking libraries which can be easily integrated in STMCube-IDE projects and other vendors IDEs.

Results can be retrieved using Python or displayed using the provided script `show-results`.

## Current status
It has been used on two targets:
- STMicroelectronics [STM32U5A5](https://github.com/sebastien-riou/crypto-benchmark-stm32u5)
- Nuvoton [M5531](https://github.com/sebastien-riou/crypto-benchmark-m5531)

It contains proper benchmarking only for ML-DSA. SHA2 is a work in progress.

Following ML-DSA librairies have been integrated (alphabetical order):
- `OPEN_SOURCE`: [Dilithium-lowram](https://github.com/sebastien-riou/dilithium-lowram.git) 
- `PQSHIELD`: [PQShield's PQMicroLib-Core](https://pqshield.com/products/pqm-cor/)
- `STM32PQC`: [ST Microelectronics's X-Cube PQC](https://www.st.com/en/embedded-software/x-cube-pqc.html)
- `WOLFSSL`: [WolfSSL](https://github.com/sebastien-riou/wolfssl) (use 'crypto-benchmark' branch)

This has been tested with:
- Ubuntu 24.04
- cmake 3.28.3
- gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- xpack-arm-none-eabi-gcc-14.2.1-1.1 (--version reports 'arm-none-eabi-gcc (xPack GNU Arm Embedded GCC x86_64) 14.2.1 20241119')
- xpack-riscv-none-elf-gcc-15.2.0-1 (--version reports 'riscv-none-elf-gcc (xPack GNU RISC-V Embedded GCC x86_64) 15.2.0')
- Python 3.12.3
- Renode 1.16 portable

## Setup 
See [Setup.md](Setup.md).

## Benchmarking using Renode

Using renode is like using a physical board except that the communication is strictly one way (Renode -> uart log file).
To achieve this, build must be done with `-DRAW_COM=1`.

### Single algorithm and parameter set
````
./build-all-targets mldsa 44 OPEN_SOURCE small minSizeRel -DRAW_COM=1
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
  - `OPEN_SOURCE`
  - `PQSHIELD`
  - `STM32PQC`
  - `WOLFSSL`
- an optimization goal:
  - `small`
  - `balanced`
  - `fast`

The output is a set of files `renode-mldsa-benchmark-*-*-*.csv`.

You should get something like:
````
renode-mldsa-benchmark-cortex-m33-OPEN_SOURCE-small.csv
Performance for a 69-byte message and zero-length context (in million cycles).                                                                       
Implementation                                                                  Level                                Operation  Minimum  Average(a)  Worst observed(b)
pqcrystals-lowram-small                                                          44                                   key-exp     1.92     1.97        2.01
pqcrystals-lowram-small                                                          44                                   sign        3.47    11.23       230.40
pqcrystals-lowram-small                                                          44                                   verify      2.76     2.77        2.78
pqcrystals-lowram-small                                                          65                                   key-exp     3.74     3.74        3.74
pqcrystals-lowram-small                                                          65                                   sign        5.68    20.98       444.43
pqcrystals-lowram-small                                                          65                                   verify      4.91     4.92        4.93
pqcrystals-lowram-small                                                          87                                   key-exp     6.13     6.26        6.38
pqcrystals-lowram-small                                                          87                                   sign        9.23    27.56       550.51
pqcrystals-lowram-small                                                          87                                   verify      8.50     8.52        8.54
(a): Match long term average for sign.                                                                                                               
(b): Probability of occurrence is 2^-37 for sign.                                                                                                    
Memory footprint for key generation                                              signing and verification (in KiB).                                  
Implementation                                                                  Level                                Stack      Heap     Static RAM  Read-only
pqcrystals-lowram-small                                                          44                                    5.19       0.00     3.77       12.52 
pqcrystals-lowram-small                                                          65                                    6.69       0.00     5.84       11.96 
pqcrystals-lowram-small                                                          87                                    8.19       0.00     7.30       12.21 
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------renode-mldsa-benchmark-cortex-m3-OPEN_SOURCE-small.csv
Performance for a 69-byte message and zero-length context (in million cycles).                                                                       
Implementation                                                                  Level                                Operation  Minimum  Average(a)  Worst observed(b)
pqcrystals-lowram-small                                                          44                                   key-exp     1.92     1.97        2.01
pqcrystals-lowram-small                                                          44                                   sign        3.51    11.33       232.38
pqcrystals-lowram-small                                                          44                                   verify      2.76     2.77        2.78
...
````


----
**NOTE**

PQSHIELD, STM32PQC and WOLFSSL require additional setup.
----

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

## Import result in Python
The following create pickle files with all data

````
./show-all-uart-results --write=1
````

The pickle files can be imported in any Python script using the `pickle` module.
See [lean-benchmarck README.md](https://github.com/sebastien-riou/lean-benchmark)

## Benchmark memory footprints
The performance benchmark is reporting the dynamic memory usage (stack, heap).
Static memory footprint is computed by the script `report_footprint.py`.
The helper script `report-mldsa-footprint` provides an easy way to use it:

````
./report-mldsa-footprint on/cortex-m33
````

After the build of all libraries has completed, you should get something like:
````
cortex-m33 mldsa 44 OPEN_SOURCE         : ro =    12.44 KiB, rw =      0 bytes
cortex-m33 mldsa 44 STM32PQC            : ro =    17.93 KiB, rw =    11.09 KiB
cortex-m33 mldsa 65 OPEN_SOURCE         : ro =    11.89 KiB, rw =      0 bytes
cortex-m33 mldsa 65 STM32PQC            : ro =    17.92 KiB, rw =    15.09 KiB
cortex-m33 mldsa 87 OPEN_SOURCE         : ro =    12.13 KiB, rw =      0 bytes
cortex-m33 mldsa 87 STM32PQC            : ro =    17.92 KiB, rw =    19.09 KiB
````

## Debugging using Renode
It is setup for VSCode for the following targets:
- cortex-m3
- rv32imc
- rv32imcb (which has a bug, but we assume it is in Renode 1.16 implementation of B extension)
- rv64imc

Example debug build:
````
python3 link_ext.py --preset=debug
./testit on/cortex-m3 mldsa 44 OPEN_SOURCE debug
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
./testit on/linux mldsa 44 OPEN_SOURCE debug
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