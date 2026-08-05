import os 
import argparse 
import logging
import runpy
import glob
import subprocess
import multiprocessing as mp
import traceback
import sys
sys.path.insert(0, '../lean-benchmark')
import lean_benchmark



class Process(mp.Process):
    def __init__(self, *args, **kwargs):
        mp.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = mp.Pipe()
        self._exception = None

    def run(self):
        try:
            mp.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))
            # raise e  # You can still rise this exception if you need to

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception



def first(s):
    for e in s:
        break
    return e

class Mldsa(object):
    @staticmethod
    def psets():
        return ['44','65', '87']

    @staticmethod
    def operations():
        return ['key-exp','sign','verify']

class Sha2(object):
    @staticmethod
    def psets():
        return ['224','256', '384', '512', '512/224', '512/256']

    @staticmethod
    def operations():
        return ['hash']


algorithms_catalog = {'mldsa':Mldsa(),'sha2':Sha2()}

goals_catalog = {'small','balanced','fast'}


def invoke_tool(cwd,*cmd):
    try:
        logging.debug(cmd)
        res = subprocess.run(cmd, capture_output=True, check=True, shell=False, cwd=cwd)  # noqa: S603
        outstr = res.stdout.decode()
        logging.debug(outstr)
        logging.debug(res.stderr.decode())
    except subprocess.CalledProcessError as e:
        nl = '\n'
        logging.debug(f'{cmd[0]} failed')
        logging.debug(f'arguments: {e.args}')
        logging.debug(f'stdout{nl}{e.stdout}')
        logging.debug(f'stderr{nl}{e.stderr}')
        logging.debug(f'return code: {e.returncode}')
        raise
    return outstr,res.returncode


