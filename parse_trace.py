import datetime
import serial 
import sys,os,argparse
from pysatl import Utils
import logging
import io
import pickle
import math
import humanfriendly
import glob
import runpy


def isolate_function(trace_file: str, function_addr:str):
    with open(trace_file) as f:
        calling_addr = None
        last_line = None
        for line in f:
            addr = int(last_line.split[' '][0],16)
            if calling_addr:
                if addr > calling_addr and addr - calling_addr <= 8:
                    calling_addr = None
            else:
                calling_addr = addr
                
            last_line = line

if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument(
        'trace_file', help='Trace file to read', type=str
    )
    parser.add_argument(
        '--func', help='Function to isolate', type=str
    )
    
    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)
    
    if args.func:
        isolate_function(args.trace_file,function)
        exit(0)
    print('nothing to do.')