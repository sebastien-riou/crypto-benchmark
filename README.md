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

### Single algorithm and parameter set
````
./test-renode
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

----
**NOTE**

PQSHIELD, STM32PQC and WOLFSSL require additional setup.
----

## Display results

````
./show-all-results --details=0
````

You should get something like:
````
$ ./show-all-results --details=0
+ ./show-results on/cortex-m3 --details=0
++ basename on/cortex-m3
+ TARGET=cortex-m3
+ pipenv run python ../lean-benchmark/lean_benchmark.py --write=0 --uart-log lbmk-uart-cortex-m3.log --details=0
hw_platform: Renode
sw_target_cpu: cortex-m3
mldsa_pset: 44
impl_name: pqcrystals-mldsa-lowram
sw_version: 0.0.0-unknown-dirty-untracked
tv_name: mldsa44-m69-h8517CD9D
64 records
Consolidated stats for mldsa_sign-mldsa_sign:
        Min cycles: 3.5M
        Ave cycles: 11.3M
        Max cycles: 232.4M
Consolidated stats for mldsa_verify-mldsa_verify:
        Min cycles: 2.8M
        Ave cycles: 2.8M
        Max cycles: 2.8M

+ ./show-results on/rv32imc --details=0
++ basename on/rv32imc
+ TARGET=rv32imc
+ pipenv run python ../lean-benchmark/lean_benchmark.py --write=0 --uart-log lbmk-uart-rv32imc.log --details=0
hw_platform: Renode
sw_target_cpu: rv32imc
mldsa_pset: 44
impl_name: pqcrystals-mldsa-lowram
sw_version: 0.0.0-unknown-dirty-untracked
tv_name: mldsa44-m69-h8517CD9D
64 records
Consolidated stats for mldsa_sign-mldsa_sign:
        Min cycles: 5.6M
        Ave cycles: 17.6M
        Max cycles: 359.3M
Consolidated stats for mldsa_verify-mldsa_verify:
        Min cycles: 4.1M
        Ave cycles: 4.2M
        Max cycles: 4.2M

+ ./show-results on/rv64imc --details=0
++ basename on/rv64imc
+ TARGET=rv64imc
+ pipenv run python ../lean-benchmark/lean_benchmark.py --write=0 --uart-log lbmk-uart-rv64imc.log --details=0
hw_platform: Renode
sw_target_cpu: rv64imc
mldsa_pset: 44
impl_name: pqcrystals-mldsa-lowram
sw_version: 0.0.0-unknown-dirty-untracked
tv_name: mldsa44-m69-h8517CD9D
64 records
Consolidated stats for mldsa_sign-mldsa_sign:
        Min cycles: 4.7M
        Ave cycles: 13.5M
        Max cycles: 262.3M
Consolidated stats for mldsa_verify-mldsa_verify:
        Min cycles: 3.5M
        Ave cycles: 3.5M
        Max cycles: 3.5M

````

## Import result in Python
The following create pickle files with all data

````
./show-all-results --write=1
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