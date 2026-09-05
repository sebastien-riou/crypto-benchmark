import logging
import argparse
import os
import sys
import report_footprint
import humanfriendly
import glob
import pickle
import math
sys.path.insert(0, '../lean-benchmark')
import lean_benchmark
from lean_benchmark import get_field, format_number


def format_size_kib(num: int, *,precision=2) -> str:
    divider = 1024
    r = num/divider
    out = f'{r:.{precision}f}'
    return out

def format_number_millions(num: int, *,precision=2) -> str:
    divider = 1000*1000
    r = num/divider
    out = f'{r:.{precision}f}'
    return out

def gen_latex_footprint_table(libs,*, lib_list=None, pset_list=None) -> str:
    out = r"""
    \begin{table}[H]
    \centering
    \setlength{\belowcaptionskip}{2pt}
    \caption{Memory footprint for key generation, signing and verification (in KiB).}
    \label{tab:mldsa-footprint}
    \footnotesize
    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}|l|r|r|r|r|r|}
    \hline
    \textbf{Implementation} &
    \textbf{Level} &
    \textbf{Stack} &
    \textbf{Heap} &
    \textbf{Static RAM} &
    \textbf{Read-only} \\
    """

    for lib in sorted(libs.keys()):
        if lib_list and lib not in lib_list:
                continue
        out += '\\hline\n'
        for pset in sorted(libs[lib].keys()):
            if pset_list and pset not in pset_list:
                continue
            stack = f'{format_size_kib(libs[lib][pset]['stack']):>5}'
            heap  = f'{format_size_kib(libs[lib][pset]['heap']):>5}'
            rw    = f'{format_size_kib(libs[lib][pset]['rw']):>5}'
            ro    = f'{format_size_kib(libs[lib][pset]['ro']):>5}'
            out += r'\texttt{'+f'{lib:20}'+'} & '+str(pset)+f' & {stack} & {heap} & {rw} & {ro} \\\\\n'
    
    out += r"""    \hline
    \end{tabular*}
    \end{table}
    """

    return out

def gen_latex_perf_table(libs,*, lib_list=None, pset_list=None, op_list=None) -> str:
    out = r"""
    \begin{table}[H]
    \centering
    \setlength{\belowcaptionskip}{2pt}
    \caption{Performance for a 69-byte message and zero-length context (in million cycles).}
    \label{tab:mldsa-perf}
    \footnotesize
    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}|l|r|r|r|r|r|}
    \hline
    \textbf{Implementation} &
    \textbf{Level} &
    \textbf{Operation} &
    \textbf{Minimum} &
    \textbf{Average\textsuperscript{a}} &
    \textbf{Worst observed\textsuperscript{b}} \\
    """

    for lib in sorted(libs.keys()):
        if lib_list and lib not in lib_list:
            continue
        out += '\\hline\n'
        for pset in sorted(libs[lib].keys()):
            if pset_list and pset not in pset_list:
                continue
            for op in ['key-exp','sign','verify']:
                if op_list and op not in op_list:
                    continue
                min_cycles    = f'{format_number_millions(libs[lib][pset][op]['min_cycles']):>5}'
                ave_cycles    = f'{format_number_millions(libs[lib][pset][op]['ave_cycles']):>5}'
                max_cycles    = f'{format_number_millions(libs[lib][pset][op]['max_cycles']):>5}'
                out += r'\texttt{'+f'{lib:20}'+'} & '+str(pset)+f' & {op} & {min_cycles} & {ave_cycles} & {max_cycles} \\\\\n'

    out += r"""    \hline
    \end{tabular*}
    \vspace{2pt}
    \begin{minipage}{\textwidth}
    \footnotesize
    \raggedright
    \textsuperscript{a} Match long term average for \texttt{sign}.
    \textsuperscript{b} Probability of occurrence is $2^{-36}$ for \texttt{sign}.
    \end{minipage}
    \end{table}
    """
    return out

