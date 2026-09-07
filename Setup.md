# Setup

## Setup by script
````
git clone https://github.com/sebastien-riou/crypto-benchmark.git
cd crypto-benchmark
./initial-setup
````

`initial-setup` is a Python script (stdlib only, no dependencies to install
first). With no flags it prompts you for the choices below; pass flags to
run non-interactively (e.g. in CI).

- `--level {minimal,full,custom}` — `minimal` clones/builds only
  `lean-benchmark` + `dilithium-lowram` (the `OPEN_SOURCE` ML-DSA-44 demo).
  `full` additionally clones every add-on in `setup_manifest.py` (other
  crypto libraries and hardware-platform repos). `custom` clones the
  add-ons you list with `--addons`.
- `--addons NAME[,NAME...]` — add-on names to include (implies
  `--level custom`). Run `./initial-setup --list-addons` to see the catalog.
- `--protocol {https,ssh}` — clone over HTTPS (default) or SSH.
- `--version {pinned,latest}` — `pinned` (default) checks out each repo's
  pinned tag from `setup_manifest.py`; `latest` clones the default branch.
- `--test-renode {0,1,on,off,true,false}` — whether to run `./test-renode`
  and show results afterward (default on).
- `-y`/`--yes` — never prompt, use flags/defaults only.
- `--dry-run` — print what would be cloned/built without doing it.

Example, skipping Renode:
````
./initial-setup --test-renode=off --yes
````

If a sibling repo directory already exists, `initial-setup` skips cloning it
and instead warns (immediately, and again in a "Summary of warnings" at the
end) if its working copy is dirty or not on the expected tag/branch.

----
**NOTE**

`STM32PQC` (ST's X-Cube PQC library) is proprietary and not git-cloneable —
see the [STM32PQC library](#stm32pqc-library) section below for manual setup.
----

## Setup step by step
This section is a step by step guide, to do the same as the [previous sections](#Setup-by-script).

### Clone repositories
Clone 3 repositories at the same level:

````
git clone https://github.com/sebastien-riou/crypto-benchmark.git
git clone https://github.com/sebastien-riou/lean-benchmark.git --recurse-submodules
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