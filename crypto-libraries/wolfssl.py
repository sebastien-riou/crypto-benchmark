class Wolfssl:

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
            'mldsa':['small','balanced','fast'],
            'mlkem':['small','fast','small-armasm','fast-armasm'],
            'aes':['small','fast'],
        }

    @staticmethod
    def supports(sw_target, goal, algo=None):
        # the -armasm goals use wolfSSL's Thumb-2 assembly: cortex-m* only
        return not goal.endswith('-armasm') or sw_target.startswith('cortex-m')

    def __init__(self):
        self.sw_target = None
        self.codename = 'WOLFSSL'
        self.path = '../wolfssl'
    
    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        return {
            'dir':'.',
            'cmd':[f'./buildit-{algo}-{goal}',f'{self.sw_target}','no']
        }

    
helper = Wolfssl()