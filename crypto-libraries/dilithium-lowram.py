class DilithiumLowRam:

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

    @staticmethod
    def algorithms():
        return {
            'mldsa':['small'],
        }
    
    def __init__(self):
        self.sw_target = None
        self.codename = 'OPEN_SOURCE'
        self.path = '../dilithium-lowram'
    
    def build_cmd(self,sw_target,goal,pset):
        self.sw_target = sw_target
        return {
            'dir':'libpqcrystals-mldsa-lowram',
            'cmd':['./buildit-core',f'on/{self.sw_target}','minSizeRel',pset]
        }

    
helper = DilithiumLowRam()