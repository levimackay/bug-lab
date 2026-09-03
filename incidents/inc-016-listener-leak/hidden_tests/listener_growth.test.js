import { test } from "node:test";
import assert from "node:assert/strict";
import { ticketBus } from "../../src/ticketBus.js";
import { waitForTicketUpdate } from "../../src/waitForTicketUpdate.js";

test("a burst of watches that all time out leaves no listeners behind", async () => {
  const before = ticketBus.listenerCount("ticket:update");
  const waits = Array.from({ length: 500 }, (_, i) => waitForTicketUpdate(`burst-${i}`, 5));
  await Promise.all(waits);
  assert.equal(ticketBus.listenerCount("ticket:update"), before);
});

test("a mix of matched and timed-out watches still cleans up every listener", async () => {
  const before = ticketBus.listenerCount("ticket:update");
  const waits = Array.from({ length: 50 }, (_, i) => waitForTicketUpdate(`mixed-${i}`, 30));
  // Half of the tickets get a real update before the timeout fires.
  for (let i = 0; i < 50; i += 2) {
    ticketBus.emit("ticket:update", { ticketId: `mixed-${i}`, status: "escalated" });
  }
  await Promise.all(waits);
  assert.equal(ticketBus.listenerCount("ticket:update"), before);
});
