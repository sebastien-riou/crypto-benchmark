CORE = [
    {
        "name": "lean-benchmark",
        "host": "github",
        "path": "sebastien-riou/lean-benchmark",
        "default_tag": "v0.0.9",
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
        "default_tag": "v0.0.14",
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
            "default_tag": "crypto-benchmark-0.0.8",
            "recurse_submodules": False,
            "build": None,  # see repo's own README -- no proven single command
            "docs_hint": "wolfssl/README.md",
        },
        {
            "name": "pqmicrolib-library",
            "codename": "PQSHIELD",
            "host": "gitlab.pqsh.net",
            "path": "engineering/sw/pqmicrolib/pqmicrolib-library",
            "default_tag": "v1.4.0",
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
            "default_tag": "crypto-benchmark-0.0.11",
            "helper_module": "rp2350",  # hardware-platforms/rp2350.py, same one benchmark.py uses
            "setup": ["./setup-pico-sdk"],  # idempotent: clones pico-sdk if missing
        },
        {
            "name": "crypto-benchmark-stm32u5",
            "host": "github",
            "path": "sebastien-riou/crypto-benchmark-stm32u5",
            "default_tag": "crypto-benchmark-0.0.10",
            "helper_module": "stm32u5",  # hardware-platforms/stm32u5.py
            "setup": None,  # nothing extra needed beyond its own repo
        },
        {
            "name": "crypto-benchmark-m5531",
            "host": "github",
            "path": "sebastien-riou/crypto-benchmark-m5531",
            "default_tag": "crypto-benchmark-0.0.10",
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
            "Proprietary ST X-Cube PQC package, not git-cloneable. Download "
            "from https://www.st.com/en/embedded-software/x-cube-pqc.html "
            "and extract to STM32_Cryptographic/ at the crypto-benchmark "
            "repo root. See Setup.md."
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
