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

**Status: not yet confirmed by anyone else.** This value is about `3.37 * 10^26` steps larger than the
estimate `5418883027667422764169643414989497193809945789706483` by @hipparcos, which the bbchallenge wiki
describes as "probably accurate to within about one period". The two agree on the first 25 digits. That
difference is far more than one period, so one of the two step counts is wrong somewhere. The difference has
now been measured exactly at identical configurations (see "Open issue" below), but it is not yet known which
count is wrong.

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
* Chunked run: every uni-cycle jump split into halves (so each cost is re-measured at the midpoint) and the
  three-cycle affinity check on every jump. Same cycle-hit step counts, digit for digit.
* Cross-checks against Pavel's base rules only (no accelerations; `data/crosschecks.txt`):
  * 6 counter strides at nesting depth 11 run out step by step (up to 1.4·10^8 macro steps each): all equal;
  * 17 uni-cycles (counter depth 1 to 3) re-simulated without the counter formula: all equal.

  (`NO1X_DEEPCHK=1 NO1X_UNI_NOCTR=1 ./target/release/no1x 29 40 -a | grep CHK`; the run stops itself
  later when one re-simulated uni-cycle exceeds the 2·10^9-step cap of the check.)

## Open issue

The 3.37·10^26 gap from hipparcos's estimate is unexplained. It is not a multiple of the period. Every part
of the step count here has been checked against Pavel's base rules, which his tests check against the raw
machine: the counter formula (depths 1 to 11), the uni-cycle costs (re-simulated, chunked, affine on every
jump), and the end (raw lockstep). So the gap more likely comes from how the estimate was computed, but that is
not confirmed. Comparing with hipparcos's method would settle it.

Further checks (Nov 14):

* A rerun with every uni-cycle jump logged (11,602 jumps: `n`, first cycle cost, cost increment) gives the same
  cycle hits digit for digit.
* The gap is not one uni-cycle counted twice or missed: no jump has a cycle cost within one period of the gap.
* Common formula slips give far larger differences than the gap: using `n^2/2` or `n(n+1)/2` in place of
  `n(n-1)/2` changes the total by about `10^40`, and dropping one cycle per jump by about `10^44`.
* The gap is `337393947962848037 * 10^9 + 52684`. (See below: this mixes a counting difference with an
  offset between the two marker events, so the round-looking low digits are not by themselves evidence of a
  `10^9`-level rounding.)

Where the estimate comes from (Nov 19). hipparcos's code and notes are in
[jhuang97/turing_machine](https://github.com/jhuang97/turing_machine) (`src/skelet1.rs`,
`notes/skelet1_notes.txt`, trace `turing_machine_traces/skelet1_to_tc.txt`):

* The estimate is not a computed preperiod. It is his base-step count at the moment the first complete `a` block
  (`C2 x^7640 D x^10344`) appears, at his simulator step 85,256,365. His notes call it "still inaccurate due to the
  higher level simulator steps and possibly being off by some fraction of a period". The notes also record an
  earlier u128 overflow in his uni-cycle step count, which he found and fixed before publishing this value.
* His simulator applies the uni-cycle acceleration exactly 11,602 times, the same number of jumps as ours.
* His multi-stride step formula (`multi_stride` in `src/skelet1.rs`) agrees exactly with the counter formula
  above on 2,000 random counters (nesting depths 1 to 6, 1 to 50 strides).
* His symbol encodings (`x=22 D=21 C=11 C0=232 C1=201 C2=42 P=2`, head `<C10` / `A>`) are the same as Pavel's, so
  configurations printed in his trace convert directly to raw tapes (`tools/hip2raw.py`).

**Exact difference at identical configurations.** `tools/match.c` runs the raw machine from our checkpoint and
reports the step at which the tape, head and state equal a target configuration (compared over the whole
30-million-cell window that the target covers). Four configurations from his trace (lines 71, 78, 82, 90; his
simulator steps 85,255,051 to 85,256,001) each occur exactly once in our run, and every one gives the same
difference (`data/hipparcos_matches.txt`):

    our count - his count = 337393947962848045468728629   (= 39840723217854623 * P + 1615701980)

So the two computations disagree by this exact amount for the same configuration. It is a pure step-count
difference, not a difference in definitions. His "first `a` block" configuration is the one at our second
cycle hit, `t0 + P + 106,082`, so

    our t0 - his estimate = 337393947962848045468728629 - (P + 106082) = 337393947962848037000052684

which is exactly the gap above. Which of the two counts is wrong is still open. Line 71 is reached 418,995,281 raw
steps before our `t0` and lines 78 to 90 after it, so the difference is already present before the cycle starts.
It must come from the accelerated part of one of the two runs. The next step is to log hipparcos's step count at
each of his 11,602 uni-cycle jumps, compare that log with ours jump by jump, and find the first jump where they
disagree.

```bash
# reproduce one match (about 1 minute)
git clone https://github.com/jhuang97/turing_machine hip
python3 tools/hip2raw.py hip/turing_machine_traces/skelet1_to_tc.txt 78 t78.txt
gcc -O3 -o match tools/match.c
./match tape.txt t78.txt 6000000000        # tape.txt from step 1 of "Reproduce" -> MATCH step_offset 5432308783
```

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
