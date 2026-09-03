import { test } from "node:test";
import assert from "node:assert/strict";
import { VirtualClock } from "../src/clock.js";
import { JobScheduler } from "../src/jobScheduler.js";

test("a single scheduled job completes with its own id and name", () => {
  const clock = new VirtualClock();
  const scheduler = new JobScheduler(clock);
  scheduler.scheduleAll([{ id: "job-1", name: "Test banner", printer: "Printer-A", delayMs: 10 }]);
  clock.runAll();
  assert.equal(scheduler.completed.length, 1);
  assert.equal(scheduler.completed[0].id, "job-1");
  assert.equal(scheduler.completed[0].name, "Test banner");
});

test("scheduling nothing completes nothing", () => {
  const clock = new VirtualClock();
  const scheduler = new JobScheduler(clock);
  scheduler.scheduleAll([]);
  clock.runAll();
  assert.deepEqual(scheduler.completed, []);
});
