class M5531:

    @staticmethod
    def sw_targets():
        return ['cortex-m55','cortex-m52']

    def __init__(self):
        self.sw_target = None
        self.path = '../crypto-benchmark-m5531'
    
    def build_cmd(self,sw_target):
        self.sw_target = sw_target
        return {
            'cmd':['./buildit']
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
        # workaround Nuvoton's weirdness wrt DWT
        input("Start the firmware manually by using the 'Run' debug target in the crypto-benchmark-m5531 repo (VSCode), then press ENTER")
        return None
    
helper = M5531()