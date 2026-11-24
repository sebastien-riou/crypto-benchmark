#!/usr/bin/env python3
"""Draws the results of an ML-DSA or ML-KEM benchmark as an SVG chart, or prints them as Markdown tables.

    python3 plot_results.py <csv> --pset 87 --mhz 160 --title "ML-DSA-87 on the STM32U5A5" --output mldsa87.svg
    python3 plot_results.py <csv> --tables

<csv> is a file made by format_results.py (format csv): the performance table, then the memory footprint.

The chart, for one parameter set: one row per library, grouped by optimization goal (README.md, "Optimization
goals"), and columns of bars, each column with its own scale from zero:
- the time of the algorithm's main operation. With --mhz, the frequency of the CPU, it is a duration: in
  milliseconds, or in microseconds when an average is below one millisecond. Without, it stays in millions of
  cycles.
  ML-KEM, decapsulation: average keys as a bar and, a few percent further on the same scale, the worst-case key
  as a dot.
  ML-DSA, signature: average over the messages, and slowest message. The slowest takes 10 to 20 times the average
  or more, so it has a column of its own: on its scale the averages could not be told apart, and two scales in one
  column would make two marks look comparable when they are not;
- the RAM: stack + heap + static RAM, in KiB;
- the flash, in KiB.
In each goal, the libraries are sorted by what the goal optimizes (smallram: RAM, smallcode: flash, otherwise time).
Values are printed with the decimal places that matter: none from 10, one below 10. A column that pairs an
average with its worst case keeps the same number of places on every row, enough to tell the two apart.
With --output, the text alternative of the chart (for the image's alt text) is printed.

No dependency beyond Python 3. One series, so one color and no legend; a value on each bar, so no axis ticks;
text in ink colors only. Blue #2a78d6 on white: contrast 4.4:1.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import goals as goals_module

FONT = 'Helvetica, Arial, sans-serif'
BAR = '#2a78d6'
INK, INK2, MUTED = '#0b0b0b', '#52514e', '#898781'
AXIS, SURFACE = '#c3c2b7', '#ffffff'
# 640 px is 480 pt, the text width of an A4 page: text of 12 px stays at 9 pt there
W = 640
SIZE = 12        # labels and values
SMALL = 11       # units and keys
ROW_H, BAR_H = 24, 12

# main operation of each algorithm: (operation in the csv, name in the chart)
MAIN_OP = {'mldsa': ('sign', 'Signature'), 'mlkem': ('decaps', 'Decapsulation')}
# what each goal's libraries are sorted by: index in a row's (time, RAM, flash)
SORT_BY = {'smallram': (1, 'RAM'), 'smallcode': (2, 'flash')}


def parse(path):
    """-> (perf, mem, notes): perf[(implementation, pset)][operation] = [minimum, average, worst] (strings, as
    printed), mem[(implementation, pset)] = [stack, heap, static RAM, flash] (strings), notes = the other lines."""
    perf, mem, notes = {}, {}, []
    with open(path) as f:
        for line in f:
            fields = [x.strip() for x in line.rstrip('\n').split(',')]
            if len(fields) == 6 and fields[1].isdigit():
                key = (fields[0], fields[1])
                try:
                    float(fields[2])
                    mem[key] = fields[2:]
                except ValueError:
                    perf.setdefault(key, {})[fields[2]] = fields[3:]
            elif line.strip() and not line.startswith('Implementation,'):
                notes.append(line.strip())
    return perf, mem, notes


def algo_of(perf):
    ops = {op for v in perf.values() for op in v}
    for algo, (op, _) in MAIN_OP.items():
        if op in ops:
            return algo
    raise SystemExit(f'neither an ML-DSA nor an ML-KEM table (operations: {", ".join(sorted(ops))})')


def split_name(impl):
    """'mldsa-native-smallram' -> ('mldsa-native', 'smallram')"""
    lib, _, goal = impl.rpartition('-')
    return lib, goal


def goal_order(goal):
    std = list(goals_module.STANDARD_GOALS)
    return (std.index(goal), '') if goal in std else (len(std), goal)


def rows_of(perf, mem, pset, algo):
    """-> {goal: [row]} for one parameter set, each goal's rows sorted by what the goal optimizes.
    row: dict(lib, time (average of the main operation), worst (its worst case), ram, flash, as floats or None)."""
    op = MAIN_OP[algo][0]
    panels = {}
    for (impl, p), ops in perf.items():
        if p != pset or op not in ops:
            continue
        lib, goal = split_name(impl)
        m = mem.get((impl, p))
        row = {'lib': lib, 'impl': impl, 'time': float(ops[op][1]), 'worst': float(ops[op][2]),
               'ram': sum(float(x) for x in m[:3]) if m else None, 'flash': float(m[3]) if m else None}
        panels.setdefault(goal, []).append(row)
    for goal, rows in panels.items():
        index = SORT_BY.get(goal, (0, 'time'))[0]
        rows.sort(key=lambda r: ((r['time'], r['ram'], r['flash'])[index] is None,
                                 (r['time'], r['ram'], r['flash'])[index] or 0, r['lib']))
    return dict(sorted(panels.items(), key=lambda kv: goal_order(kv[0])))


def short(v):
    """A value with the decimal places that matter: none from 10, one below 10, two significant digits below 1."""
    if v is None:
        return 'no data'
    if v >= 9.95:
        return f'{v:.0f}'
    if v >= 0.995:
        return f'{v:.1f}'
    return f'{v:.2g}'


def pair_decimals(pairs):
    """Decimal places for a column of (average, worst case): those its smallest value needs, and more while a
    worst case would print the same as its average. The same number for the whole column, so that it reads evenly."""
    smallest = min(a for a, _ in pairs)
    decimals = 0 if smallest >= 9.95 else 1 if smallest >= 0.995 else 2
    while decimals < 3 and any(a != b and f'{a:.{decimals}f}' == f'{b:.{decimals}f}' for a, b in pairs):
        decimals += 1
    return decimals


def time_unit(panels, mhz):
    """-> (factor from millions of cycles, unit, unit in words): a duration when the CPU's frequency is given, in
    milliseconds, or in microseconds when an average is below one millisecond."""
    if not mhz:
        return 1, 'millions of cycles', 'millions of cycles'
    if min(r['time'] for rows in panels.values() for r in rows) * 1000 / mhz < 1:
        return 1e6 / mhz, '\u00b5s', 'microseconds'
    return 1000 / mhz, 'ms', 'milliseconds'


# ---- SVG

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def text_width(s, size):
    """Width of a text in Helvetica, close enough to keep labels apart."""
    w = 0
    for c in s:
        if c in " .,:;/'|!ijlI()[]":
            w += 0.28
        elif c in 'ftr-':
            w += 0.34
        elif c in 'mwMW':
            w += 0.83
        elif c.isupper():
            w += 0.68
        else:
            w += 0.556
    return w * size


def text(x, y, s, size=SIZE, fill=INK2, anchor='start', weight='normal'):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>')


def bar(x0, x1, y, h, fill, r=4):
    """Horizontal bar: square at the baseline x0, rounded data end at x1."""
    if x1 - x0 < 0.5:
        return ''
    r = min(r, (x1 - x0) / 2, h / 2)
    return (f'<path d="M{x0:.1f},{y:.1f} H{x1 - r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{y + r:.1f} '
            f'V{y + h - r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1 - r:.1f},{y + h:.1f} H{x0:.1f} Z" fill="{fill}"/>')


def dot(x, y, fill):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fill}" stroke="{SURFACE}" stroke-width="2"/>'


def chart(panels, algo, title, mhz=None):
    """-> the SVG text"""
    rows = [r for rs in panels.values() for r in rs]
    k, unit, _ = time_unit(panels, mhz)

    # A column: its name (None: it continues the previous column's), the keys of its second header line (glyph and
    # text), its mark (bar; bar+dot: a bar to 'value' and a dot at 'extent' on the same scale), the value label of
    # a row, and its share of the width.
    op_name = f'{MAIN_OP[algo][1]} ({unit})'
    decimals = pair_decimals([(r['time'] * k, r['worst'] * k) for r in rows])
    if algo == 'mlkem':
        columns = [dict(name=op_name, keys=[('bar', 'average keys'), ('dot', 'worst-case key')], mark='bar+dot',
                        value=lambda r: r['time'], extent=lambda r: r['worst'],
                        label=lambda r: f'{r["time"] * k:.{decimals}f} / {r["worst"] * k:.{decimals}f}',
                        share=0.42)]
        memory_shares, gap = (0.30, 0.28), 20
    else:
        columns = [dict(name=op_name, keys=[(None, 'average')], mark='bar',
                        value=lambda r: r['time'], extent=lambda r: r['time'],
                        label=lambda r: short(r['time'] * k), share=0.27),
                   dict(name=None, keys=[(None, 'slowest message')], mark='bar',
                        value=lambda r: r['worst'], extent=lambda r: r['worst'],
                        label=lambda r: short(r['worst'] * k), share=0.27)]
        memory_shares, gap = (0.24, 0.22), 16
    columns += [dict(name='RAM (KiB)', keys=[(None, 'stack + heap + static')], mark='bar',
                     value=lambda r: r['ram'], extent=lambda r: r['ram'],
                     label=lambda r: short(r['ram']), share=memory_shares[0]),
                dict(name='Flash (KiB)', keys=[(None, 'code and constants')], mark='bar',
                     value=lambda r: r['flash'], extent=lambda r: r['flash'],
                     label=lambda r: short(r['flash']), share=memory_shares[1])]

    label_w = max(text_width(r['lib'], SIZE) for r in rows) + 14
    avail = W - label_w - (len(columns) - 1) * gap - 8
    x = label_w
    for c in columns:
        col_w = avail * c['share']
        widest = max(text_width(c['label'](r), SIZE) for r in rows)
        # the marks take what the widest value label leaves; a dot overhangs its position by 4.5 px
        c['x0'] = x
        c['plot_w'] = col_w - widest - (7 + (5 if 'dot' in c['mark'] else 0))
        c['top'] = max((c['extent'](r) or 0) for r in rows) or 1
        x += col_w + gap

    out = []
    y = 0
    out.append(text(0, y + 15, title, size=13, fill=INK, weight='bold'))
    y += 34
    for c in columns:
        if c['name']:
            out.append(text(c['x0'], y, c['name'], fill=INK))
        kx = c['x0']
        for glyph, label in c['keys']:
            # the key of a bar and of a dot, drawn in the muted ink
            if glyph == 'bar':
                out.append(bar(kx, kx + 16, y + 6, 9, MUTED, r=3))
                kx += 21
            elif glyph == 'dot':
                out.append(f'<line x1="{kx:.1f}" y1="{y + 10.5}" x2="{kx + 12:.1f}" y2="{y + 10.5}" '
                           f'stroke="{MUTED}" stroke-width="2"/>')
                out.append(dot(kx + 14, y + 10.5, MUTED))
                kx += 24
            out.append(text(kx, y + 15, label, size=SMALL, fill=MUTED))
            kx += text_width(label, SMALL) + 12
    y += 30
    for goal, goal_rows in panels.items():
        out.append(text(0, y + 13, goal, fill=INK, weight='bold'))
        sorted_by = SORT_BY.get(goal, (0, 'time'))[1]
        out.append(text(text_width(goal, SIZE) * 1.06 + 8, y + 13, f'sorted by {sorted_by}', size=SMALL, fill=MUTED))
        y += 20
        for c in columns:
            out.append(f'<line x1="{c["x0"]:.1f}" y1="{y}" x2="{c["x0"]:.1f}" y2="{y + ROW_H * len(goal_rows)}" '
                       f'stroke="{AXIS}" stroke-width="1"/>')
        for r in goal_rows:
            by = y + (ROW_H - BAR_H) / 2
            mid = by + BAR_H / 2
            base = by + BAR_H - 2
            out.append(text(label_w - 10, base, r['lib'], anchor='end'))
            for c in columns:
                x0, v = c['x0'], c['value'](r)
                end = x0
                if v is not None:
                    sx = lambda value: x0 + value / c['top'] * c['plot_w']
                    end = sx(v)
                    out.append(bar(x0, end, by, BAR_H, BAR))
                    e = c['extent'](r)
                    if c['mark'] == 'bar+dot' and e is not None:
                        out.append(f'<line x1="{end:.1f}" y1="{mid:.1f}" x2="{sx(e):.1f}" y2="{mid:.1f}" '
                                   f'stroke="{BAR}" stroke-width="2"/>')
                        out.append(dot(sx(e), mid, BAR))
                        end = sx(e) + 4.5
                out.append(text(end + 7, base, c['label'](r)))
            y += ROW_H
        y += 12
    h = y - 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:.0f}" viewBox="0 0 {W} {h:.0f}" '
            f'role="img">\n<title>{esc(title)}</title>\n<rect width="{W}" height="{h:.0f}" fill="{SURFACE}"/>\n'
            + '\n'.join(s for s in out if s) + '\n</svg>\n')


def alt_text(panels, algo, title, mhz=None):
    """What the chart shows, in words: for the image's alt text."""
    k, _, unit = time_unit(panels, mhz)
    op = MAIN_OP[algo][1].lower()
    what = (f'{op} in {unit} (average keys, then the worst-case key)' if algo == 'mlkem'
            else f'{op} in {unit} (average, then the slowest message)')
    decimals = pair_decimals([(r['time'] * k, r['worst'] * k) for rows in panels.values() for r in rows])
    parts = []
    for goal, rows in panels.items():
        items = []
        for r in rows:
            t = (f'{r["time"] * k:.{decimals}f} and {r["worst"] * k:.{decimals}f}' if algo == 'mlkem'
                 else f'{short(r["time"] * k)} and {short(r["worst"] * k)}')
            m = 'no memory data' if r['ram'] is None else f'{short(r["ram"])}, {short(r["flash"])}'
            items.append(f'{r["lib"]} {t}, {m}')
        parts.append(f'Goal {goal}: ' + '; '.join(items) + '.')
    return f'{title}. For each library: {what}, RAM in KiB, flash in KiB. ' + ' '.join(parts)


