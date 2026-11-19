"""Convert one line of hipparcos's skelet1_to_tc.txt trace to a raw tape (head index, state, tape) using Pavel/conv.py encodings."""
import sys, re
LEFT = {'D':'01101','P':'011','C0':'0110111011','C1':'011001','C2':'01111011','C':'0101'}
RIGHT_HF = {'D':'11010','P':'110','C':'1010','R':'110'}   # head-first order
A_BLK = ['C2','x^7640','D','x^10344']
BUDGET = 30_000_000
def left_cells(tok):
    if tok in LEFT: return LEFT[tok]
    m = re.fullmatch(r'x(?:\^(\d+))?', tok)
    if m: return '011011' * int(m.group(1) or 1)
    m = re.fullmatch(r'\[a\](?:\^(\d+))?', tok)
    if m: return ''.join(left_cells(t) for t in A_BLK) * int(m.group(1) or 1)
    raise ValueError(tok)
def right_cells(tok):
    if tok in RIGHT_HF: return RIGHT_HF[tok]
    m = re.fullmatch(r'x(?:\^(\d+))?', tok)
    if m: return '110110' * int(m.group(1) or 1)
    raise ValueError(tok)
line = open(sys.argv[1]).read().splitlines()[int(sys.argv[2]) - 1]
line = re.sub(r'\x1b\[[0-9;]*m', '', line)
head, cfg = line.split(': ', 1)
T = int(head.split(' | ')[2])
toks = cfg.split()
assert toks[0] == 'L' and toks[-1] == 'R', (toks[0], toks[-1])
hi = [i for i, t in enumerate(toks) if t in ('<', '>')]; assert len(hi) == 1
h = hi[0]
ltoks = toks[1:h]; rtoks = toks[h+1:]
assert ltoks[0] == '[debris 2]' or ltoks[0] == '[debris', ltoks[:2]
ltoks = ltoks[2:] if ltoks[0] == '[debris' else ltoks[1:]
# debris 2 ends with a huge x-run (x^3179489803280); only its nearest cells can matter
left = ''.join(left_cells(t) for t in ltoks)
left = ('011011' * ((BUDGET - len(left)) // 6)) + left
left = '!' + left
right = ''.join(right_cells(t) for t in rtoks)
if toks[h] == '>':
    hd, st, tape = len(left), 0, left + right
else:
    hd, st, tape = len(left) - 1, 2, left + '10' + right
open(sys.argv[3], 'w').write(f"{hd} {st}\n{tape}\n")
print(T, hd, st, len(tape))
