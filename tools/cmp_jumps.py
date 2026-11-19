import re, sys
def load(fn):
    out = []
    for line in open(fn):
        m = re.match(r'UNI (\d+) sim_step=(\d+) n=(\d+) before=(\d+) cost=(\d+)', line)
        if m: out.append(tuple(int(x) for x in m.groups()))
    return out
ours, his = load(sys.argv[1]), load(sys.argv[2])
print('jumps', len(ours), len(his))
prev = 0; shown = 0
for a, b in zip(ours, his):
    k, n1, n2 = a[0], a[2], b[2]
    d = (a[3] + a[4]) - (b[3] + b[4])
    if abs(n1 - n2) > 1: print('n differs by more than 1 at', k, n1, n2)
    if d != prev:
        print(f'k={k} after_diff={d} (change {d - prev}) n={n1}/{n2} our_before={a[3]} his_before={b[3]} our_cost={a[4]} his_cost={b[4]}')
        shown += 1
        if shown > 200: break
    prev = d
print('last compared k', min(len(ours), len(his)), 'after_diff', prev)