def gen_latex_perf_vs_msg_len_table(libs,*, lib_list=None, pset_list=None, op_list=None) -> str:
    out = r"""
    \begin{table}[H]
    \centering
    \setlength{\belowcaptionskip}{2pt}
    \caption{Performance vs message length, zero-length context (in million cycles).}
    \label{tab:mldsa-perf}
    \footnotesize
    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}|l|r|r|r|r|r|}
    \hline
    \textbf{Implementation} &
    \textbf{Level} &
    \textbf{Operation} &
    \textbf{Minimum} &
    \textbf{Average\textsuperscript{a,c}} &
    \textbf{Worst observed\textsuperscript{b,c}} \\
    """
    for lib in sorted(libs.keys()):
        if lib_list and lib not in lib_list:
            continue

        out += '\\hline\n'
        for pset in sorted(libs[lib].keys()):
            if pset_list and pset not in pset_list:
                continue
            op = 'sign'
            min_cycles69    = libs[lib][pset][op]['min_cycles']
            min_cycles    = f'{format_number_millions(min_cycles69):>5}'
            ave_cycles69    = libs[lib][pset][op]['ave_cycles']
            ave_cycles    = f'{format_number_millions(ave_cycles69):>5}'
            max_cycles69    = libs[lib][pset][op]['max_cycles']
            max_cycles    = f'{format_number_millions(max_cycles69):>5}'
            out += r'\texttt{'+f'{lib:20}'+'} & '+str(pset)+f' & sign 69 & {min_cycles} & {ave_cycles} & {max_cycles} \\\\\n'
            for op in ['sign 10K','sign 1M']:
                if op_list and op not in op_list:
                    continue
                min_cycles    = f'{format_number_millions(libs[lib][pset][op]['min_cycles']):>5}'
                ave = ave_cycles69 - min_cycles69 + libs[lib][pset][op]['min_cycles']
                ave_cycles    = f'{format_number_millions(ave):>5}'
                max = max_cycles69 - min_cycles69 + libs[lib][pset][op]['min_cycles']
                max_cycles    = f'{format_number_millions(max):>5}'
                out += r'\texttt{'+f'{lib:20}'+'} & '+str(pset)+f' & {op} & {min_cycles} & {ave_cycles} & {max_cycles} \\\\\n'

    out += r"""    \hline
    \end{tabular*}
    \vspace{2pt}
    \begin{minipage}{\textwidth}
    \footnotesize
    \raggedright
    \textsuperscript{a} Match long term average for \texttt{sign}.
    \textsuperscript{b} Probability of occurrence is $2^{-36}$ for \texttt{sign}.
    \textsuperscript{c} Extrapolated from 69-cycle baseline.
    \end{minipage}
    \end{table}
    """
    return out

def gen_csv_footprint_table(libs,*, pset_list=None) -> str:
    out = 'Memory footprint for all benchmarked operations (in KiB).\n'
    out += 'Implementation,Level,Stack,Heap,Static RAM,Read-only\n'

    for lib in sorted(libs.keys()):
        for pset in sorted(libs[lib].keys()):
            try:
                stack = f'{format_size_kib(libs[lib][pset]['stack']):>5}'
                heap  = f'{format_size_kib(libs[lib][pset]['heap']):>5}'
                rw    = f'{format_size_kib(libs[lib][pset]['rw']):>5}'
                ro    = f'{format_size_kib(libs[lib][pset]['ro']):>5}'
                out += f'{lib:20}'+' , '+str(pset)+f' , {stack} , {heap} , {rw} , {ro} \n'
            except KeyError:
                logging.warning(f'no size data for lib {lib}, pset {pset}')
                pass

    return out

