// For uni-cycle jump K of hipparcos's simulator: compare the jump's formula cost with the cost of its first
// three cycles simulated with the uni-cycle acceleration off (his base counter rules plus strides).
use turing_machine::skelet1::{BigInt, CounterSimulator, CounterStepInfo, CounterSymbol, Direction};
use CounterSymbol::*;

const P: u128 = 53946;

fn cycle_end(sim: &CounterSimulator, x_target: u128) -> bool {
    sim.dir == Direction::Right
        && matches!(sim.left_tape.as_slice(), [.., C2, D, X(x), C1, D] if *x == x_target)
}

fn rstr(sim: &CounterSimulator) -> String {
    sim.right_tape.iter().rev().map(|s| format!("{s}")).collect::<Vec<_>>().join(",")
}

fn main() {
    let gdef: Vec<String> = turing_machine::skelet1::right_block_definition()[&turing_machine::skelet1::CounterBlockType::G]
        .iter().map(|s| format!("{s}")).collect();
    println!("GDEF_RIGHT {}", gdef.join(","));
    let ks: Vec<u64> = std::env::args().skip(1).map(|a| a.parse().unwrap()).collect();
    let kmax = *ks.iter().max().unwrap();
    let mut sim = CounterSimulator::new(true, true);
    let mut k = 0u64;
    loop {
        let pre = sim.dir == Direction::Right
            && matches!(sim.left_tape.as_slice(), [.., CounterSymbol::Block(_, 1), X(_), C1, D]);
        if ks.contains(&(k + 1)) && sim.dir == Direction::Right {
            println!("HSTR {} {}", sim.base_steps, rstr(&sim));
        }
        if !pre || !ks.contains(&(k + 1)) {
            if let CounterStepInfo::UniCycle(_) = sim.step().unwrap() {
                k += 1;
                if k >= kmax { break; }
            }
            continue;
        }
        let mut probe = sim.clone();
        let before = probe.base_steps;
        let res = probe.step().unwrap();
        if let CounterStepInfo::UniCycle(n) = res {
            k += 1;
            if ks.contains(&k) {
                let jump_cost = probe.base_steps - before;
                let x0 = match sim.left_tape.as_slice() { [.., X(x), C1, D] => *x, _ => panic!() };
                let rdesc: Vec<String> = sim.right_tape.iter().rev().take(12).map(|s| format!("{s}")).collect();
                let n_c = sim.right_tape.iter().filter(|s| **s == C).count();
                let n_g: u128 = sim.right_tape.iter().map(|s| match s { CounterSymbol::Block(_, e) => *e, _ => 0 }).sum();
                println!("JUMP {k} n={n} x0={x0} right_C={n_c} right_blocks={n_g} right_head={}", rdesc.join(" "));
                let mut raw = sim.clone();
                raw.do_uni_cycles = false;
                let mut costs: Vec<BigInt> = Vec::new();
                let mut start = raw.base_steps;
                for c in 1..=3u128.min(n) {
                    let mut guard = 0u64;
                    loop {
                        if c == 1 && raw.dir == Direction::Right && raw.can_do_stride() {
                            println!("HSTR {} {}", raw.base_steps, rstr(&raw));
                        }
                        raw.step().unwrap();
                        guard += 1;
                        if cycle_end(&raw, x0 - c * P) { break; }
                        if guard > 50_000_000 { println!("  cycle {c}: end not found"); return; }
                    }
                    costs.push(raw.base_steps - start);
                    start = raw.base_steps;
                }
                let nb = BigInt::from(n);
                let affine = if costs.len() >= 2 {
                    let d = costs[1] - costs[0];
                    nb * costs[0] + d * (nb * (nb - BigInt::ONE) / BigInt::TWO)
                } else { costs[0] * nb };
                let affine_ok = costs.len() < 3 || costs[2] - costs[1] == costs[1] - costs[0];
                println!("  cycle costs (base rules): {:?} affine_check={affine_ok}", costs.iter().map(|c| c.to_string()).collect::<Vec<_>>());
                println!("  jump formula cost   = {jump_cost}");
                println!("  affine from cycles  = {affine}");
                if affine >= jump_cost { println!("  affine - formula    = {}", affine - jump_cost); }
                else { println!("  formula - affine    = {}", jump_cost - affine); }
            }
            if k >= kmax { break; }
        }
        sim = probe;
    }
}
