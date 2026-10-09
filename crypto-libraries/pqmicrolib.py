class PqMicroLibCore:
    # pqmicrolib-library CMake preset (without the 'gcc-' prefix) of each software target, and
    # the ML-DSA tiers (PQS_MLDSA_TIER, same names as the crypto-benchmark goals) it can be
    # built with. Targets with several tiers have one preset per tier, gcc-<preset>-<goal>;
    # the other targets have a single preset with a fixed tier.
    PRESETS = {
        'cortex-m3':  ('armv7m',           ('small',)),
        'cortex-m4':  ('armv7em',          ('balanced',)),
        'cortex-m7':  ('armv7em',          ('balanced',)),
        'cortex-m33': ('armv8m',           ('small', 'balanced', 'fast')),
        'cortex-m52': ('armv8_1m',         ('balanced',)),
        'cortex-m55': ('armv8_1m',         ('balanced',)),
        'rv32imcb':   ('rv32imcb',         ('small', 'balanced', 'fast')),
        'rv32imac':   ('rv32imac',         ('balanced',)),
        'rv64imac':   ('rv64imac',         ('balanced',)),
        'linux':      ('x86_64-linux-gnu', ('small',)),
    }

    @classmethod
    def preset(cls, sw_target, goal=None):
        """pqmicrolib-library preset name of 'sw_target', without the 'gcc-' prefix.

        For the targets that have one preset per ML-DSA tier, 'goal' selects the preset.
        It is ignored for the other targets (single preset, fixed tier)."""
        base, tiers = cls.PRESETS.get(sw_target, (sw_target, ()))
        if len(tiers) > 1 and goal in tiers:
            return f'{base}-{goal}'
        return base

    @classmethod
    def mldsa_tiers(cls, sw_target):
        """ML-DSA tiers (goals) the library can be built with for 'sw_target'."""
        return cls.PRESETS.get(sw_target, (sw_target, ()))[1]

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
            'rv32imac',
            'rv64imac'
            ]

    @staticmethod
    def algorithms():
        return {
            # restricted per target by supports(): only the tiers of the target's preset(s)
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
        # ML-DSA: the goal must be a tier the target's preset(s) can be built with.
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
        preset = f'gcc-{self.preset(sw_target, goal)}'
        # CMake prepends $CFLAGS to the toolchain's initial flags, but only when (re)configuring
        # from scratch, hence --fresh (buildit forwards extra arguments to cmake).
        return {
            'dir':'utl/tools',
            'cmd':['env','CFLAGS=-flto -ffat-lto-objects','./buildit',preset,'--fresh']
        }


helper = PqMicroLibCore()
