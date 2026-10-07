class Pqrv:

    @staticmethod
    def sw_targets():
        return [
            'rv32imc',
            'rv32imcb'
            ]

    @staticmethod
    def algorithms():
        return {
            'mldsa':['fast'],
            'mlkem':['fast'],
        }

    def __init__(self):
        self.sw_target = None
        self.codename = 'PQRV'
        self.path = '../PQRV'

    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        # one library for all algorithms and parameter sets
        return {
            'dir':'libpqrv',
            'cmd':['./buildit',self.sw_target]
        }


helper = Pqrv()