def gen_csv_perf_table_mldsa(libs,*, lib_list=None, pset_list=None, op_list=None) -> str:
    out = 'Performance for a 69-byte message and zero-length context (in million cycles).\n'
    out += 'Implementation,Level,Operation,Minimum,Average(a),Worst observed(b)\n'

    for lib in sorted(libs.keys()):
        #if lib_list and lib not in lib_list:
        #    continue

        for pset in sorted(libs[lib].keys()):
            #if pset_list and pset not in pset_list:
            #    continue
            logging.debug(f'libs[lib][pset]={libs[lib][pset]}')
            for op in ['key-exp','sign','verify']:
                if op_list and op not in op_list:
                    continue
                min_cycles    = f'{format_number_millions(libs[lib][pset][op]['min_cycles']):>5}'
                ave_cycles    = f'{format_number_millions(libs[lib][pset][op]['ave_cycles']):>5}'
                max_cycles    = f'{format_number_millions(libs[lib][pset][op]['max_cycles']):>5}'
                out += f'{lib:20}'+' , '+str(pset)+f' , {op} , {min_cycles} , {ave_cycles} , {max_cycles}\n'

    out += '(a): Match long term average for sign.\n'
    out += '(b): Probability of occurrence is 2^-36 for sign.\n'
    return out

def gen_csv_perf_table(libs,*, lib_list=None, pset_list=None, op_list=None) -> str:
    out = 'Performance in cycles.\n'
    out += 'Implementation,Parameter set,Operation,Minimum,Average(a),Worst observed(b)\n'

    for lib in sorted(libs.keys()):
        #if lib_list and lib not in lib_list:
        #    continue

        for pset in sorted(libs[lib].keys()):
            #if pset_list and pset not in pset_list:
            #    continue
            logging.debug(f'libs[lib][pset]={libs[lib][pset]}')
            for op in sorted(libs[lib][pset].keys()):
                if op in ['stack', 'heap', 'ro', 'rw']:
                    continue
                logging.debug(f'op={op}')
                if op_list and op not in op_list:
                    continue
                min_cycles    = f'{format_number(libs[lib][pset][op]['min_cycles']):>5}'
                ave_cycles    = f'{format_number(libs[lib][pset][op]['ave_cycles']):>5}'
                max_cycles    = f'{format_number(libs[lib][pset][op]['max_cycles']):>5}'
                out += f'{lib:20}'+' , '+str(pset)+f' , {op} , {min_cycles} , {ave_cycles} , {max_cycles}\n'

    return out

def run_info(data) -> dict:
    keys = data['info'][::2] #items at even index
    values = data['info'][1::2] #items at odd index
    return dict(zip(keys,values))

def run_timestamp(p, data) -> str:
    #every record carries the timestamp of its run, the file name starts with it as well
    timestamps = [r['timestamp'] for r in data['results'] if 'timestamp' in r]
    if timestamps:
        return max(timestamps)
    return os.path.basename(p)[:len('YYYYMMDD-HH-MM-SS')]

def select_latest_runs(result_files, root):
    """Keep only the most recent result file for each benchmarked configuration.

    Result files accumulate in the root directory, so the same configuration is
    usually present several times. All of them used to be reported, each one
    overwriting the previous, which made the outcome depend on the order glob()
    happens to return the files in: a stale run could silently win over the
    latest one. Only the latest run describes the current state of the target,
    so that is the one we keep.
    """
    latest = {}
    for p in result_files:
        with open(os.path.join(root,p),'rb') as f:
            data = pickle.load(f)
        info = run_info(data)
        key = (info['hw_platform'],
               info['sw_target_cpu'],
               info['algo'],
               info['impl_name'],
               info['pset'])
        ts = run_timestamp(p,data)
        if key not in latest or ts > latest[key][0]:
            latest[key] = (ts,p)
    selected = set(p for ts,p in latest.values())
    superseded = sorted(set(result_files) - selected)
    for p in superseded:
        logging.debug(f'ignoring {p}: superseded by a more recent run')
    if superseded:
        logging.info(f'using {len(selected)} result files, {len(superseded)} superseded by more recent runs')
    return sorted(selected)

