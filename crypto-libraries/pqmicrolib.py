class PqMicroLibCore:
    # The pqmicrolib-library presets used here are defined in its presets/crypto-benchmark.json
    # (branch 'crypto-benchmark'): one per software target and tier, named <sw_target>-<tier>, for every
    # target of sw_targets() and for 'linux' (host).
    # goal -> tier. ML-DSA: small: PQS_MLDSA_SIGN_HIGH_RAM / PQS_MLDSA_VERIFY_HIGH_RAM OFF, balanced: ON,
    # fast: balanced built for speed (same as balanced on some targets).
    TIERS = {'smallram':'small', 'balanced':'balanced', 'fast':'fast'}

    # folder of the library's files in target/<cpu>/goals/<algo>/<goal>/, see link_ext.py
    link_name = 'pqcle'

    @classmethod
    def preset(cls, sw_target, goal):
        """pqmicrolib-library preset name of 'sw_target' for 'goal'."""
        return f'{sw_target}-{cls.TIERS[goal]}'

    @classmethod
    def link_dirs(cls, sw_target, goal, algo):
        """(folder of the archives, folder of the headers) of a goal's build, relative to pqmicrolib-library."""
        preset = cls.preset(sw_target, goal)
        return f'out/{preset}/lib', f'out/build/{preset}/inc/pqcle'

    @staticmethod
    def sw_targets():
        return [
            'cortex-m3',
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m52',
            'cortex-m55',
            'rv32imcb',
            'rv32imc',
            'rv64imc'
            ]

    @staticmethod
    def algorithms():
        return {
            'mldsa':['smallram','balanced','fast'],
            # single ML-KEM implementation, built from the <target>-balanced or <target>-fast preset
            'mlkem':['balanced','fast'],
            # single implementation, from the <target>-balanced preset
            'sha2':['balanced']
        }

    @staticmethod
    def supports_algo(sw_target, algo):
        # the sha2 benchmark includes the secure SHA-2 (libsha2_secure.a): built by the Arm presets only
        return algo != 'sha2' or sw_target.startswith('cortex-m')

    @classmethod
    def supports(cls, sw_target, goal, algo):
        # only the targets that have presets
        return sw_target in cls.sw_targets() + ['linux'] and goal in cls.algorithms().get(algo, [])

    def __init__(self):
        self.sw_target = None
        self.codename = 'PQSHIELD'
        self.path = '../pqmicrolib-library'

    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        preset = self.preset(sw_target, goal)
        # The presets build with LTO: they set CFLAGS=-flto -ffat-lto-objects in their
        # environment. CMake prepends $CFLAGS to the toolchain's initial flags, but only when
        # (re)configuring from scratch, hence --fresh (buildit forwards extra arguments to cmake).
        return {
            'dir':'utl/tools',
            'cmd':['./buildit',preset,'--fresh']
        }


helper = PqMicroLibCore()
