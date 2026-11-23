#!/usr/bin/env python3
"""Optimization goals, options and library manifests: the one place that knows their names.

Used by benchmark.py, link_ext.py and format_results.py, and by the shell scripts through its command line:
    python3 goals.py default <CRYPTO_LIB> <algo>   the goal a script uses when none is given
    python3 goals.py rev <CRYPTO_LIB>              the library's revision, as the firmware reports it
    python3 goals.py check <CRYPTO_LIB> <algo> <goal> [<k=v,k=v>]
                                                   fails unless the library has this goal and these options
    python3 goals.py list                          the goals of every library
"""

import glob
import hashlib
import os
import re
import runpy
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LIBRARIES_DIR = os.path.join(ROOT, 'crypto-libraries')
EXTERNAL_LIBS_DIR = os.path.join(ROOT, 'external-libs_git_ignore')

# The standard goals: the same meaning for every library and algorithm (README.md, "Optimization goals").
# The integration of a library chooses the configuration that serves each goal best on each target, and lists
# only the goals it has a configuration for.
STANDARD_GOALS = {
    'smallram':  'least RAM (static, stack and heap), then least flash; speed last',
    'smallcode': 'least flash (code, constants, initial values of data), then least RAM; speed last',
    'balanced':  'no dominant constraint: what one would ship by default on a typical MCU',
    'fast':      'fewest cycles; RAM and flash unconstrained',
}

# A build made with options (benchmark.py --opt) is not a standard goal: it is reported as 'custom'
CUSTOM = 'custom'
CUSTOM_PREFIX = CUSTOM + '_'

# Width of the library revision in the firmware: fixed, so that a new revision does not move the code
LIB_REV_WIDTH = 16

_OPT_KEY = r'[a-z][a-z0-9_]*'
# no space, comma or quote: the options travel as one K=V argument, through the shell, CMake and the C compiler
_OPT_VALUE = r'[A-Za-z0-9_.+=:/@-]*'


class GoalError(ValueError):
    pass


def check_goal(goal):
    """A goal is one of the standard goals: anything else is an option of a library (see parse_opts)."""
    if goal not in STANDARD_GOALS:
        raise GoalError(f'unknown goal "{goal}", the goals are: {", ".join(STANDARD_GOALS)}')
    return goal


def goals_of(helper, algo):
    """The goals of a library (its manifest's helper) for an algorithm, [] when it does not implement it."""
    goals = helper.algorithms().get(algo)
    if goals is None:
        return []
    for goal in goals:
        try:
            check_goal(goal)
        except GoalError as e:
            raise GoalError(f'{helper.codename}, {algo}: {e}. A variant of a library is an option (--opt), '
                            f'not a goal') from None
    return list(goals)


def default_goal(helper, algo):
    """The goal used when none is given: balanced where the library has it, otherwise the first it lists."""
    goals = goals_of(helper, algo)
    if not goals:
        raise GoalError(f'{helper.codename} has no goal for algorithm "{algo}"')
    return 'balanced' if 'balanced' in goals else goals[0]


def parse_opts(items):
    """['k=v', ...] (or one 'k=v,k=v' string) -> dict, in the order of opts_string()."""
    if isinstance(items, str):
        items = [i for i in items.split(',') if i]
    opts = {}
    for item in items or []:
        key, sep, value = item.partition('=')
        if not sep or not re.fullmatch(_OPT_KEY, key) or not re.fullmatch(_OPT_VALUE, value):
            raise GoalError(f'invalid option "{item}": expected <key>=<value>, key in lower case, value without '
                            f'space, comma or quote')
        if key in opts:
            raise GoalError(f'option "{key}" given twice')
        opts[key] = value
    return dict(item.split('=', 1) for item in _sorted_items(opts))


def _sorted_items(opts):
    # sorted as strings, 'k=v' as a whole: the order CMakeLists.txt puts GOAL_OPTS in (list(SORT))
    return sorted(f'{k}={v}' for k, v in (opts or {}).items())


def opts_string(opts):
    """The options as they travel to the build and back in the results: 'k=v,k=v', in one order whatever
    the order they were given in."""
    return ','.join(_sorted_items(opts))


def goal_id(goal, opts=None):
    """What identifies a build next to its library: the goal, or custom_<hash> for a goal built with options.

    Word characters only: it is part of the ELF file names that report_footprint.py parses. CMakeLists.txt
    computes the same value (GOAL_ID)."""
    opts = opts_string(opts if isinstance(opts, dict) else parse_opts(opts or ''))
    if not opts:
        return goal
    return CUSTOM_PREFIX + hashlib.sha256(f'{goal} {opts}'.encode()).hexdigest()[:8]


