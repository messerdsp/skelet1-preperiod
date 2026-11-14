# Skelet #1: exact preperiod

Machine: `1RB1RD_1LC0RC_1RA1LD_0RE0LB_---1RC` (BB(5) "Skelet #1", a translated cycler with
period 8,468,569,863 steps and a shift of 107,917 cells to the right).

## Result

    preperiod t0 = 5418883027667422764169643752383445156657982789759167

**Definition.** Steps are counted from the blank tape (step 0 is the start). Step `t` is the transition taken
from configuration `t` to `t+1`, identified by (state, symbol read). `t0` is the smallest `t` such that
step `t'` equals step `t' + P` for every `t' >= t`, with `P = 8,468,569,863`. In other words, the machine
runs `t0` steps and then repeats a fixed sequence of `P` transitions forever. Other definitions (for example
one based on whole tape configurations) can differ from this one by less than one period.

The configuration `0 > x^7639 D ... 3 x^3849 P` used in Pavel Kropitz's `translated_cycle` test first
occurs at step `t0 + 106,082 = 5418883027667422764169643752383445156657982789865249`.

**Status: not yet confirmed independently.** This value is about `3.37 * 10^26` steps larger than the
estimate `5418883027667422764169643414989497193809945789706483` by @hipparcos, which the bbchallenge wiki
describes as "probably accurate to within about one period". The two agree on the first 25 digits. That
difference is far more than one period, so one of the two step counts is wrong somewhere. It has not been
resolved yet; see "Open issue" below.

## Method

1. **Accelerated simulation with exact step counts.** `simulator/no1x.diff` is a patch to Pavel Kropitz's
   simulator (`univerz/bbc`, branch `no1`, commit `9b73376`, file `src/bin/no1.rs`). His simulator counts
   steps exactly for its basic block rules (checked against the raw machine by his own tests), but not
   for its two accelerations. The patch adds:
   * **counter acceleration:** a closed formula. For a counter `> S_0 3 S_1 3 ... 3 S_k P`, with
     `RL(S)` = steps to cross segment `S` right and back (`16` per `x`, `16` per `D`, `1,726,192` per `b`),
     one stride at level `j` costs `St_j = RL(S_{j-1}) + 99 + 4*St_{j+1} + 6*D_{j+1}`, with
     `St_{k+1} = RL(S_k) + 9`, `D_{k+1} = 0`, `D_j = 16*D_{j+1} + 112`. `N` strides cost
     `N*St_1 + D_1*N*(N-1)/2`.
   * **uni-cycle acceleration:** before each jump of `n` uni-cycles, the next cycles are simulated without the
     jump (with exact counter costs). The cost of cycle `i` is affine in `i`, so `n` cycles cost
     `n*c0 + (c1-c0)*n*(n-1)/2`.
   * big-integer step totals (the total does not fit in 128 bits).
2. **Raw check of the cycle start.** The last jump larger than `10^11` steps ends at simulator step
   98,749,155. That configuration (`data/checkpoint.txt.gz`, step count in Pavel's units, add 19 for steps from
   blank) is written out as a raw tape (`tools/conv.py`). `tools/lockstep.c` runs two copies of the raw machine,
   one `P` steps ahead of the other, and compares their transitions step by step. The last disagreement is at
   offset 5,431,587,297 from the checkpoint, which gives `t0`.

## Checks done

* Counter formula vs. the same simulator with counter acceleration off: 1,780 matching configurations,
  counters of 1 to 10 digits, 0 mismatches (up to about `10^14` steps).
* Every uni-cycle jump: the first simulated cycle must give exactly the configuration that Pavel's jump
  gives; for the first 40 jumps, a third cycle confirms that the cost is affine.
* Pavel's start configuration `1 > P` is raw step 19 (direct simulation from blank).
* The three cycle hits are exactly `P` apart in the accelerated count.
* Lockstep: periodic from `t0` through the cycle hit and two more full periods; the second copy is shifted
  107,917 cells to the right, as expected. The left tape beyond 100 million cells is replaced by a sentinel
  that stops the program if reached; it was never reached.
* Restarting the accelerated run from a saved snapshot gives the same step counts.

## Open issue

The 3.37·10^26 gap from hipparcos's estimate is unexplained. It is not a multiple of the period. The
most likely places for an error on this side are the uni-cycle extrapolation (about 1.9·10^20 uni-cycles in
total, too many to simulate one by one) and the counter formula at nesting depths above 10. A run that splits
every uni-cycle jump into halves and checks affinity on every jump is the next test. Comparing with however
hipparcos computed the estimate would settle it.

## Reproduce

```bash
# 1. the raw check (about 1 minute; needs ~200 MB RAM)
zcat data/checkpoint.txt.gz > cp.txt
python3 tools/conv.py cp.txt 0 tape.txt
gcc -O3 -o lockstep tools/lockstep.c
./lockstep tape.txt 8468569863 5431693380
# -> last_mismatch 5431587297 ... head_shift 107917
# t0 = 5418883027667422764169643752383445156657977358171850 + 19 + 5431587297 + 1

# 2. the accelerated run (about 20 minutes)
git clone -b no1 https://github.com/univerz/bbc && cd bbc && git checkout 9b73376
cp src/bin/no1.rs src/bin/no1x.rs && patch src/bin/no1x.rs < ../simulator/no1x.diff
sed -i 's/^\[dependencies\]/[dependencies]\nnum-bigint = "=0.4.3"/' Cargo.toml
rustup toolchain install nightly-2023-04-27
RUSTFLAGS="-C target-cpu=native" cargo +nightly-2023-04-27 build --release --bin no1x   # RUSTFLAGS drops the repo's mold linker flag
./target/release/no1x 28 40 -a | grep '^TC'
```

`data/cycle_hits.txt` has the output of step 2 (the step counts there are in Pavel's units: add 19).

## Credits

Simulator and block rules: Pavel Kropitz (univerz). Analysis of the machine: Shawn Ligocki and others in the
bbchallenge community. Estimate compared against: @hipparcos.

Step counting, raw check and write-up by messerdsp, with Claude Opus 5.5.
