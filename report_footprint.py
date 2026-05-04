import os
import sys
import re
import logging
import argparse

import humanfriendly

def report_footprint(build_dir):
    size_report_str = r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+).*crypto-benchmark-(\w+)-(\w+)-(\w+)-(\w+).elf"
    size_report_pattern = re.compile(size_report_str)

    targets = [ f.path for f in os.scandir(build_dir) if f.is_dir() ]
    out = {}
    for target_path in targets:
        target = os.path.basename(target_path)
        sizes_path = os.path.join(target_path,'sizes.txt')
        logging.debug(f'sizes_path: {sizes_path}')
        if os.path.exists(sizes_path):
            sizes_str = open(sizes_path).read()
            logging.debug(sizes_str)
            size_matches = re.findall(size_report_pattern,sizes_str)
            sizes = {}
            for m in size_matches:
                d = {}
                d['text'] = int(m[0])
                d['data'] = int(m[1])
                d['bss'] = int(m[2])
                d['lib'] = m[5]
                d['goal'] = m[6]
                d['algo'] = m[7]
                d['pset'] = m[8]
                logging.debug(d)
                if d['algo'] not in sizes.keys():
                    sizes[d['algo']] = {}
                if d['pset'] not in sizes[d['algo']].keys():
                    sizes[d['algo']][d['pset']] = {}
                if d['lib'] not in sizes[d['algo']][d['pset']].keys():
                    sizes[d['algo']][d['pset']][d['lib']] = {}
                if d['goal'] not in sizes[d['algo']][d['pset']][d['lib']].keys():
                    sizes[d['algo']][d['pset']][d['lib']][d['goal']] = {}
                sizes[d['algo']][d['pset']][d['lib']][d['goal']] = d
            logging.debug(f'sizes={sizes}')
            stub={}
            for algo in sizes.keys():
                stub[algo]={}
                for pset in sizes[algo].keys():
                    stub[algo][pset]={}
                    for goal in sizes[algo][pset]['STUB']:
                        stub_size = sizes[algo][pset]['STUB'][goal]
                        stub_text_size = stub_size['text']
                        stub_ram_size = stub_size['data']+stub_size['bss']
                        stub[algo][pset][goal] = {'size':stub_size,'text_size':stub_text_size,'ram_size':stub_ram_size}
            out[target]={}
            for algo in sizes.keys():
                out[target][algo]={}
                for pset in sizes[algo].keys():
                    out[target][algo][pset]={}
                    for lib in sizes[algo][pset]:
                        if lib == 'STUB':
                            continue
                        out[target][algo][pset][lib]={}
                        for goal in sizes[algo][pset][lib]:
                            stub_size = stub[algo][pset][goal]['size']
                            stub_text_size = stub[algo][pset][goal]['text_size']
                            stub_ram_size = stub[algo][pset][goal]['ram_size']
                            lib_size = sizes[algo][pset][lib][goal]
                            d = {}
                            d['text'] = lib_size['text'] - stub_text_size 
                            ram_size = lib_size['data'] + lib_size['bss'] - stub_ram_size 
                            if ram_size < 0:
                                logging.warning(f'{algo} {pset} {lib} {goal} ram size is {ram_size}, correcting to 0')
                                ram_size = 0
                            d['ram'] = ram_size
                            out[target][algo][pset][lib][goal]=d
    return out

if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    
    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)
    
    out = report_footprint('build')
    for target in out.keys():
        for algo in out[target].keys():
            for pset in out[target][algo].keys():
                for lib in out[target][algo][pset].keys():
                    for goal in out[target][algo][pset][lib].keys():
                        d = out[target][algo][pset][lib][goal]
                        print(f"{target} {algo} {pset} {lib:20} {goal:8}: ro = {humanfriendly.format_size(d['text'],binary=True):>12}, rw = {humanfriendly.format_size(d['ram'],binary=True):>12}")