def is_custom(goal_id_):
    return goal_id_.startswith(CUSTOM_PREFIX)


def check_opts(helper, algo, opts):
    """Options must be declared by the library's manifest: options(algo) -> {key: description}."""
    if not opts:
        return
    declared = getattr(helper, 'options', lambda algo: {})(algo) or {}
    unknown = [k for k in opts if k not in declared]
    if unknown:
        known = ', '.join(sorted(declared)) if declared else 'none'
        raise GoalError(f'{helper.codename}, {algo}: unknown option(s) {", ".join(unknown)} (it has: {known})')


def manifests():
    """Paths of the manifests of every library: the supported ones, then the external ones."""
    paths = sorted(glob.glob(os.path.join(LIBRARIES_DIR, '*.py')))
    for d in sorted(glob.glob(os.path.join(EXTERNAL_LIBS_DIR, '*', ''))):
        name = os.path.basename(os.path.dirname(d))
        p = os.path.join(d, f'{name}.py')
        if os.path.exists(p):
            paths.append(p)
    return paths


def load(path):
    return runpy.run_path(path)['helper']


def find_library(codename):
    """The helper of the library with this CRYPTO_LIB value (e.g. WOLFSSL), None when there is none (STUB)."""
    # an external library's manifest is external-libs_git_ignore/<codename in lower case>/: no need to load them all
    name = codename.lower()
    p = os.path.join(EXTERNAL_LIBS_DIR, name, f'{name}.py')
    if os.path.exists(p):
        return load(p)
    for p in sorted(glob.glob(os.path.join(LIBRARIES_DIR, '*.py'))):
        helper = load(p)
        if helper.codename == codename:
            return helper
    return None


def _git(path, *args):
    res = subprocess.run(['git', '-C', path, *args], capture_output=True, text=True, timeout=20)  # noqa: S603, S607
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    return res.stdout.strip()


def git_revision(path):
    """'<8 hex digits>' of the commit checked out in the repository at path, '+' appended when it has local
    changes to tracked files; '?' when path is not the root of a git repository."""
    try:
        path = os.path.realpath(path)
        if os.path.realpath(_git(path, 'rev-parse', '--show-toplevel')) != path:
            return '?'
        rev = _git(path, 'rev-parse', '--short=8', 'HEAD')
        if _git(path, 'status', '--porcelain', '--untracked-files=no'):
            rev += '+'
        return rev
    except (OSError, RuntimeError, subprocess.SubprocessError):
        return '?'


def lib_rev(codename):
    """Revision of a library for the firmware's lib_rev field: the manifest's revision() when it has one,
    otherwise the git revision of its repository (the manifest's path). '-' without a library (STUB)."""
    helper = find_library(codename)
    if helper is None:
        return '-'
    revision = getattr(helper, 'revision', None)
    if revision:
        return str(revision())
    path = helper.path
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    return git_revision(path)


def main(argv):
    if len(argv) == 3 and argv[0] == 'default':
        helper = find_library(argv[1])
        if helper is None:
            raise GoalError(f'no library with CRYPTO_LIB "{argv[1]}"')
        print(default_goal(helper, argv[2]))
    elif len(argv) == 2 and argv[0] == 'rev':
        # no padding here: CMakeLists.txt pads it to LIB_REV_WIDTH
        print(lib_rev(argv[1])[:LIB_REV_WIDTH])
    elif len(argv) in (4, 5) and argv[0] == 'check':
        codename, algo, goal = argv[1:4]
        check_goal(goal)
        opts = parse_opts(argv[4] if len(argv) == 5 else '')
        helper = find_library(codename)
        # no manifest (STUB, or an external library kept elsewhere), or an algorithm its manifest does not
        # list (libtomcrypt's SHA-2 behind OPEN_SOURCE): nothing more to check, CMake decides
        if helper is not None and algo in helper.algorithms():
            lib_goals = goals_of(helper, algo)
            if goal not in lib_goals:
                raise GoalError(f'{codename} has no goal "{goal}" for {algo} (it has: {", ".join(lib_goals) or "none"})')
            check_opts(helper, algo, opts)
    elif argv == ['list']:
        for goal, meaning in STANDARD_GOALS.items():
            print(f'{goal:10} {meaning}')
        for p in manifests():
            helper = load(p)
            for algo in helper.algorithms():
                options = getattr(helper, 'options', lambda algo: {})(algo) or {}
                try:
                    lib_goals = goals_of(helper, algo)
                except GoalError as e:
                    # one library that needs fixing does not hide the others
                    print(f'ERROR: {e}')
                    continue
                line = f'{helper.codename:14} {algo:6} {" ".join(lib_goals)}'
                if options:
                    line += f'   (options: {" ".join(sorted(options))})'
                print(line)
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except GoalError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
