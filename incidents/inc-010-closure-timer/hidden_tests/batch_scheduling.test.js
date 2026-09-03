import { test } from "node:test";
import assert from "node:assert/strict";
import { VirtualClock } from "../../src/clock.js";
import { JobScheduler } from "../../src/jobScheduler.js";
import { PRINT_JOBS } from "../../src/jobs.js";

test("every scheduled job completes with its own id, not the last job's", () => {
  const clock = new VirtualClock();
  const scheduler = new JobScheduler(clock);
  scheduler.scheduleAll(PRINT_JOBS);
  clock.runAll();

  const gotIds = scheduler.completed.map((c) => c.id).sort();
  const wantIds = PRINT_JOBS.map((j) => j.id).sort();
  assert.deepEqual(gotIds, wantIds);
});

test("each completion carries its own job's name and printer", () => {
  const clock = new VirtualClock();
  const scheduler = new JobScheduler(clock);
  scheduler.scheduleAll(PRINT_JOBS);
  clock.runAll();

  const byId = new Map(scheduler.completed.map((c) => [c.id, c]));
  for (const job of PRINT_JOBS) {
    const completion = byId.get(job.id);
    assert.ok(completion, `no completion recorded for ${job.id}`);
    assert.equal(completion.name, job.name);
    assert.equal(completion.printer, job.printer);
  }
});

test("jobs complete at the time their own delay elapses, in delay order", () => {
  const clock = new VirtualClock();
  const scheduler = new JobScheduler(clock);
  scheduler.scheduleAll(PRINT_JOBS);
  clock.runAll();

  const byId = new Map(scheduler.completed.map((c) => [c.id, c.ranAt]));
  assert.equal(byId.get("job-105"), 10);
  assert.equal(byId.get("job-107"), 20);
  assert.equal(byId.get("job-104"), 30);
  assert.equal(byId.get("job-106"), 50);
});
