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
        # fast: m4fspeed (ML-KEM) / m4f (ML-DSA); smallram: m4fstack
        return {
            'mlkem':['smallram','fast'],
            'mldsa':['smallram','fast'],
        }

    @staticmethod
    def options(algo):
        # read by cmake/pqm4.cmake
        return {
            'opt': "compiler optimization flag (default -O3, pqm4's own speed setting)",
            'impl': "pqm4 implementation folder, e.g. m4fspeed, m4fstack, m4f, clean (default: the goal's)",
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
