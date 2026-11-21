class Pqm4:

    @staticmethod
    def sw_targets():
        # the assembly needs DSP instructions and FPU registers (see cmake/pqm4.cmake): no cortex-m3, no RISC-V
        return [
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m52',
            'cortex-m55',
            ]

    @staticmethod
    def algorithms():
        # fast: m4fspeed (ML-KEM) / m4f (ML-DSA); small: m4fstack
        return {
            'mlkem':['small','fast'],
            'mldsa':['small','fast'],
        }

    def __init__(self):
        self.sw_target = None
        self.codename = 'PQM4'
        self.path = '../pqm4'

    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        # nothing to build here: crypto-benchmark compiles the sources itself, see cmake/pqm4.cmake
        return None


helper = Pqm4()
