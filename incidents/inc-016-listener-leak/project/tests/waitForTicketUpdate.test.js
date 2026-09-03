import { test } from "node:test";
import assert from "node:assert/strict";
import { ticketBus } from "../src/ticketBus.js";
import { waitForTicketUpdate } from "../src/waitForTicketUpdate.js";

test("resolves 'updated' with the matching update when one arrives in time", async () => {
  const wait = waitForTicketUpdate("tic-42", 200);
  ticketBus.emit("ticket:update", { ticketId: "tic-42", status: "resolved" });
  const result = await wait;
  assert.equal(result.status, "updated");
  assert.equal(result.update.status, "resolved");
});

test("ignores updates for other tickets while waiting for its own", async () => {
  const wait = waitForTicketUpdate("tic-7", 200);
  ticketBus.emit("ticket:update", { ticketId: "tic-99", status: "resolved" });
  ticketBus.emit("ticket:update", { ticketId: "tic-7", status: "escalated" });
  const result = await wait;
  assert.equal(result.status, "updated");
  assert.equal(result.update.ticketId, "tic-7");
});

test("resolves 'timeout' when no matching update arrives", async () => {
  const result = await waitForTicketUpdate("tic-lonely", 20);
  assert.equal(result.status, "timeout");
});
