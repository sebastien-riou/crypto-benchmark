#!bin/python3

import os
import shutil
import sys
from glob import glob
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import goals


def main(*,preset='minSizeRel', goal=None):
    """Create the symbolic links to the libraries built in the other repositories.

    Libraries with one build per target are linked in target/<cpu>/<library>/.
    Libraries with one build per goal (the manifests with link_dirs(), see crypto-libraries/) are linked for
    every goal at once, in target/<cpu>/goals/<algo>/<goal>/<library>/: CMake takes the folder of its GOAL, so
    a build does not depend on a previous run of this script for the right goal. Their builds with options
    (manifests with custom_ids()) are linked the same way, in .../<algo>/custom_<hash>/<library>/.

    goal: optional, recorded in goal.txt as the goal of a ./buildit run without GOAL=<goal>."""
    targets = ['cortex-m3','cortex-m4','cortex-m7','cortex-m33','cortex-m52','cortex-m55','rv32i','rv32imc','rv32imcb','rv64imc','linux']
    libs = ['pqcrystals-mldsa-lowram','libtomcrypt','lean-benchmark','pqrv'] #,'fpfp']

    PQCLE_SRC='../../../pqmicrolib-library/'
    PQCLE='target/ext/pqcle'

    LOWRAM_SRC='../../../dilithium-lowram/libpqcrystals-mldsa-lowram'
    LOWRAM='target/ext/libpqcrystals-mldsa-lowram'

    TOMCRYPT_SRC='../../../libtomcrypt'
    TOMCRYPT='target/ext/libtomcrypt'

    LBMK_SRC=f'../../../lean-benchmark/dist/liblean-benchmark-{preset}/'
    LBMK='target/ext/liblean-benchmark'

    WOLFSSL_SRC='../../../wolfssl'
    WOLFSSL='target/ext/wolfssl'

    PQRV_SRC='../../../PQRV/libpqrv'
    PQRV='target/ext/libpqrv'

    FPFP_SRC='../../../fixed-point-fndsa-portable'
    FPFP='target/ext/fpfp'

    # libraries with one build per goal: link name (see the manifests) -> root of the library in target/ext
    per_goal_roots = {'pqcle': PQCLE, 'wolfssl': WOLFSSL}

    if goal is not None:
        goals.check_goal(goal)
        with open('goal.txt','w') as f:
            print(goal,file=f)

    for p in [PQCLE,LOWRAM,TOMCRYPT,LBMK,WOLFSSL,PQRV]:#,FPFP]:
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
    os.symlink(PQRV_SRC,PQRV,target_is_directory=True)
    #os.symlink(FPFP_SRC,FPFP,target_is_directory=True)

    def link(dst_dir,source,pattern):
        """Link the files of 'source' matching 'pattern', and its subdirectories, in 'dst_dir'."""
        logging.debug(f'dst={dst_dir}')
        for f in glob(f'{dst_dir}/{pattern}'):
            os.remove(f)
        if not os.path.exists(source):
            # not an error: no build of this library for this target (and goal), CMake says so if it needs one
            logging.debug(f'No file found for {dst_dir} in {source}')
            return
        files = glob(f'{source}/{pattern}')
        if 0==len(files):
            logging.debug(f'No file found for {dst_dir} in {source}/{pattern}')
        # a path relative to dst_dir: the links keep working when the repositories are moved together
        up = os.path.relpath('.', dst_dir)
        for f in files:
            src = os.path.join(up,f)
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
            os.makedirs(dst_dir,exist_ok=True)
            os.symlink(os.path.join(up,subdir),subdir_dst,target_is_directory=True)

    for libname in libs:
        for targetname in targets:
            match(libname):
                case 'pqcrystals-mldsa-lowram':
                    source_lib = f'{LOWRAM}/build/{targetname}/lib{libname}'
                    source_h = f'{LOWRAM}/include'
                case 'libtomcrypt':
                    source_lib = TOMCRYPT + f'/build/{targetname}'
                    source_h = TOMCRYPT + '/src/headers'
                case 'lean-benchmark':
                    source_lib = LBMK + f'/build/{targetname}/lib{libname}'
                    source_h = LBMK + '/include'
                case 'pqrv':
                    source_lib = f'{PQRV}/build/{targetname}/lib'
                    source_h = f'{PQRV}/include'
                case 'fpfp':
                    source_lib = f'{FPFP}/build/{targetname}/lib{libname}'
                    source_h = f'{FPFP}/include'
                case _:
                    raise RuntimeError(f'missing case for "{libname}"')

            dst_dir = os.path.join('target',targetname,libname)
            link(dst_dir,source_lib,'*.a')
            link(dst_dir,source_h,'*.h')

    # the libraries with one build per goal, every goal of every algorithm
    per_goal = [h for h in map(goals.load, sorted(glob(os.path.join('crypto-libraries','*.py')))) if hasattr(h,'link_dirs')]
    for targetname in targets:
        # start from scratch: no link to a build that no longer exists, nor to a goal that no longer does
        shutil.rmtree(os.path.join('target',targetname,'goals'),ignore_errors=True)
        for helper in per_goal:
            root = per_goal_roots[helper.link_name]
            # the folders these libraries were linked in before the per-goal ones: whatever they still hold
            # belongs to the goal of the last run of an older link_ext.py
            old_dir = os.path.join('target',targetname,helper.link_name)
            if os.path.isdir(old_dir) and not os.path.islink(old_dir):
                for f in os.scandir(old_dir):
                    if f.is_symlink():
                        os.remove(f.path)
                if not os.listdir(old_dir):
                    os.rmdir(old_dir)
            for algo in helper.algorithms():
                # every goal, and the builds with options (benchmark.py --opt) the library's repository holds
                custom_ids = getattr(helper,'custom_ids',lambda root,targetname,algo: [])
                for lib_goal in goals.goals_of(helper,algo) + custom_ids(root,targetname,algo):
                    source_lib,source_h = helper.link_dirs(targetname,lib_goal,algo)
                    dst_dir = os.path.join('target',targetname,'goals',algo,lib_goal,helper.link_name)
                    link(dst_dir,f'{root}/{source_lib}','*.a')
                    link(dst_dir,f'{root}/{source_h}','*.h')

if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument('--preset', default='minSizeRel', type=str)
    parser.add_argument('--goal', default=None, choices=list(goals.STANDARD_GOALS),
                        help='goal of a ./buildit run without GOAL=<goal> (recorded in goal.txt); '
                             'the libraries are linked for every goal in all cases')

    args = parser.parse_args()

    logformat = '%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s'
    logdatefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level=args.log_level, format=logformat, datefmt=logdatefmt)
    main(preset=args.preset,goal=args.goal)
