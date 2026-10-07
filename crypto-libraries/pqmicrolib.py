class PqMicroLibCore:
    @staticmethod
    def preset(sw_target: str):
        match sw_target:
            case 'cortex-m3':
                return 'armv7m'
            case 'cortex-m4' | 'cortex-m7':
                return 'armv7me'
            case 'cortex-m33':
                return 'armv8m'
            case 'cortex-m52' | 'cortex-m55':
                return 'armv8_1m'
            case 'rv32imcb':
                # no preset uses the bit manipulation extensions: RV32IMAC code, free of
                # atomic instructions, also runs on the rv32imcb target (no A extension)
                return 'rv32imac'
            case _:
                return sw_target
        

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
            'mldsa':None, #['small','balanced'],
            'mlkem':['balanced'],
            'sha2':None
        }

    @staticmethod
    def supports_algo(sw_target, algo):
        # the sha2 benchmark includes the secure SHA-2 (libsha2_secure.a): built by the Arm presets only
        return algo != 'sha2' or sw_target.startswith('cortex-m')

    def __init__(self):
        self.sw_target = None
        self.codename = 'PQSHIELD'
        self.path = '../pqmicrolib-library'
    
    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        preset = f'gcc-{self.preset(sw_target)}'
        # CMake prepends $CFLAGS to the toolchain's initial flags, but only when (re)configuring
        # from scratch, hence --fresh (buildit forwards extra arguments to cmake).
        return {
            'dir':'utl/tools',
            'cmd':['env','CFLAGS=-flto -ffat-lto-objects','./buildit',preset,'--fresh']
        }

    
helper = PqMicroLibCore()