# Setup

## Setup by script
````
git clone https://github.com/sebastien-riou/crypto-benchmark.git
cd crypto-benchmark
./initial-setup
````

The script `initial-setup` is going to:
- clone `lean-benchmark` and `dilithium-lowram` 
- build them
- build crypto-benchmark 
- run MLDSA-44 benchmark on Renode
- show the results

if you want to skip Renode:
````
./initial-setup 0
````

## Setup step by step
This section is a step by step guide, to do the same as the [previous sections](#Setup-by-script).

### Clone repositories
Clone 3 repositories at the same level:

````
git clone https://github.com/sebastien-riou/crypto-benchmark.git
git clone https://github.com/sebastien-riou/lean-benchmark.git
git clone https://github.com/sebastien-riou/dilithium-lowram.git
````

----
**NOTE**

Clone any other repository you want to benchmark similarly.

----


### Build 'lowram' implementation
````
cd dilithium-lowram
./build-all-targets
cd ..
````

### Build lean-benchmark
````
cd lean-benchmark
./build-all-targets
cd ..
````

### Setup pipenv for crypto-benchmark
````
cd crypto-benchmark
pipenv install
pipenv sync
````

### Build crypto-benchmark

This build all targets for MLDSA-44 benchmarking:
````
python3 link_ext.py
./build-all-targets mldsa 44
````

----
**NOTES**

- `link_ext.py` is creating symlinks to other repositories. 
It is needed only the first time, but it does not hurt if you do it everytime.

- We use 'debug' builds here because it makes debug easier and does not impact benchmarking results (what is benchmarked is almost fully contained in dilithium-lowram repository).
----

## STM32PQC library
It is expected at the top level of this repository:

````
~/repos/crypto-benchmark$ tree -L 1 STM32_Cryptographic/
STM32_Cryptographic/
├── CMOX_HBS_PQC.chm
├── _htmresc
├── include
├── interface
├── lib
├── LICENSE.txt
├── readme.html
└── Release_Notes.html

5 directories, 4 files
````

----
**NOTES**

- This works with the package version V1.1.0 / 27-June-2025 freely available at [ST Microelectronics's X-Cube PQC](https://www.st.com/en/embedded-software/x-cube-pqc.html).
----