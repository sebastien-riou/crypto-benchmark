class Stm32u5a5:

    @staticmethod
    def sw_targets():
        return ['cortex-m33']

    def __init__(self):
        self.sw_target = None
        self.path = '../crypto-benchmark-stm32u5'
        self.run_in_parallel = False # wait 'run' script to exit before starting leanbenchmark
    
    def build_cmd(self,sw_target):
        self.sw_target = sw_target
        return {
            'cmd':['make','clean','all']
        }
    
    def load_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but load for {sw_target} is requested')
        return {
            'cmd':['./flash']
        }
    
    def run_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but run for {sw_target} is requested')
        return {
            'cmd':['./run']
        }

    def com_device_cmd(self):
        return {
            'cmd':['./find-uart']
        }
    
helper = Stm32u5a5()