# ---- Markdown tables

def tables(perf, mem, notes, algo):
    psets = sorted({p for _, p in perf}, key=int)
    name = {'mldsa': 'ML-DSA', 'mlkem': 'ML-KEM'}[algo]
    out = []
    for pset in psets:
        panels = rows_of(perf, mem, pset, algo)
        out.append(f'### {name}-{pset}\n')
        if algo == 'mldsa':
            out.append('| Goal | Library | Key generation | Signature, fastest | Signature, average | '
                       'Signature, slowest | Verification | Stack | Heap | Static RAM | Flash |')
            out.append('|---|---|---|---|---|---|---|---|---|---|---|')
        else:
            out.append('| Goal | Library | Key generation | Encapsulation | Decapsulation | Stack | Heap | '
                       'Static RAM | Flash |')
            out.append('|---|---|---|---|---|---|---|---|---|')
        for goal, rows in panels.items():
            for r in rows:
                ops = perf[(r['impl'], pset)]
                m = mem.get((r['impl'], pset), ['', '', '', ''])
                if algo == 'mldsa':
                    cells = [ops['key-exp'][1], ops['sign'][0], ops['sign'][1], ops['sign'][2], ops['verify'][1]]
                else:
                    cells = [f'{ops[o][1]} / {ops[o][2]}' for o in ('key-exp', 'encaps', 'decaps')]
                out.append(f'| `{goal}` | {r["lib"]} | ' + ' | '.join(cells + list(m)) + ' |')
        out.append('')
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('csv', help='results made by format_results.py (format csv)')
    parser.add_argument('--pset', help='parameter set to draw, e.g. 87 or 768')
    parser.add_argument('--title', help='title of the chart')
    parser.add_argument('--mhz', type=float, help="frequency of the CPU in MHz: the chart's times are then durations")
    parser.add_argument('--output', help='SVG file to write')
    parser.add_argument('--tables', action='store_true', help='print the results as Markdown tables')
    args = parser.parse_args()
    perf, mem, notes = parse(args.csv)
    algo = algo_of(perf)
    if args.tables:
        print(tables(perf, mem, notes, algo))
        return
    if not (args.pset and args.title and args.output):
        parser.error('--pset, --title and --output are needed to draw a chart (or use --tables)')
    panels = rows_of(perf, mem, args.pset, algo)
    if not panels:
        raise SystemExit(f'no result for the parameter set {args.pset} in {args.csv}')
    with open(args.output, 'w') as f:
        f.write(chart(panels, algo, args.title, args.mhz))
    print(alt_text(panels, algo, args.title, args.mhz))


if __name__ == '__main__':
    main()
