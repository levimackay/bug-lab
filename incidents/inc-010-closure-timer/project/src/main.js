import { VirtualClock } from "./clock.js";
import { JobScheduler } from "./jobScheduler.js";
import { PRINT_JOBS } from "./jobs.js";

const clock = new VirtualClock();
const scheduler = new JobScheduler(clock);
scheduler.scheduleAll(PRINT_JOBS);
clock.runAll();

console.log(`jobs queued:    ${PRINT_JOBS.length}`);
console.log(`jobs completed: ${scheduler.completed.length}`);
for (const c of scheduler.completed) {
  console.log(`  ${c.id} (${c.name}) on ${c.printer}, done at t=${c.ranAt}ms`);
}

const distinctIds = new Set(scheduler.completed.map((c) => c.id));
if (distinctIds.size !== PRINT_JOBS.length) {
  console.error(`ERROR: expected ${PRINT_JOBS.length} distinct completions, saw ${distinctIds.size}: [${[...distinctIds].join(", ")}]`);
  process.exit(1);
}
process.exit(0);
