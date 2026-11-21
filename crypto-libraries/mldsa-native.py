class MldsaNative:

    @staticmethod
    def sw_targets():
        # rv32i is left out: mldsa-native needs 32x32->64 multiplications (M extension)
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
        # small: MLD_CONFIG_REDUCE_RAM, built for size; fast: the default memory mode, built for speed
        return {
            'mldsa':['small','fast'],
        }

    def __init__(self):
        self.sw_target = None
        self.codename = 'MLDSA_NATIVE'
        self.path = '../mldsa-native'

    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        # nothing to build here: crypto-benchmark compiles the sources itself, see libmldsa-lbmk/CMakeLists.txt
        return None


helper = MldsaNative()
