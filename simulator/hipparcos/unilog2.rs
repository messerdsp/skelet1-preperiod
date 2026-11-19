// For every uni-cycle jump of hipparcos's simulator, report jumps that leave the head facing Left
// (level-0 counter: multi_stride sets dir = Left and try_uni_cycle does not undo it), with the cost of
// one sweep "> w R ==> < w R" over the right tape after the jump: 16/x, 16/D, 1726192/G, 9 for the bounce.
use turing_machine::skelet1::{BigInt, CounterBlockType, CounterSimulator, CounterStepInfo, CounterSymbol, Direction};

fn main() {
    let mut sim = CounterSimulator::new(true, true);
    let mut k = 0u64;
    let mut total = BigInt::ZERO;
    let mut count = 0u64;
    for _ in 0..85257400u64 {
        let res = sim.step().unwrap();
        if let CounterStepInfo::UniCycle(n) = res {
            k += 1;
            if sim.dir == Direction::Left {
                let mut sweep = BigInt::from(9u8);
                let mut ok = true;
                for s in &sim.right_tape {
                    match s {
                        CounterSymbol::X(e) => sweep += BigInt::from(*e) * BigInt::from(16u8),
                        CounterSymbol::D => sweep += BigInt::from(16u8),
                        CounterSymbol::Block(CounterBlockType::G, e) => sweep += BigInt::from(*e) * BigInt::from(1726192u32),
                        CounterSymbol::R => (),
                        _ => ok = false,
                    }
                }
                if !ok { println!("LEFT {k} n={n} right tape has other symbols"); continue; }
                total += sweep;
                count += 1;
                println!("LEFT {k} n={n} sweep={sweep}");
            }
        }
    }
    println!("JUMPS_LEFT {count} TOTAL_SWEEP {total}");
}