if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument(
        'device', help='Path to the serial device', type=str
    )
    parser.add_argument(
        '--baud', default=115200, help='Baudrate', type=int
    )
    parser.add_argument(
        '--exclusive', help='Exclusive access', action='store_true'
    ) 
    parser.add_argument(
        '--dry-run', help='List the benchmarks without running them', action='store_true'
    ) 
    parser.add_argument(
        '--hw-platform', help='Specify one or more hardware platforms (must be reachable using "device")', default=None, nargs='+', type=str
    )  
    parser.add_argument(
        '--sw-target', help='Specify one or more software build targets', default=None, nargs='+', type=str
    )  
    parser.add_argument(
        '--goal', help='List of goals to benchmark', default=None, nargs='+', choices=goals_catalog
    )
    parser.add_argument(
        '--lib', help='List of libraries to benchmark', default=None, nargs='+', type=str
    )
    parser.add_argument(
        '--algo', help='List of algorithms to benchmark', default=None, nargs='+', type=str
    )
    parser.add_argument(
        '--pset', help='List of parameter sets to benchmark, this require --algo with exactly one algorithm', default=None, nargs='+', type=str
    )
      
    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)
     
    def get_names(c):
        return [x['name'] for x in c]

    #- detect hw platforms
    if args.hw_platform:
        hwp = args.hw_platform
    else:
        hwp = glob.glob(os.path.join('hardware-platforms','*.py'))
        logging.info(f'Detected hardware platforms: {hwp}')
    #refine hw_platforms: each entry can be 
    # - a path to a python file describing the platform
    # - a name, i.e., 'rp2350'
    hw_platforms = []
    for i in range(len(hwp)):
        original = hwp[i]
        org = original
        if os.path.exists(org) and org.endswith('.py'):
            #it is a path
            manifest = org
            name = os.path.basename(org)[:-3]
        else:
            #it is a name
            name = org
            p = os.path.join('hardware-platforms',f'{name}.py')
            if not os.path.exists(p):
                m = f'HW platform {name}: {p} does not exist'
                logging.error(m)
                raise RuntimeError(m)
            manifest = p
        if not os.path.exists(manifest):
            m = f'HW platform {name} discarded: {manifest} does not exist'
            logging.warning(m)
            continue
        params = runpy.run_path(manifest)
        hw_platform = {'name':name, 'helper': params['helper']}
        logging.debug(f'{original} -> {hw_platform}')
        hw_platforms.append(hw_platform)
    logging.info(f'Valid hardware platforms: {get_names(hw_platforms)}')
    if len(hw_platforms) == 0:
        logging.error('Need at least one hardware platform')
        exit(-1)
    
    #- detect sw_libs
    if args.lib:
        libs = args.lib
    else:
        libs = glob.glob(os.path.join('crypto-libraries','*.py'))
        logging.info(f'Detected crypto libraries: {libs}')
    #refine sw_libs: each entry can be 
    # - a path to a python file describing the lib
    # - a name, i.e., 'dilithium-lowram'
    
    sw_libs = []
    for i in range(len(libs)):
        original = libs[i]
        org = original
        if os.path.exists(org) and org.endswith('.py'):
            #it is a path
            manifest = org
            name = os.path.basename(org)[:-3]
        else:
            #it is a name
            name = org
            p = os.path.join('crypto-libraries',f'{name}.py')
            if not os.path.exists(p):
                m = f'SW library {name}: {p} does not exist'
                logging.error(m)
                raise RuntimeError(m)
            manifest = p
        if not os.path.exists(manifest):
            m = f'SW library {name} discarded: {manifest} does not exist'
            logging.warning(m)
            continue
        params = runpy.run_path(manifest)
        sw_lib = {'name':name, 'path':p, 'helper': params['helper']}
        logging.debug(f'{original} -> {sw_lib}')
        sw_libs.append(sw_lib)
    logging.info(f'Valid software libraries (preliminary): {get_names(sw_libs)}')
    if len(sw_libs) == 0:
        logging.error('Need at least one software library')
        exit(-2)

    #- detect software targets
    sw_targets = set()
    for hwp in hw_platforms:
        for t in hwp['helper'].sw_targets():
            sw_targets.add(t)
    if args.sw_target:
        sw_targets = set(args.sw_target)
    if len(sw_targets) == 0:
        logging.error('Need at least one software target')
        exit(-3)    
    usable_sw_targets = set()
    for lib in sw_libs:
        # check there is at least one sw target which is supported
        found = False
        for t in sw_targets:
            if t in lib['helper'].sw_targets():
                found = True
                usable_sw_targets.add(t)
        if not found:
            logging.warning(f'SW library {lib['name']} discarded because it does not support any of the selected software targets ({sw_targets})')
            sw_libs.remove(lib)
    if len(sw_libs) == 0:
        logging.error('Need at least one software library')
        exit(-3)
    # Keep only the software targets which are useful, i.e., there is at least one lib on one platform that needs it    
    sw_targets = usable_sw_targets
    logging.info(f'SW targets: {sw_targets}')

    algos = set()
    for lib in sw_libs:
        for algo in lib['helper'].algorithms():
            algos.add(algo)
    if args.algo:
        for a in args.algo:
            if a not in algos:
                logging.error(f'Algorithm "{a}" is not supported by any of the selected software libraries {sw_libs}')
                exit(-5)
        algos = set(args.algo)
    logging.info(f'Algorithms: {algos}')

    psets = args.pset
    if psets:
        if len(algos) > 1:
            logging.error(f'--pset cannot be used because several algorithms are selected ({len(algos)})')
            exit(-4)
        # check specified psets exist for the selected algo
        for p in psets:
            a = first(algos)
            if p not in algorithms_catalog[a].psets():
                logging.error(f'"{p}" in not a valid parameter set for algorithm "{a}"')
                exit(-6)
    
    goals = args.goal
    if goals:
        # check specified goal exist for the selected libraries and algorithms
        for g in goals:
            for a in algos:
                usable_sw_libs = []
                for lib in sw_libs:
                    lib_algos = lib['helper'].algorithms()
                    if lib_algos[a] and g not in lib_algos[a]:
                        logging.debug(f'"{lib['name']}" discarded because it does not support goal "{g}" for algorithm "{a}"')
                    else:
                        usable_sw_libs.append(lib)
                sw_libs = usable_sw_libs

    # final pass on software libraries: remove the ones that don't support any of the algorithms
    useful_sw_libs = []
    for lib in sw_libs:
        lib_algos = lib['helper'].algorithms()
        for a in algos:
            if a in lib_algos:
                useful_sw_libs.append(lib)
                break
    if len(sw_libs) > len(useful_sw_libs):
        sw_libs = useful_sw_libs
    logging.info(f'Valid software libraries: {get_names(sw_libs)}')    

    def tool(cwd, *cmd):
        if cwd:
            logging.info(f'Executing from {cwd}: {cmd}')
        else:
            logging.info(f'Executing {cmd}')
        if args.dry_run:
            return '',0
        else:
            out,res = invoke_tool(cwd, *cmd)
            if res != 0:
                raise RuntimeError(res)
            return out,res
        
    def process_cmd(full_cmd, root):
        if full_cmd:
            cwd = None
            if 'dir' in full_cmd:
                cwd=full_cmd['dir']
                if os.path.relpath(cwd) == cwd:
                    # if cwd is relative, make it relative to the path of the manifest
                    cwd=os.path.join(root,cwd)
            if cwd is None:
                cwd=root
            out,res = tool(cwd,*full_cmd['cmd'])
            if res != 0:
                raise RuntimeError(res) 
        else:
            logging.debug('process_cmd: full_cmd is None')

    link_ext_dict = runpy.run_path('link_ext.py')
    def link_ext(goal):
        logging.debug(f'link_ext({goal})')
        if not args.dry_run:
            link_ext_dict['main'](goal=goal)
    
    format_result_dict = runpy.run_path('format_results.py')
    def format_result(target,algo,format,*,
         root='.',
         lib=None,
         pset=None,
         op=None,
         hw_platform=None,
         file=None):
        logging.debug(f'format_result({target},{algo},{format},{root},{lib},{pset},{op},{hw_platform},{file})')
        if not args.dry_run:
            file = open(file,'w')
            format_result_dict['main'](target,algo,format,
                                       root=root,
                                       args_lib=lib,
                                       args_pset=pset,
                                       args_op=op,
                                       args_hw_platform=hw_platform,
                                       file=file)

    out_files = []
    for hwp_dict in hw_platforms:
        hwp = hwp_dict['helper']
        hwp_name = hwp_dict['name']
        hwp_path = hwp.path
        hwp_sw_targets = hwp.sw_targets()
        for swt in sw_targets:
            if swt not in hwp_sw_targets:
                continue
            for lib in sw_libs:
                lib_codename = lib['helper'].codename
                for algo in algos:
                    if psets is None:
                        all_psets = algorithms_catalog[algo].psets()
                    else:
                        all_psets = psets
                    if goals is None:
                        if algo in lib['helper'].algorithms():
                            all_goals = lib['helper'].algorithms()[algo]
                            if all_goals is None:
                                all_goals = ['balanced']
                        else:
                            continue
                    else:
                        all_goals = goals

                    #args.dry_run=True
                    # build and run benchmark    
                    for goal in all_goals:
                        for pset in all_psets:
                            
                            logging.info(f'{hwp_name}, {swt}, {lib['name']}, {algo}, {goal}, {pset}')
                            pset_code = pset #TODO handle sha2 codes
                            
                            logging.info('build library')
                            process_cmd(lib['helper'].build_cmd(swt,goal,pset_code),lib['helper'].path)

                            link_ext(goal)

                            logging.info('build crypto-benchmark')
                            out,res = tool(None, './buildit',f'on/{swt}',algo,pset_code,lib_codename)
                            
                            logging.info('build firmware')
                            process_cmd(hwp.build_cmd(swt),hwp_path)

                            logging.info('load firmware')
                            load_cmd = hwp.load_cmd(swt)
                            process_cmd(load_cmd,hwp_path)

                            logging.info('run firmware')
                            p1 = Process(target=process_cmd, args=[hwp.run_cmd(swt),hwp_path])
                            p1.start()
                            p2 = Process(target=tool,args=[None,'./get-results',args.device,'--device-timeout=180','--write=1'])
                            p2.start()
                            p1.join()
                            if p1.exception:
                                logging.error(f'Hardware platform failed to run the firmware')
                                error,trace = p1.exception
                                logging.error(trace)
                                exit(-7)
                            p2.join()
                            if p2.exception:
                                logging.error(f'An exception occured in lean_benchmark.py')
                                error,trace = p2.exception
                                logging.error(trace)
                                exit(-8)

                            # build stub target for static memory sizes
                            logging.info('build crypto-benchmark STUB for size')
                            out,res = tool(None, './buildit',f'on/{swt}',algo,pset_code,'STUB')
                    #args.dry_run=False
                    # compute sizes
                    logging.info('Compute size')
                    outdir = f'build/{swt}'
                    elf_files = glob.glob(f'{outdir}/crypto-benchmark-{lib_codename}-*.elf')
                    elf_files += glob.glob(f'{outdir}/crypto-benchmark-STUB-*.elf')
                    out,res = tool(None, 'size',*elf_files)
                    with open(f'{outdir}/sizes.txt','w') as f:
                        print(out,file=f)
                    file_name = f'{lean_benchmark.get_timestamp()}-{hwp_name}-{swt}-{lib['name']}-{algo}.csv'
                    if len(hwp_sw_targets) > 1:
                        hwp_name += f'-{swt}'
                    logging.info('Formating results')
                    format_result(swt,algo,'csv',lib=[lib_codename],hw_platform=hwp_name,file=file_name)
                    out_files.append(file_name)
    logging.info(f'All benchmark done, see output files:\n\t{'\n\t'.join(out_files)}')
    
                            
                            
                            