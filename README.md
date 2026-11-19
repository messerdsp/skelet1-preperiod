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
describes as "probably accurate to within about one period". That gap is now explained to the last digit (see
"The gap to the earlier estimate" below). hipparcos's simulator skips one uncounted sweep across the tape after
13 of its uni-cycle jumps. With a one-line fix, his simulator agrees with ours at every one of the 11,602 jumps.

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

## The gap to the earlier estimate

**Summary.**

    our t0 - his estimate = 337393947962848037000052684
                          = 337393947962848045468728629   (steps hipparcos's simulator never counts)
                          - (P + 106082)                  (his marker event comes one period after t0)

Both parts are established exactly below. hipparcos's code and notes are in
[jhuang97/turing_machine](https://github.com/jhuang97/turing_machine) (commit `5c91d34`; `src/skelet1.rs`,
`notes/skelet1_notes.txt`, trace `turing_machine_traces/skelet1_to_tc.txt`).

**The bug.** In `src/skelet1.rs`, `try_uni_cycle` computes the cost of `k` uni-cycles and then calls
`multi_stride(k*T)` to update the counter on the right. When that counter has level 0 (no `C` on the right
tape), `multi_stride` takes its `> w0 R ==> < w0 R` branch, which also sets `self.dir = Left`.
`try_uni_cycle` never turns the head back to the right. The rule it implements,
`J x^(N+P) C1 D > r  -->  F J x^N C1 D > G s^T(r)`, ends with the head facing right, and the step count it
returns is for that configuration. So after such a jump his tape is one sweep (`> G^k r ==> < G^k r`) further
along than his step count says. Each time this happens, the cost of that sweep is lost.

* It happens at 13 of his 11,602 jumps (jumps 1166 to 11553; `data/hipparcos_skipped_sweeps.txt`, from
  `simulator/hipparcos/unilog2.rs`). The 13 sweep costs add up to exactly 337393947962848045468728629.
* Fix (`simulator/hipparcos/fix_dir_after_uni_cycle.diff`): set `self.dir = Right` at the end of
  `try_uni_cycle`. With it, his step count after each of the 11,602 jumps equals ours, ending with a
  difference of 0 (`data/uni_jumps_hipparcos_fixed.txt.gz` against `data/uni_jumps_ours.txt.gz`, compared with
  `tools/cmp_jumps.py`). Without it, the two logs agree exactly up to jump 1166 and then differ by the
  accumulated skipped sweeps (`data/uni_jumps_hipparcos.txt.gz`).
* Direct look at the first case: after jump 1166, our run sweeps across the right tape 3 times before reaching
  `D x^96588465265005731513 C x R`; his sweeps twice. The missing sweep costs 3170649210060961228601 steps,
  exactly the cost of one sweep over the right tape at that point (`16` per `x`, `16` per `D`, `1,726,192` per
  `G`, `9` for the bounce at `R`).
* His own consistency check passes regardless: at jumps 1166, 1167 and 2323, his jump formula equals the cost of
  the same cycles simulated with his base rules (`simulator/hipparcos/uniprobe.rs`). The jump costs are right.
  Only the head direction after the jump is wrong.

**The marker event.** The estimate is not a computed preperiod. It is his step count at the moment the first
complete `a` block (`C2 x^7640 D x^10344`) appears, at his simulator step 85,256,365. His notes call it "still
inaccurate due to the higher level simulator steps and possibly being off by some fraction of a period". That
configuration is the one at our second cycle hit, `t0 + P + 106,082`.

Earlier checks that led here:

* His notes record an earlier u128 overflow in his uni-cycle step count, which he found and fixed before
  publishing this value. That one is not the cause here.
* The gap is not one uni-cycle counted twice or missed, and common formula slips (`n^2/2` or `n(n+1)/2` for
  `n(n-1)/2`, one cycle dropped per jump) give differences of `10^40` or more.
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

which is exactly the gap above. Line 71 is reached 418,995,281 raw steps before our `t0`, so the difference
was already there before the cycle starts. That pointed to the accelerated part, and the jump-by-jump
comparison above found the cause.

```bash
# reproduce one configuration match (about 1 minute)
git clone https://github.com/jhuang97/turing_machine hip
python3 tools/hip2raw.py hip/turing_machine_traces/skelet1_to_tc.txt 78 t78.txt
gcc -O3 -o match tools/match.c
./match tape.txt t78.txt 6000000000        # tape.txt from step 1 of "Reproduce" -> MATCH step_offset 5432308783

# reproduce the jump-by-jump comparison (a few minutes each)
cd hip && git checkout 5c91d34 && cp ../simulator/hipparcos/unilog*.rs src/bin/
cargo build --release --bin unilog --bin unilog2
./target/release/unilog2 | tail -1          # -> JUMPS_LEFT 13 TOTAL_SWEEP 337393947962848045468728629
./target/release/unilog > hip.log
patch -p1 < ../simulator/hipparcos/fix_dir_after_uni_cycle.diff
cargo build --release --bin unilog && ./target/release/unilog > hip_fixed.log
cd ../bbc && NO1X_UNILOG=1 ./target/release/no1x 28 40 -a | grep '^UNI ' > ../ours.log   # build as in "Reproduce"
cd .. && python3 tools/cmp_jumps.py ours.log hip_fixed.log | tail -1    # -> after_diff 0
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
