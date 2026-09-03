import { test } from "node:test";
import assert from "node:assert/strict";
import { VirtualClock } from "../src/clock.js";

test("runAll fires callbacks in delay order regardless of registration order", () => {
  const clock = new VirtualClock();
  const order = [];
  clock.setTimeout(() => order.push("late"), 30);
  clock.setTimeout(() => order.push("early"), 5);
  clock.runAll();
  assert.deepEqual(order, ["early", "late"]);
});

test("now() reflects the time of the callback currently firing", () => {
  const clock = new VirtualClock();
  let seenAt = null;
  clock.setTimeout(() => {
    seenAt = clock.now();
  }, 15);
  clock.runAll();
  assert.equal(seenAt, 15);
});
