class PqMicroLibCore:
    # The pqmicrolib-library presets used here are defined in its presets/crypto-benchmark.json
    # (branch 'crypto-benchmark'): one per software target and ML-DSA goal, named
    # <sw_target>-<goal>, for every target of sw_targets() and for 'linux' (host).
    # small: PQS_MLDSA_SIGN_HIGH_RAM / PQS_MLDSA_VERIFY_HIGH_RAM OFF, balanced: ON,
    # fast: balanced built for speed (same as balanced on some targets).
    TIERS = ('small', 'balanced', 'fast')

    @classmethod
    def preset(cls, sw_target, goal=None):
        """pqmicrolib-library preset name of 'sw_target' for 'goal'.

        A goal that is not an ML-DSA tier (None, or a goal of another algorithm) selects the
        'balanced' preset: the other algorithms have a single implementation."""
        if goal not in cls.TIERS:
            goal = 'balanced'
        return f'{sw_target}-{goal}'

    @classmethod
    def mldsa_tiers(cls, sw_target):
        """ML-DSA tiers (goals) the library can be built with for 'sw_target'."""
        return cls.TIERS if sw_target in cls.sw_targets() + ['linux'] else ()

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
            # restricted per target by supports(): only the targets that have presets
            'mldsa':['small','balanced','fast'],
            # single ML-KEM implementation, 'balanced' is only a label
            'mlkem':['balanced'],
            'sha2':None
        }

    @staticmethod
    def supports_algo(sw_target, algo):
        # the sha2 benchmark includes the secure SHA-2 (libsha2_secure.a): built by the Arm presets only
        return algo != 'sha2' or sw_target.startswith('cortex-m')

    @classmethod
    def supports(cls, sw_target, goal, algo=None):
        # ML-DSA: the goal must be a tier the target has a preset for.
        if algo in (None, 'mldsa'):
            return goal in cls.mldsa_tiers(sw_target)
        # other algorithms: single implementation, only the goals listed in algorithms()
        goals = cls.algorithms().get(algo)
        return goals is None or goal in goals

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
