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

def gen_footprint_table(libs,*, lib_list=None, pset_list=None) -> str:
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

def gen_perf_table(libs,*, lib_list=None, pset_list=None, op_list=None) -> str:
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
    \textsuperscript{b} Probability of occurrence is $2^{-37}$ for \texttt{sign}.
    \end{minipage}
    \end{table}
    """
    return out

if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
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
        'target', help='target platform to report', type=str
    )
    parser.add_argument(
        'algo', help='algorithm to report', type=str
    )

    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)

    libs = {}

    impl_to_lib_name = {
        'pqcrystals-mldsa-lowram':'pqcrystals-lowram',
        'umldsa':'pqshield-balanced',
        'wolfssl-lowram':'wolfssl-lowram',
        'stm32pqc-lowram':'stm32pqc-lowram'
    }
    build_target_to_lib_name = {
        'OPEN_SOURCE':'pqcrystals-lowram',
        'PQSHIELD':'pqshield-balanced',
        'WOLFSSL':'wolfssl-lowram',
        'STM32PQC':'stm32pqc-lowram'
    }

    #get perf results
    result_files = glob.glob('*.pickle',root_dir=args.root)
    for p in result_files:
        with open(os.path.join(args.root,p),'rb') as f:
            data = pickle.load(f)
            info = data['info']
            results = data['results']
            keys = data['info'][::2] #items at even index
            values = data['info'][1::2] #items at odd index
            info = dict(zip(keys,values))

            logging.debug(info)

            lib = impl_to_lib_name[info['impl_name']]
            pset = info['mldsa_pset']

            if lib not in libs:
                libs[lib] = {}
            if pset not in libs[lib]:
                libs[lib][pset] = {}

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
                    setup_to_report = {
                        'mldsa_gen_key':'key-exp',
                        'mldsa_sign69':'sign',
                        'mldsa_verify69':'verify',
                    }
                    operation = setup_to_report[value['setup']]
                    libs[lib][pset][operation] = {
                                'min_cycles':min_cycles,
                                'max_cycles':max_cycles,
                                'ave_cycles':ave_cycles,
                                
                                }
                except KeyError:
                    pass 
                ms = max(ms,max_stack)
                heap_sum += max_heap
            libs[lib][pset]['stack'] = ms
            libs[lib][pset]['heap'] = heap_sum

    #get footprint results
    sizes = report_footprint.report_footprint(os.path.join(args.root,'build'))
    sizes = sizes[args.target][args.algo]
    
    #re struct results by libs
    for pset in sizes.keys():
        for lib in sizes[pset].keys():
            d = sizes[pset][lib]
            libs[build_target_to_lib_name[lib]][pset]['ro']=d['text']
            libs[build_target_to_lib_name[lib]][pset]['rw']=d['ram']


    logging.debug(libs)
    print(gen_perf_table(libs,lib_list=args.lib, pset_list=args.pset, op_list=args.op))
    print(gen_footprint_table(libs,lib_list=args.lib, pset_list=args.pset))