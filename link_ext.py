#!bin/python3

import os
import sys
from glob import glob 
import logging
import argparse

def main(*,preset='minSizeRel', goal=None):
    targets = ['cortex-m3','cortex-m4','cortex-m7','cortex-m33','cortex-m55','rv32i','rv32imc','rv32imcb','rv64imc','linux']
    libs = ['pqcle','pqcrystals-mldsa-lowram','libtomcrypt','lean-benchmark','wolfssl']

    PQCLE_SRC='../../../aikido/'
    PQCLE='target/ext/pqcle'

    LOWRAM_SRC='../../../dilithium-lowram/libpqcrystals-mldsa-lowram'
    LOWRAM='target/ext/libpqcrystals-mldsa-lowram'

    TOMCRYPT_SRC='../../../libtomcrypt'
    TOMCRYPT='target/ext/libtomcrypt'

    LBMK_SRC=f'../../../lean-benchmark/dist/liblean-benchmark-{preset}/'
    LBMK='target/ext/liblean-benchmark'

    WOLFSSL_SRC='../../../wolfssl'
    WOLFSSL='target/ext/wolfssl'

    debug=''
    if preset == 'debug':
        debug='-debug'
    if goal is None:
        goal='small'
    goal_file = 'goal.txt'
    with open(goal_file,'w') as f:
        print(goal,file=f)
    goal='-'+goal
        
    for p in [PQCLE,LOWRAM,TOMCRYPT,LBMK,WOLFSSL]:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    os.makedirs('target/ext',exist_ok=True)
    os.symlink(PQCLE_SRC,PQCLE,target_is_directory=True)
    os.symlink(LOWRAM_SRC,LOWRAM,target_is_directory=True)
    os.symlink(TOMCRYPT_SRC,TOMCRYPT,target_is_directory=True)
    os.symlink(LBMK_SRC,LBMK,target_is_directory=True)
    os.symlink(WOLFSSL_SRC,WOLFSSL,target_is_directory=True)

    def link(libname,targetname,source,pattern):
        dst_dir = os.path.join('target',targetname,libname)
        logging.debug(f'dst={dst_dir}')
        for f in glob(f'{dst_dir}/{pattern}'):
            os.remove(f)
        if not os.path.exists(source):
            logging.warning(f'No file found for {targetname}/{libname} in {source}')
            return
        files = glob(f'{source}/{pattern}')
        if 0==len(files):
            logging.warning(f'No file found for {targetname}/{libname} in {source}/{pattern}')
        for f in files:
            src = os.path.join('..','..','..',f)
            dst = os.path.join(dst_dir,os.path.basename(f))
            logging.debug(f'src={src}, dst={dst}')
            os.makedirs(dst_dir,exist_ok=True)
            os.symlink(src,dst)
        
        # link any subdirectory as well
        subdirs = [ f.path for f in os.scandir(source) if f.is_dir() ]
        for subdir in subdirs:
            name = os.path.basename(subdir)
            logging.debug(f'name={name}')
            subdir_dst = f'{dst_dir}/{name}'
            logging.debug(f'subdir={subdir}, subdir_dst={subdir_dst}')
            try:
                os.remove(subdir_dst)
            except:
                pass
            subdir_src = os.path.join('..','..','..',subdir)
            os.symlink(subdir_src,subdir_dst,target_is_directory=True)

    for libname in libs:
        for targetname in targets:
            match(libname):
                case 'pqcle':
                    if targetname == 'linux':
                        targetdir = 'gcc-x86_64-linux-gnu'
                    else:
                        targetdir = f'gcc-{targetname}{goal}{debug}'
                    source = f'{PQCLE}/out/build/{targetdir}'
                    source_lib = f'{PQCLE}/out/{targetdir}/lib'
                    source_h = source+'/inc/pqcle'
                case 'pqcrystals-mldsa-lowram':
                    source_lib = f'{LOWRAM}/build/{targetname}/lib{libname}'
                    source_h = f'{LOWRAM}/include'
                case 'libtomcrypt':
                    source_lib = TOMCRYPT + f'/build/{targetname}'
                    source_h = TOMCRYPT + '/src/headers'
                case 'lean-benchmark':
                    source_lib = LBMK + f'/build/{targetname}/lib{libname}'
                    source_h = LBMK + '/include'
                case 'wolfssl':
                    if goal == '-balanced':
                        logging.warning('No support for a "balanced" wolfssl yet, using "fast"')
                        goal='-fast'
                    source_lib = WOLFSSL + f'/build/{targetname}{goal}/lib'
                    source_h = WOLFSSL + f'/build/{targetname}{goal}/include/wolfssl'

            link(libname,targetname,source_lib,'*.a')
            link(libname,targetname,source_h,'*.h')

if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument('--preset', default='minSizeRel', type=str)
    goals = ('small','balanced','fast')
    parser.add_argument('--goal', default='small', choices=goals)
    
    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)
    main(preset=args.preset,goal=args.goal)