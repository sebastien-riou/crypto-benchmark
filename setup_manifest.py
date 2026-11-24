CORE = [
    {
        "name": "lean-benchmark",
        "host": "github",
        "path": "sebastien-riou/lean-benchmark",
        "default_tag": "v0.0.11",
        "recurse_submodules": True,
        "build": ["./build-all-targets debug", "./build-all-targets minSizeRel"],
    },
]

MINIMAL_DEMO = [
    {
        "name": "dilithium-lowram",
        "codename": "OPEN_SOURCE",
        "host": "github",
        "path": "sebastien-riou/dilithium-lowram",
        "default_tag": "crypto-benchmark-0.0.16",
        "recurse_submodules": True,
        "build": ["./build-all-targets"],
    },
]

ADDONS = {
    "crypto-libraries": [
        {
            "name": "wolfssl",
            "codename": "WOLFSSL",
            "host": "github",
            "path": "sebastien-riou/wolfssl",
            # pinned by commit instead of default_tag: its last tag, crypto-benchmark-0.0.16, builds ML-DSA without
            # wolfSSL's Thumb-2 assembly, which the wolfSSL glue (impl_wolfssl.h) requires on Cortex-M
            "commit": "a240b14dda5460944d67974c68993e9f3d3c3417",
            "branch": "crypto-benchmark",  # for --version latest: the default branch (master) is upstream wolfSSL
            "recurse_submodules": False,
            "build": None,  # see repo's own README -- no proven single command
            "docs_hint": "wolfssl/README.md",
        },
        {
            "name": "PQRV",  # link_ext.py expects ../PQRV/libpqrv
            "codename": "PQRV",
            "host": "github",
            "path": "sebastien-riou/PQRV",
            "default_tag": "crypto-benchmark-0.0.16",
            "branch": "crypto-benchmark",  # for --version latest: the default branch (main) has no libpqrv
            "recurse_submodules": False,
            "build": ["./libpqrv/buildit rv32imcb rv32imc"],  # the only targets PQRV supports
        },
        {
            "name": "mldsa-native",
            "codename": "MLDSA_NATIVE",
            "host": "github",
            "path": "pq-code-package/mldsa-native",  # upstream, used unmodified
            # pinned by commit instead of default_tag: v2.0.0, the last release, predates the RV32IM NTT
            "commit": "ea97cc798b85dad1662bbe9aea4e7e3ec9c4bbbb",
            "branch": "main",
            "recurse_submodules": False,
            "build": None,  # compiled by crypto-benchmark itself, see libmldsa-lbmk/CMakeLists.txt
        },
        {
            "name": "mlkem-native",
            "codename": "MLKEM_NATIVE",
            "host": "github",
            "path": "pq-code-package/mlkem-native",  # upstream, used unmodified
            "commit": "def370229aa57d759e5779a27261086d5855aead",  # main, a snapshot like mldsa-native's
            "branch": "main",
            "recurse_submodules": False,
            "build": None,  # compiled by crypto-benchmark itself, see libmlkem-lbmk/CMakeLists.txt
        },
        {
            "name": "pqm4",
            "codename": "PQM4",
            "host": "github",
            "path": "mupq/pqm4",  # upstream, used unmodified
            # its last tag (SignatureRound1, 2024) predates the current ML-DSA code
            "commit": "0dd10ee5c4572bcf3abb80f46b997edc3055d48c",
            "branch": "master",
            "recurse_submodules": False,
            "submodules": ["mupq"],  # fips202 and the common headers; libopencm3 is not used
            "build": None,  # compiled by crypto-benchmark itself, see cmake/pqm4.cmake
        },
        {
            "name": "pqmicrolib-library",
            "codename": "PQSHIELD",
            "host": "gitlab.pqsh.net",
            "path": "engineering/sw/pqmicrolib/pqmicrolib-library",
            "default_tag": "crypto-benchmark-v0.0.19",
            "branch": "crypto-benchmark",  # for --version latest: presets/crypto-benchmark.json is not on the default branch
            "recurse_submodules": False,
            "internal": True,  # requires gitlab.pqsh.net access; clone may fail
            "build": None,
            "docs_hint": "pqmicrolib-library/BUILD.md",
        },
    ],
    "hardware-platforms": [
        {
            "name": "crypto-benchmark-rp2350",
            "host": "github",
            "path": "sebastien-riou/crypto-benchmark-rp2350",
            "default_tag": "crypto-benchmark-0.0.18",
            "helper_module": "rp2350",  # hardware-platforms/rp2350.py, same one benchmark.py uses
            # idempotent: clone pico-sdk if missing, build picotool with USB support if missing
            "setup": ["./setup-pico-sdk", "./setup-picotool"],
        },
        {
            "name": "crypto-benchmark-stm32u5",
            "host": "github",
            "path": "sebastien-riou/crypto-benchmark-stm32u5",
            "default_tag": "crypto-benchmark-0.0.16",
            "helper_module": "stm32u5",  # hardware-platforms/stm32u5.py
            "setup": None,  # nothing extra needed beyond its own repo
        },
        {
            "name": "crypto-benchmark-m5531",
            "host": "github",
            "path": "sebastien-riou/crypto-benchmark-m5531",
            "default_tag": "crypto-benchmark-0.0.16",
            "helper_module": "m5531",  # hardware-platforms/m5531.py
            "setup": ["pipenv install"],  # bootstraps its own pyocd venv
        },
    ],
}

MANUAL_ONLY = [
    {
        "name": "STM32_Cryptographic",
        "codename": "STM32PQC",
        "note": (
            "Proprietary ST STM32 Cryptographic middleware package (V5.0.0 "
            "or later, which includes ML-KEM and ML-DSA), not git-cloneable. "
            "Download X-CUBE-CRYPTOLIB from "
            "https://www.st.com/en/embedded-software/x-cube-cryptolib.html "
            "and extract it to STM32_Cryptographic/ "
            "at the crypto-benchmark repo root. See Setup.md."
        ),
    },
]

HOST_URL_TEMPLATES = {
    "github": {
        "https": "https://github.com/{path}.git",
        "ssh": "git@github.com:{path}.git",
    },
    "gitlab.pqsh.net": {
        "https": "https://gitlab.pqsh.net/{path}.git",
        "ssh": "git@gitlab.pqsh.net:{path}.git",
    },
}
