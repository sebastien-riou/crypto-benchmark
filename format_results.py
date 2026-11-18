import logging
import argparse
import os
import re
import sys
import report_footprint
import humanfriendly
import glob
import pickle
import math
import ast
import functools
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
    \textbf{Flash} \\
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
            flash = f'{format_size_kib(libs[lib][pset]['flash']):>5}'
            out += r'\texttt{'+f'{lib:20}'+'} & '+str(pset)+f' & {stack} & {heap} & {rw} & {flash} \\\\\n'
    
    out += r"""    \hline
    \end{tabular*}
    \end{table}
    """

    return out

# operations of the ML-DSA tables; the prepared-key ones are reported only by libraries that have them
MLDSA_TABLE_OPS = ['key-exp','sign','verify','sk-prepare','sign-prepared','pk-prepare','verify-prepared']

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
            for op in MLDSA_TABLE_OPS:
                if op_list and op not in op_list:
                    continue
                if op not in libs[lib][pset]:
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
    out += 'Implementation,Level,Stack,Heap,Static RAM,Flash\n'

    for lib in sorted(libs.keys()):
        for pset in sorted(libs[lib].keys()):
            try:
                stack = f'{format_size_kib(libs[lib][pset]['stack']):>5}'
                heap  = f'{format_size_kib(libs[lib][pset]['heap']):>5}'
                rw    = f'{format_size_kib(libs[lib][pset]['rw']):>5}'
                flash = f'{format_size_kib(libs[lib][pset]['flash']):>5}'
                out += f'{lib:20}'+' , '+str(pset)+f' , {stack} , {heap} , {rw} , {flash} \n'
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
            for op in MLDSA_TABLE_OPS:
                if op_list and op not in op_list:
                    continue
                if op not in libs[lib][pset]:
                    continue
                min_cycles    = f'{format_number_millions(libs[lib][pset][op]['min_cycles']):>5}'
                ave_cycles    = f'{format_number_millions(libs[lib][pset][op]['ave_cycles']):>5}'
                max_cycles    = f'{format_number_millions(libs[lib][pset][op]['max_cycles']):>5}'
                out += f'{lib:20}'+' , '+str(pset)+f' , {op} , {min_cycles} , {ave_cycles} , {max_cycles}\n'

    out += '(a): Match long term average for sign.\n'
    out += '(b): Probability of occurrence is 2^-36 for sign.\n'
    return out

def gen_csv_perf_table_mlkem(libs,*, lib_list=None, pset_list=None, op_list=None, tv_names=None) -> str:
    # the test vectors of the reported runs: all from BTVG-MLKEM, or all without record (see main)
    names = sorted(set((tv_names or {}).values()), key=lambda name: int(name.split('-')[0][len('mlkem'):]))
    records = [mlkem_tv_record(name) for name in names]
    btvg = len(records) > 0 and all(records)
    if btvg:
        out = 'Performance on the test vectors of BTVG-MLKEM (in million cycles).\n'
        out += 'Implementation,Level,Operation,Best case(a),Average(b),Worst case(c)\n'
    else:
        out = 'Performance over all test cases (in million cycles).\n'
        out += 'Implementation,Level,Operation,Minimum,Average,Worst observed(a)\n'

    for lib in sorted(libs.keys()):
        for pset in sorted(libs[lib].keys(), key=int):
            logging.debug(f'libs[lib][pset]={libs[lib][pset]}')
            for op in ['key-exp','encaps','decaps','decaps-reject']:
                if op_list and op not in op_list:
                    continue
                min_cycles    = f'{format_number_millions(libs[lib][pset][op]['min_cycles'],precision=3):>5}'
                ave_cycles    = f'{format_number_millions(libs[lib][pset][op]['ave_cycles'],precision=3):>5}'
                max_cycles    = f'{format_number_millions(libs[lib][pset][op]['max_cycles'],precision=3):>5}'
                out += f'{lib:20}'+' , '+str(pset)+f' , {op} , {min_cycles} , {ave_cycles} , {max_cycles}\n'

    # no comma in the notes: they are lines of the CSV file
    # short lines: column -t (show-all-results) pads the first column to the longest one
    if btvg:
        out += '(a): Minimum on the best case: no extra SHAKE128 block for the matrix A and few SampleNTT iterations.\n'
        out += '(b): Mean over the average set: keys with the long term average cost of the matrix A.\n'
        out += '(c): Maximum on the worst cases: the most extra SHAKE128 blocks for the matrix A.\n'
        out += 'Test vectors of BTVG-MLKEM (https://github.com/sebastien-riou/BTVG-MLKEM):\n'
        for record in records:
            cases = [f'ML-KEM-{record["pset"]}: {record["name"]}']
            for c in record['cases']:
                if c['role'] == 'best':
                    cases.append(f'best case probability {c["probability"]}')
                elif c['role'] == 'worst':
                    cases.append(f'worst case {c["e"]} extra blocks (tier {c["tier"]} probability {c["probability"]})')
            out += '; '.join(cases) + '.\n'
    else:
        out += '(a): The test cases include keys whose matrix A generation needs a 4th SHAKE128 block for some polynomials.\n'
        if names:
            out += f'Test vectors: {"; ".join(names)}.\n'
            out += 'Sanity check sets (build option SANITY_TV=1) or runs made before BTVG-MLKEM.\n'
    out += 'decaps-reject: decapsulation of an invalid ciphertext (implicit rejection).\n'
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
                if op in ['stack', 'heap', 'flash', 'rw']:
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

