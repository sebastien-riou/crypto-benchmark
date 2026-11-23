class Wolfssl:

    # goal -> the name the wolfssl repository (branch 'crypto-benchmark') gives to the matching configuration:
    # it is built by buildit-<algo>-<name> into build/<cpu>-<name>
    BUILD_NAMES = {
        # smallram: WOLFSSL_DILITHIUM_SMALL and the SMALL_MEM options; balanced: WOLFSSL_DILITHIUM_SMALL only
        'mldsa': {'smallram':'small', 'balanced':'balanced', 'fast':'fast'},
        # smallram: WOLFSSL_MLKEM_SMALL and the SMALL_MEM options
        'mlkem': {'smallram':'small', 'fast':'fast'},
        # smallcode: WOLFSSL_AES_SMALL_TABLES
        'aes':   {'smallcode':'small', 'fast':'fast'},
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
        # on cortex-m*, the ML-DSA and ML-KEM goals use wolfSSL's Thumb-2 assembly (see buildit-toolchain in the
        # wolfssl repository); AES stays C
        return {algo: list(names) for algo, names in cls.BUILD_NAMES.items()}

    @classmethod
    def link_dirs(cls, sw_target, goal, algo):
        """(folder of the archives, folder of the headers) of a goal's build, relative to the wolfssl repository."""
        build = f'build/{sw_target}-{cls.BUILD_NAMES[algo][goal]}'
        return f'{build}/lib', f'{build}/include/wolfssl'

    def __init__(self):
        self.sw_target = None
        self.codename = 'WOLFSSL'
        self.path = '../wolfssl'

    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        return {
            'dir':'.',
            'cmd':[f'./buildit-{algo}-{self.BUILD_NAMES[algo][goal]}',f'{self.sw_target}','no']
        }


helper = Wolfssl()
