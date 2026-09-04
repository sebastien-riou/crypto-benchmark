class PqMicroLibCore:
    @staticmethod
    def preset(sw_target: str):
        match sw_target:
            case 'cortex-m3':
                return 'armv7m'
            case 'cortex-m4' | 'cortex-m7':
                return 'armv7me'
            case 'cortex-m33':
                return 'armv8m',
            case 'cortex-m52' | 'cortex-m55':
                return 'armv8_1m'
            case _:
                return sw_target
        

    @staticmethod
    def sw_targets():
        return [
            'cortex-m3',
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m52',
            'cortex-m55',
            'rv32imac',
            'rv64imac'
            ]

    @staticmethod
    def algorithms():
        return {
            'mldsa':None, #['small','balanced'],
            'sha2':None
        }
    
    def __init__(self):
        self.sw_target = None
        self.codename = 'PQSHIELD'
        self.path = '../pqmicrolib-library'
    
    def build_cmd(self,sw_target,goal,pset):
        self.sw_target = sw_target
        preset = f'gcc-{self.preset(sw_target)}'
        return {
            'dir':'utl/tools',
            'cmd':['./buildit',preset]
        }

    
helper = PqMicroLibCore()