# ML-KEM test vectors: a set of BTVG-MLKEM comes with its record, libmlkem-lbmk/include/<name>.py, which gives the
# role of each test case. The sets of the sanity check build (SANITY_TV=1, libmlkem-lbmk/gen-tv.py), which the
# benchmark used before BTVG-MLKEM, have none.
MLKEM_TV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libmlkem-lbmk', 'include')

@functools.cache
def mlkem_tv_record(tv_name):
    """The record of the BTVG-MLKEM set tv_name, as a dict of its variables; None for a set without record."""
    match = re.fullmatch(r'mlkem\d+-n(\d+)-h[0-9A-F]+', tv_name)
    if not match:
        return None
    path = os.path.join(MLKEM_TV_DIR, f'{tv_name}.py')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        tree = ast.parse(f.read(), path)
    # Python literals only (BTVG-MLKEM SPEC.md section 7)
    record = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    if record.get('name') != tv_name or len(record.get('cases', [])) != int(match.group(1)):
        raise RuntimeError(f'{path} is not the record of {tv_name}')
    return record

def mlkem_sanity_run(info) -> bool:
    """True for an ML-KEM run on a set without record: a sanity check build, or a run made before BTVG-MLKEM."""
    return info['algo'] == 'mlkem' and mlkem_tv_record(info.get('tv_name', '')) is None

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
    An ML-KEM run on the sanity check test vectors is kept apart: it does not
    supersede a run on those of BTVG-MLKEM, nor the reverse (main reports one
    kind or the other).
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
               info['pset'],
               mlkem_sanity_run(info))
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
         args_sanity_tv=False,
         file=None):
    
    libs = {}
    # ML-KEM: name of the test vectors of each reported (implementation, parameter set)
    tv_names = {}

    impl_to_lib_name = {
        'pqcrystals-mldsa-lowram':'pqcrystals-lowram',
        'umldsa-small':'pqshield',
        'umldsa-balanced':'pqshield',
        'umldsa-fast':'pqshield',
        'umlkem-balanced':'pqshield',
        'umlkem-fast':'pqshield',
        'pqcle':'pqshield',
        'wolfssl-small':'wolfssl',
        'wolfssl-balanced':'wolfssl',
        'wolfssl-fast':'wolfssl',
        # results of the former goals small-armasm and fast-armasm: existing result files still use these names (the
        # goals small and fast now use wolfSSL's Thumb-2 assembly on cortex-m*)
        'wolfssl-small-armasm':'wolfssl',
        'wolfssl-fast-armasm':'wolfssl',
        'stm32pqc-small':'stm32pqc',
        'stm32pqc-balanced':'stm32pqc',
        'stm32pqc-fast':'stm32pqc',
        'pqrv':'pqrv'
    }
    impl_to_goal_name = {
        'pqcrystals-mldsa-lowram':'small',
        'umldsa-small':'small',
        'umldsa-balanced':'balanced',
        'umldsa-fast':'fast',
        'umlkem-balanced':'balanced',
        'umlkem-fast':'fast',
        'pqcle':'balanced',
        'wolfssl-small':'small',
        'wolfssl-balanced':'balanced',
        'wolfssl-fast':'fast',
        # results of the former goals small-armasm and fast-armasm (see impl_to_lib_name)
        'wolfssl-small-armasm':'small-armasm',
        'wolfssl-fast-armasm':'fast-armasm',
        'stm32pqc-small':'small',
        'stm32pqc-balanced':'balanced',
        'stm32pqc-fast':'fast',
        'pqrv':'fast'
    }
    build_target_to_lib_name = {
        'OPEN_SOURCE':'pqcrystals-lowram',
        'PQSHIELD':'pqshield',
        'WOLFSSL':'wolfssl',
        'STM32PQC':'stm32pqc',
        'PQRV':'pqrv'
    }
    # External libraries are not in the tables above: their library name is the build target name
    # in lower case, and their implementation name is '<library name>-<goal>'
    def lib_name(build_target):
        return build_target_to_lib_name.get(build_target, build_target.lower())
    def impl_to_lib_and_goal_name(impl_name):
        if impl_name in impl_to_lib_name:
            return impl_to_lib_name[impl_name], impl_to_goal_name[impl_name]
        # the goal is small, balanced, fast or one of the external library's own goals
        lib, _, goal = impl_name.rpartition('-')
        if lib and re.fullmatch(r'\w+', goal):
            return lib, goal
        raise RuntimeError(f'unknown implementation name "{impl_name}", the implementation name of an external library must be "<library name>-<goal>"')
    def build_target_to_full_lib_name(lib,goal):
        return f'{lib_name(lib)}-{goal}'

    lib_names = []
    if args_lib:
        for lib in args_lib:
            lib_names.append(lib_name(lib))
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
            lib,goal = impl_to_lib_and_goal_name(info['impl_name'])
            if lib not in lib_names:
                logging.debug(f'ignoring lib {lib}')
                continue
            logging.debug(f"info['impl_name']={info['impl_name']}")
            full_name = f'{lib}-{goal}'
            logging.debug(f'adding perf data for {full_name}')
            pset = info['pset']

            if args_pset and pset not in args_pset:
                logging.debug(f'ignoring pset {pset}')
                continue

            # ML-KEM: the runs on the test vectors of BTVG-MLKEM, or with args_sanity_tv the others (see mlkem_tv_record)
            tv_record = None
            if algo == 'mlkem':
                if mlkem_sanity_run(info) != args_sanity_tv:
                    logging.debug(f'ignoring {p}: ML-KEM test vectors {info.get("tv_name")}, sanity check set: {not args_sanity_tv}')
                    continue
                tv_record = mlkem_tv_record(info['tv_name'])
                tv_names[(full_name,pset)] = info['tv_name']

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
                role = None
                if tv_record:
                    if case_index >= len(tv_record['cases']):
                        raise RuntimeError(f'{p}: test case {case_index} is not in {tv_record["name"]}')
                    role = tv_record['cases'][case_index]['role']
                consolidated[key]['data'].append({'min_cycles':min_cycles,'max_cycles':max_cycles,'ave_cycles':ave_cycles,'max_stack':max_stack,'max_heap':max_heap,'role':role})
            ms = 0
            heap_sum = 0
            for key,value in consolidated.items():
                val = value['data']
                if tv_record:
                    # BTVG-MLKEM: minimum on the best case, mean over the average set, maximum on the worst cases
                    by_role = {role:[v for v in val if v['role'] == role] for role in ('best','average','worst')}
                    for role,v in by_role.items():
                        if not v:
                            raise RuntimeError(f'{p}: {key} has no result for the {role} case(s) of {tv_record["name"]}')
                    min_cycles = min([v['min_cycles'] for v in by_role['best']])
                    max_cycles = max([v['max_cycles'] for v in by_role['worst']])
                    ave_cycles = math.ceil(sum([v['ave_cycles'] for v in by_role['average']])/len(by_role['average']))
                else:
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
                                # libraries with prepared keys only (DSA_PREPARED_KEYS)
                                'mldsa_sk_prepare':'sk-prepare',
                                'mldsa_pk_prepare':'pk-prepare',
                                'mldsa_sign_prepared69':'sign-prepared',
                                'mldsa_verify_prepared69':'verify-prepared',
                                'mldsa_sign_prepared10K':'sign-prepared 10K',
                                'mldsa_verify_prepared10K':'verify-prepared 10K',
                                'mldsa_sign_prepared1M':'sign-prepared 1M',
                                'mldsa_verify_prepared1M':'verify-prepared 1M',
                            }
                        case 'mlkem':
                            setup_to_report = {
                                'mlkem_keygen':'key-exp',
                                'mlkem_encaps':'encaps',
                                'mlkem_decaps':'decaps',
                                'mlkem_decaps_reject':'decaps-reject',
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
                    libs[full_name][pset]['flash']=d['flash']
                    libs[full_name][pset]['rw']=d['ram']
                except KeyError:
                    logging.debug(libs.get(full_name))
                    logging.warning(f'discarding size info for {full_name} {pset} because dynamic sizes info does not exist')
                    pass
                #if full_name not in libs:
                #    libs[full_name] = {}
                #if pset not in libs[full_name]:
                #    libs[full_name][pset] = {}
                #libs[full_name][pset]['flash']=d['flash']
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
                case 'mlkem':
                    print(gen_csv_perf_table_mlkem(libs, op_list=args_op, tv_names=tv_names),file=file)
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
        '--sanity-tv', action='store_true',
        help='ML-KEM: report the runs on the sanity check test vectors (SANITY_TV=1 builds, and runs made before '
             'BTVG-MLKEM) instead of those on the test vectors of BTVG-MLKEM'
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
         args_sanity_tv=args.sanity_tv,
         file=file)