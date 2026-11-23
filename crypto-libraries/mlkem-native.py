class MlkemNative:

    @staticmethod
    def sw_targets():
        # the targets of mldsa-native, see mldsa-native.py
        return [
            'cortex-m3',
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m52',
            'cortex-m55',
            'rv32imc',
            'rv32imcb',
            'rv64imc'
            ]

    @staticmethod
    def algorithms():
        # fast: MLK_CONFIG_SERIAL_FIPS202_ONLY and -Os, the fastest configuration measured (see libmlkem-lbmk/CMakeLists.txt)
        return {
            'mlkem':['fast'],
        }

    @staticmethod
    def options(algo):
        # read by libmlkem-lbmk/CMakeLists.txt
        return {
            'opt': 'compiler optimization flag, e.g. -O3 (default -Os)',
            'serial_fips202': '1: MLK_CONFIG_SERIAL_FIPS202_ONLY, 0: the 4-way Keccak (default 1)',
        }

    def __init__(self):
        self.sw_target = None
        self.codename = 'MLKEM_NATIVE'
        self.path = '../mlkem-native'

    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        # nothing to build here: crypto-benchmark compiles the sources itself, see libmlkem-lbmk/CMakeLists.txt
        return None


helper = MlkemNative()
