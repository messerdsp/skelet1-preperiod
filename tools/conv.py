"""Convert no1x snapshot lines ("sim_step T dir L | R") to raw tapes for lockstep.c / rawadv.c."""
import sys, re
LEFT = {'D': '01101', 'P': '011', '0': '0110111011', '1': '011001', '2': '01111011', '3': '0101'}
RIGHT_STORED = {'D': '01011', 'P': '011', '3': '0101'}
LEFT_A = ['2', 'x^7640', 'D', 'x^10344']
LEFT_B = ['D', 'x^72142', 'D', 'x^3076', 'D', 'x^1538', 'D', 'x^300', 'D', 'x^30826']
RIGHT_B = ['x^30826', 'D', 'x^300', 'D', 'x^1538', 'D', 'x^3076', 'D', 'x^72142', 'D']  # far-first
LEFT_C = ['1', 'D', 'x^72141', '1', 'D', 'x^3075', '1', 'D', 'x^1537', '1', 'D', 'x^299', '1', 'D', 'x^30825']
MAXCELLS = 200_000_000
LEFT_BUDGET = 100_000_000

def left_item(it):
    if it in LEFT: return LEFT[it]
    if it == '!': return '!'
    m = re.fullmatch(r'x\^(\d+)', it)
    if m:
        n = int(m.group(1)); assert n * 6 < MAXCELLS, it; return '011011' * n
    m = re.fullmatch(r'L\((\d+)\)', it)
    if m: return ''.join('0' + '1' * int(c) for c in m.group(1))
    m = re.fullmatch(r'([abc])\^(\d+)', it)
    if m:
        blk = {'a': LEFT_A, 'b': LEFT_B, 'c': LEFT_C}[m.group(1)]
        return ''.join(left_item(i) for i in blk) * int(m.group(2))
    raise ValueError(it)

def right_item_headfirst(it):
    if it in RIGHT_STORED: return RIGHT_STORED[it][::-1]
    m = re.fullmatch(r'x\^(\d+)', it)
    if m:
        n = int(m.group(1)); assert n * 6 < MAXCELLS, it; return '110110' * n
    m = re.fullmatch(r'b\^(\d+)', it)
    if m: return ''.join(right_item_headfirst(i) for i in RIGHT_B[::-1]) * int(m.group(1))
    raise ValueError(it)

def convert(line, sentinel_upto_a=True):
    """Returns (T, sim_step, head_index, state, tape). Everything left of and including the last a-block
    becomes a sentinel '!' cell (that region is assumed never visited again)."""
    head, rest = line.split(' | ')
    ss, T, d, L = head.split(' ', 3)
    litems = L.split(',') if L else []
    ritems = rest.strip().split(',') if rest.strip() else []
    if sentinel_upto_a:
        ai = max([i for i, it in enumerate(litems) if it.startswith('a^')], default=-1)
        if ai >= 0: litems = ['!'] + litems[ai + 1:]
    # keep only the nearest ~LEFT_BUDGET cells of the left tape; beyond them a sentinel
    kept, size = [], 0
    for it in reversed(litems):
        if it == '!': break
        m = re.fullmatch(r'x\^(\d+)', it)
        sz = 6 * int(m.group(1)) if m else 100
        if size + sz > LEFT_BUDGET:
            if m and LEFT_BUDGET - size >= 6:
                kept.append(f"x^{(LEFT_BUDGET - size) // 6}")  # nearest part of a long x-run
            break
        kept.append(it); size += sz
    litems = ['!'] + kept[::-1]
    left = ''.join(left_item(i) for i in litems)
    right = ''.join(right_item_headfirst(i) for i in ritems)
    if d == 'R':
        return int(T), int(ss), len(left), 0, left + right
    else:
        return int(T), int(ss), len(left) - 1, 2, left + '10' + right

if __name__ == '__main__':
    snaps, idx, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    lines = open(snaps).read().splitlines()
    T, ss, h, st, tape = convert(lines[idx])
    with open(out, 'w') as f: f.write(f"{h} {st}\n{tape}\n")
    print(T, ss, h, st, len(tape))
