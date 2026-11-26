class Wolfssl:
    """wolfSSL, built by its own autotools (autogen.sh, configure, make, make install) with the options below,
    into build/<cpu>-<algo>-<goal> of the wolfssl repository.

    What a goal is made of is defined here, as the values of the knobs below; `benchmark.py --opt` overrides
    them one by one to tune a goal (README.md "Tuning a goal")."""

    # configure's options: wolfCrypt only, without what the benchmark does not call, then each algorithm's.
    # --enable-armasm is added on the targets wolfSSL has assembly for (see toolchain())
    CONFIGURE = ['--disable-filesystem', '--disable-crypttests', '--disable-shared', '--enable-cryptonly',
                 '--enable-dh=no', '--enable-ecc=no', '--enable-aesgcm=no', '--enable-chacha=no',
                 '--enable-pkcs8=no', '--enable-pkcs12=no', '--enable-tls=no', '--enable-tlsv12=no',
                 '--enable-tls13=no', '--enable-asn=no', '--enable-rsa=no', '--enable-hkdf=no',
                 '--enable-pwdbased=no', '--enable-hashdrbg=no', '--enable-sha=no', '--enable-aescbc=no',
                 # timing resistance
                 '--enable-harden=yes']
    CONFIGURE_ALGO = {
        'mldsa': ['--enable-mldsa', '--enable-mlkem=no', '--enable-aes=no'],
        'mlkem': ['--enable-mldsa=no', '--enable-mlkem=yes', '--enable-aes=no'],
        'aes': ['--enable-mldsa=no', '--enable-mlkem=no', '--enable-aes=yes', '--enable-cmac'],
    }
    # compiler flags of every build, after the target's and before the goal's
    CFLAGS = ['--specs=nosys.specs', '-flto', '-ffat-lto-objects', '-DHAVE_PK_CALLBACKS', '-DWOLFSSL_USER_IO',
              '-DWOLFSSL_NO_SOCK', '-DWC_NO_RNG', '-DNO_WRITEV', '-DNO_WOLFSSL_DIR']
    CFLAGS_ALGO = {'mldsa': ['-DWOLFSSL_DILITHIUM_NO_ASN1'], 'mlkem': [], 'aes': []}

    # algo -> knob -> (description, {value: compiler flags}); the first value is wolfSSL's default
    KNOBS = {
        'mldsa': {
            'code': ('code size of the arithmetic', {
                'large': [],
                'nolarge': ['-DWOLFSSL_DILITHIUM_NO_LARGE_CODE'],
                'small': ['-DWOLFSSL_DILITHIUM_SMALL']}),
            'keygen': ('memory use of key generation', {
                'full': [],
                'small': ['-DWOLFSSL_DILITHIUM_MAKE_KEY_SMALL_MEM']}),
            'sign': ('memory use of signing: precalc keeps the decoded key vectors, precalc_a the matrix A', {
                'full': [],
                'small': ['-DWOLFSSL_DILITHIUM_SIGN_SMALL_MEM'],
                'precalc': ['-DWOLFSSL_DILITHIUM_SIGN_SMALL_MEM', '-DWOLFSSL_DILITHIUM_SIGN_SMALL_MEM_PRECALC'],
                # the value is the number of rows of A kept: 8 is all of them for every parameter set
                'precalc_a': ['-DWOLFSSL_DILITHIUM_SIGN_SMALL_MEM', '-DWOLFSSL_DILITHIUM_SIGN_SMALL_MEM_PRECALC_A=8']}),
            'verify': ('memory use of verification: small_nomalloc and smallest keep their buffers in the key', {
                'full': [],
                'small': ['-DWOLFSSL_DILITHIUM_VERIFY_SMALL_MEM'],
                'small_nomalloc': ['-DWOLFSSL_DILITHIUM_VERIFY_SMALL_MEM', '-DWOLFSSL_DILITHIUM_VERIFY_NO_MALLOC'],
                # wolfSSL a240b14d leaves mldsa_vec_check_low unused in this mode, an error with its -Werror
                'smallest': ['-DWOLFSSL_DILITHIUM_VERIFY_SMALLEST_MEM', '-Wno-error=unused-function']}),
            'poly64': ('1: the small memory code uses a 64-bit polynomial (2 KiB more, a bit faster)', {
                '0': [],
                '1': ['-DWOLFSSL_DILITHIUM_SMALL_MEM_POLY64']}),
        },
        'mlkem': {
            'code': ('code size of the C arithmetic', {
                'large': [],
                'nolarge': ['-DWOLFSSL_MLKEM_NO_LARGE_CODE'],
                'small': ['-DWOLFSSL_MLKEM_SMALL']}),
            'keygen': ('memory use of key generation', {
                'full': [],
                'small': ['-DWOLFSSL_MLKEM_MAKEKEY_SMALL_MEM']}),
            'encaps': ('memory use of encapsulation', {
                'full': [],
                'small': ['-DWOLFSSL_MLKEM_ENCAPSULATE_SMALL_MEM']}),
            'asm': ('0: C arithmetic instead of the assembly (which only the Cortex-M targets have)', {
                '1': [],
                '0': ['-DWC_MLKEM_NO_ASM']}),
            'nomalloc': ('1: no allocator, the buffers are on the stack', {
                '0': [],
                '1': ['-DWOLFSSL_NO_MALLOC']}),
        },
        'aes': {
            'tables': ('size of the lookup tables', {
                'full': [],
                'small': ['-DWOLFSSL_AES_SMALL_TABLES']}),
            'unroll': ('0: the rounds are a loop', {
                '1': [],
                '0': ['-DWOLFSSL_AES_NO_UNROLL']}),
            # no knob for wolfSSL's bitsliced AES (-DWC_AES_BITSLICED -DHAVE_AES_ECB): tried on 2026-11-25, a CMAC
            # of 16 bytes took 700 times the cycles of the table-based code and more stack than the 40 KiB the
            # harness measures
        },
    }
    # knobs of every algorithm
    COMMON_KNOBS = {
        'sha3': ('Keccak: assembly (which only the Cortex-M targets have), C, or compact C', {
            'asm': [],
            'c': ['-DWC_SHA3_NO_ASM'],
            'small': ['-DWC_SHA3_NO_ASM', '-DWOLFSSL_SHA3_SMALL']}),
        # no flag: wolfSSL's configure chooses, -O2 for these builds. A flag given here comes after it
        'opt': ('compiler optimization flag', {
            'default': [],
            '-Os': ['-Os'],
            '-O2': ['-O2'],
            '-O3': ['-O3']}),
    }

    # algo -> goal -> the knobs that differ from wolfSSL's defaults.
    # Chosen from sizes and Renode runs on Cortex-M33, then timed on the STM32U5A5 (2026-11-25, LIBRARIES.md
    # gives the figures; Renode ranked -Os for ML-KEM and verify=small backwards, the board decided). What did
    # not make it: -O3 (no faster, 4 to 12 KiB more), sign=precalc (3 % faster than sign=small for nearly twice
    # its memory), code=nolarge (nearly the size of large), verify=small_nomalloc and smallest (they move the
    # verification buffers from the heap, where they reuse the memory of a signature, to the key: 5 to 11 KiB
    # more static RAM), sha3=c (the size of the assembly, slower), poly64.
    GOALS = {
        'mldsa': {
            'smallram':  {'code': 'small', 'keygen': 'small', 'sign': 'small', 'verify': 'small', 'opt': '-Os'},
            # the compact Keccak is 2.8 KiB less than the assembly, and Keccak is most of ML-DSA's time
            'smallcode': {'code': 'small', 'keygen': 'small', 'sign': 'small', 'verify': 'small', 'opt': '-Os',
                          'sha3': 'small'},
            # the matrix A is expanded once per signature, not once per attempt: most of the speed of the
            # default signature with 30 % less memory
            'balanced':  {'code': 'small', 'keygen': 'small', 'sign': 'precalc_a', 'verify': 'small', 'opt': '-Os'},
            # the small memory verification is 5 to 6 % faster than the default one on the board, and needs
            # 11 KiB instead of 80 at ML-DSA-87; -Os would cost 6 %
            'fast':      {'verify': 'small'},
        },
        'mlkem': {
            'smallram':  {'code': 'small', 'keygen': 'small', 'encaps': 'small', 'opt': '-Os'},
            'smallcode': {'code': 'small', 'keygen': 'small', 'encaps': 'small', 'opt': '-Os', 'nomalloc': '1',
                          'sha3': 'small', 'asm': '0'},
            # no allocator: 3.4 KiB less flash at the speed of smallram, the buffers are on the stack
            'balanced':  {'code': 'small', 'keygen': 'small', 'encaps': 'small', 'opt': '-Os', 'nomalloc': '1'},
            # -Os is 3 to 8 % faster than wolfSSL's -O2 on the board (fewer instruction cache misses), 2 KiB less
            'fast':      {'opt': '-Os'},
        },
        'aes': {
            'smallcode': {'tables': 'small', 'unroll': '0', 'opt': '-Os'},
            'fast':      {},
        },
    }

    # folder of the library's files in target/<cpu>/goals/<algo>/<goal>/, see link_ext.py
    link_name = 'wolfssl'

    @staticmethod
    def sw_targets():
        return [
            'cortex-m3',
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m52',
            'cortex-m55',
            'cortex-m85',
            'rv32i',
            'rv32imc',
            'rv32imcb',
            'rv64imc'
            ]

    @classmethod
    def algorithms(cls):
        # on cortex-m*, ML-DSA and ML-KEM use wolfSSL's Thumb-2 assembly (see toolchain()); AES stays C
        return {algo: list(goals) for algo, goals in cls.GOALS.items()}

    @staticmethod
    def toolchain(sw_target, algo):
        """(configure's --host, compiler flags of the target, its configure options): -march/-mabi as in
        target/<cpu>.cmake of crypto-benchmark."""
        if sw_target.startswith('cortex-m'):
            # Thumb-2 assembly for ML-DSA (Keccak only) and ML-KEM. Not for AES: wolfSSL's Thumb-2 AES ignores
            # WOLFSSL_AES_SMALL_TABLES, so smallcode and fast would build the same code
            return 'arm-none-eabi', [f'-mcpu={sw_target}'], ['--enable-armasm=yes'] if algo != 'aes' else []
        # RISC-V: the host is riscv-none-elf rather than riscv32/riscv64 on purpose: configure would then enable
        # RISC-V inline assembly in sp_int.c, which uses mul (not available on rv32i)
        march = {
            'rv32i': ['-march=rv32i_zicsr', '-mabi=ilp32'],
            'rv32imc': ['-march=rv32imc_zicsr', '-mabi=ilp32'],
            'rv32imcb': ['-march=rv32imc_zbb_zbc_zbs_zbkb_zbkc_zbkx_zicsr', '-mabi=ilp32'],
            'rv64imc': ['-march=rv64imc_zicsr', '-mabi=lp64'],
        }
        if sw_target not in march:
            raise ValueError(f'wolfssl: no toolchain for target {sw_target}')
        return 'riscv-none-elf', march[sw_target], ['--enable-armasm=no'] if algo != 'aes' else []

    @classmethod
    def knobs(cls, algo):
        return {**cls.KNOBS[algo], **cls.COMMON_KNOBS}

    @classmethod
    def options(cls, algo):
        return {name: f'{description}: {", ".join(values)}'
                for name, (description, values) in cls.knobs(algo).items()}

    @classmethod
    def check_options(cls, algo, opts):
        """Called by goals.py before anything is built: the values must be known too."""
        for goal in cls.GOALS[algo]:
            cls.settings(algo, goal, opts)

    @classmethod
    def settings(cls, algo, goal, opts=None):
        """The value of every knob for a goal, with the options on top."""
        knobs = cls.knobs(algo)
        settings = {name: next(iter(values)) for name, (_, values) in knobs.items()}
        for name, value in {**cls.GOALS[algo][goal], **(opts or {})}.items():
            if name not in knobs:
                raise ValueError(f'wolfssl, {algo}: unknown option "{name}" (it has: {", ".join(sorted(knobs))})')
            if value not in knobs[name][1]:
                raise ValueError(f'wolfssl, {algo}: option {name}={value} is not one of '
                                 f'{", ".join(knobs[name][1])}')
            settings[name] = value
        return settings

    @classmethod
    def flags(cls, algo, goal, opts=None):
        """The compiler flags of a goal with these options, after CFLAGS and CFLAGS_ALGO."""
        knobs = cls.knobs(algo)
        return [flag for name, value in cls.settings(algo, goal, opts).items() for flag in knobs[name][1][value]]

    @staticmethod
    def build_name(algo, goal_id):
        """One build per algorithm and goal (or custom_<hash>, a goal with options: goal_id() of goals.py)."""
        return f'{algo}-{goal_id}'

    @classmethod
    def link_dirs(cls, sw_target, goal_id, algo):
        """(folder of the archives, folder of the headers) of a build, relative to the wolfssl repository."""
        build = f'build/{sw_target}-{cls.build_name(algo, goal_id)}'
        return f'{build}/lib', f'{build}/include/wolfssl'

    @classmethod
    def custom_ids(cls, root, sw_target, algo):
        """The builds with options present in the wolfssl repository (at 'root'), as their custom_<hash>."""
        import glob, os
        prefix = os.path.join(root, 'build', f'{sw_target}-{cls.build_name(algo, "")}')
        return sorted(os.path.basename(p)[len(os.path.basename(prefix)):] for p in glob.glob(prefix + 'custom_*'))

    def __init__(self):
        self.sw_target = None
        self.codename = 'WOLFSSL'
        self.path = '../wolfssl'

    def build_cmd(self,sw_target,goal,pset,algo,opts=None):
        """wolfSSL's own build, run in the wolfssl repository. DEBUG_INFO=yes in the environment adds -g: debug
        information only, the code is the same (README.md "Debugging using Renode")."""
        import os
        # goals.py of the repository's root, which is in the path of every script that loads a manifest
        import goals as goals_module
        self.sw_target = sw_target
        host, target_flags, target_configure = self.toolchain(sw_target, algo)
        debug_info = ['-g'] if os.environ.get('DEBUG_INFO', 'no') != 'no' else []
        cflags = [*target_flags, *debug_info, *self.CFLAGS, *self.CFLAGS_ALGO[algo], *self.flags(algo, goal, opts)]
        configure = [
            '--enable-debug=no', f'--host={host}',
            f'CC={host}-gcc', f'AR={host}-gcc-ar', f'STRIP={host}-strip', f'RANLIB={host}-gcc-ranlib',
            'CFLAGS=' + ' '.join(cflags),
            *self.CONFIGURE, *self.CONFIGURE_ALGO[algo], *target_configure,
        ]
        build = f'build/{sw_target}-{self.build_name(algo, goals_module.goal_id(goal, opts))}'
        return {
            'dir': '.',
            'cmd': ['sh', '-exc', 'prefix="$PWD/$1"; shift; ./autogen.sh; ./configure --prefix="$prefix" "$@"; '
                    'make; make install', 'wolfssl-build', build, *configure],
        }


helper = Wolfssl()