def main(args_target,args_algo,format,*,
         root='.',
         args_lib=None,
         args_pset=None,
         args_op=None,
         args_hw_platform=None,
         file=None):
    
    libs = {}

    impl_to_lib_name = {
        'pqcrystals-mldsa-lowram':'pqcrystals-lowram',
        'umldsa-small':'pqshield',
        'umldsa-balanced':'pqshield',
        'pqcle':'pqshield',
        'wolfssl-small':'wolfssl',
        'wolfssl-balanced':'wolfssl',
        'wolfssl-fast':'wolfssl',
        'stm32pqc-small':'stm32pqc',
        'stm32pqc-balanced':'stm32pqc'
    }
    impl_to_goal_name = {
        'pqcrystals-mldsa-lowram':'small',
        'umldsa-small':'small',
        'umldsa-balanced':'balanced',
        'pqcle':'balanced',
        'wolfssl-small':'small',
        'wolfssl-balanced':'balanced',
        'wolfssl-fast':'fast',
        'stm32pqc-small':'small',
        'stm32pqc-balanced':'balanced'
    }
    build_target_to_lib_name = {
        'OPEN_SOURCE':'pqcrystals-lowram',
        'PQSHIELD':'pqshield',
        'WOLFSSL':'wolfssl',
        'STM32PQC':'stm32pqc'
    }
    def build_target_to_full_lib_name(lib,goal):
        return f'{build_target_to_lib_name[lib]}-{goal}'

    lib_names = []
    if args_lib:
        for lib in args_lib:
            lib_names.append(build_target_to_lib_name[lib])
    else:
        for lib in build_target_to_lib_name.keys():
            lib_names.append(build_target_to_lib_name[lib])
    logging.debug(f'lib_names: {lib_names}')

    #get perf results
    result_files = select_latest_runs(glob.glob('*.pickle',root_dir=root), root)
    hw_platforms = {}
    for p in result_files:
        with open(os.path.join(root,p),'rb') as f:
            data = pickle.load(f)
            results = data['results']
            info = run_info(data)
            target = info['sw_target_cpu']
            if target != args_target:
                continue
            hw_platform = info['hw_platform']
            if args_hw_platform and args_hw_platform != hw_platform:
                continue
            hw_platforms[hw_platform] = p
            logging.debug(info)
            algo = info['algo']
            if args_algo != algo:
                logging.debug(f'ignoring algo {algo}')
                continue
            lib = impl_to_lib_name[info['impl_name']]
            if lib not in lib_names:
                logging.debug(f'ignoring lib {lib}')
                continue
            goal = impl_to_goal_name[info['impl_name']]
            logging.debug(f"info['impl_name']={info['impl_name']}")
            full_name = f'{lib}-{goal}'
            logging.debug(f'adding perf data for {full_name}')
            pset = info['pset']

            if args_pset and pset not in args_pset:
                logging.debug(f'ignoring pset {pset}')
                continue

            if full_name not in libs:
                libs[full_name] = {}
            if pset not in libs[full_name]:
                libs[full_name][pset] = {}

            consolidated = {}
            for r in results:
                info=r['setup info']
                case_index=r.get('case_index',0)
                cycles = get_field(r['data'],'cycles')
                min_cycles = min(cycles)
                max_cycles = max(cycles)
                ave_cycles = math.ceil(sum(cycles)/len(cycles))
                stack_sizes = get_field(r['data'],'stack size')
                max_stack = max(stack_sizes)
                try:
                    heap_sizes = get_field(r['data'],'heap size')
                    max_heap = max(heap_sizes)
                except:
                    max_heap = 0
                    heap_reported = False
                key = f'{info['dut name']}-{info['args setup name']}'
                if key not in consolidated:
                    consolidated[key]={'dut':info['dut name'], 'setup':info['args setup name'], 'data':[]}
                consolidated[key]['data'].append({'min_cycles':min_cycles,'max_cycles':max_cycles,'ave_cycles':ave_cycles,'max_stack':max_stack,'max_heap':max_heap})
            ms = 0
            heap_sum = 0
            for key,value in consolidated.items():
                val = value['data']
                min_cycles = min([v['min_cycles'] for v in val])
                max_cycles = max([v['max_cycles'] for v in val])
                ave_cycles = math.ceil(sum([v['ave_cycles'] for v in val])/len(val))
                max_stack = max([v['max_stack'] for v in val])
                max_heap = max([v['max_heap'] for v in val])
                try:
                    special_case_algo = True
                    match algo:
                        case 'mldsa':
                            setup_to_report = {
                                'mldsa_gen_key':'key-exp',
                                'mldsa_sign69':'sign',
                                'mldsa_verify69':'verify',
                                'mldsa_sign10K':'sign 10K',
                                'mldsa_verify10K':'verify 10K',
                                'mldsa_sign1M':'sign 1M',
                                'mldsa_verify1M':'verify 1M',
                            }
                        case _:
                            special_case_algo=False
                    if special_case_algo:
                        operation = setup_to_report[value['setup']]
                    else:
                        operation = value['setup']
                    libs[full_name][pset][operation] = {
                                'min_cycles':min_cycles,
                                'max_cycles':max_cycles,
                                'ave_cycles':ave_cycles,
                                }
                except KeyError:
                    pass 
                ms = max(ms,max_stack)
                heap_sum += max_heap
            
            libs[full_name][pset]['stack'] = ms
            libs[full_name][pset]['heap'] = heap_sum

    if len(hw_platforms) > 1:
        logging.error(f'hw_platforms: {hw_platforms}')
        raise RuntimeError(f'More than one hw_platform found, please use --hw-platform')
    #get footprint results
    sizes = report_footprint.report_footprint(os.path.join(root,'build'))
    sizes = sizes[args_target][args_algo]
    
    #re struct results by libs
    for pset in sizes.keys():
        if args_pset and pset not in args_pset:
            continue
        for lib in sizes[pset].keys():
            if args_lib and lib not in args_lib:
                logging.debug(f'{lib} ignored')
                continue
            for goal in sizes[pset][lib].keys():
                full_name = build_target_to_full_lib_name(lib,goal)
                logging.debug(f'process {full_name} sizes')
                d = sizes[pset][lib][goal]
                try:
                    libs[full_name][pset]['ro']=d['text']
                    libs[full_name][pset]['rw']=d['ram']
                except KeyError:
                    logging.debug(libs.get(full_name))
                    logging.warning(f'discarding size info for {full_name} {pset} because dynamic sizes info does not exist')
                    pass
                #if full_name not in libs:
                #    libs[full_name] = {}
                #if pset not in libs[full_name]:
                #    libs[full_name][pset] = {}
                #libs[full_name][pset]['ro']=d['text']
                #libs[full_name][pset]['rw']=d['ram']
                

    logging.debug(libs)

    match format:
        case 'latex':
            print(gen_latex_perf_table(libs,lib_list=args_lib, pset_list=args_pset, op_list=args_op),file=file)
            print(gen_latex_perf_vs_msg_len_table(libs,lib_list=args_lib, pset_list=args_pset, op_list=args_op),file=file)
            print(gen_latex_footprint_table(libs,lib_list=args_lib, pset_list=args_pset),file=file)
        case 'csv':
            match args_algo:
                case 'mldsa':
                    print(gen_csv_perf_table_mldsa(libs, op_list=args_op),file=file)
                case _:
                    print(gen_csv_perf_table(libs, op_list=args_op),file=file)
            print(gen_csv_footprint_table(libs),file=file)






if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    formats = ('csv', 'latex')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument(
        '--root', help='Path to crypto-benchmark root', default='.', type=str
    )
    parser.add_argument(
        '--lib', help='List of libraries to report', default=None, nargs='+', type=str
    )
    parser.add_argument(
        '--pset', help='List of parameter sets to report', default=None, nargs='+', type=str
    )
    parser.add_argument(
        '--op', help='List of operations to report', default=None, nargs='+', type=str
    )
    parser.add_argument(
        '--hw-platform', help='Specify a hardware platform', type=str
    )
    parser.add_argument(
        '--file', help='Specify the output file', type=str
    )
    parser.add_argument(
        'target', help='Target platform to report', type=str
    )
    parser.add_argument(
        'algo', help='Algorithm to report', type=str
    )
    parser.add_argument(
        'format', help='Desired output format', choices=formats
    )

    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)

    file=None
    if args.file:
        file = open(args.file,'w')

    main(args.target,args.algo,args.format,
         root=args.root,
         args_lib=args.lib,
         args_pset=args.pset,
         args_op=args.op,
         args_hw_platform=args.hw_platform,
         file=file)