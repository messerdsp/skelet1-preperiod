// Logs every uni-cycle jump of hipparcos's accelerated Skelet #1 simulator:
// jump index, simulator step, number of cycles, base steps before the jump, cost of the jump.
use turing_machine::skelet1::{CounterSimulator, CounterStepInfo};
fn main() {
    let mut sim = CounterSimulator::new(true, true);
    let mut k = 0u64;
    for i in 0..200000000u64 {
        let before = sim.base_steps;
        let res = sim.step().unwrap();
        if let CounterStepInfo::UniCycle(n) = res {
            k += 1;
            println!("UNI {k} sim_step={i} n={n} before={before} cost={}", sim.base_steps - before);
            if k == 11602 { println!("END base_steps={}", sim.base_steps); return; }
        }
    }
    println!("END base_steps={}", sim.base_steps);
}
