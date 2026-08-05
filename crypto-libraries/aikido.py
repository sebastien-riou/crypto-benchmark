class PqMicroLibCore:

    @staticmethod
    def sw_targets():
        return [
            'cortex-m3',
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m52',
            'rv32i',
            'rv32imc',
            'rv32imcb',
            'rv64imc'
            ]

    @staticmethod
    def algorithms():
        return {
            'mldsa':['small','balanced'],
            'sha2':None
        }
    
    def __init__(self):
        self.sw_target = None
        self.codename = 'PQSHIELD'
        self.path = '../aikido'
    
    def build_cmd(self,sw_target,goal,pset):
        self.sw_target = sw_target
        return {
            'dir':'utl/tools',
            'cmd':['./buildit',f'gcc-{self.sw_target}-{goal}']
        }

    
helper = PqMicroLibCore()