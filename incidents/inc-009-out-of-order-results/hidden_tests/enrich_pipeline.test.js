import { test } from "node:test";
import assert from "node:assert/strict";
import { enrichOrders } from "../../src/enrich.js";
import { ORDERS } from "../../src/orders.js";

test("enrichOrders enriches every order in the batch exactly once", async () => {
  const summary = await enrichOrders(ORDERS);
  assert.equal(summary.enriched, ORDERS.length);
  assert.equal(summary.results.length, ORDERS.length);
});

test("results line up with the orders that were submitted, in submission order", async () => {
  const summary = await enrichOrders(ORDERS);
  const gotIds = summary.results.map((r) => r.orderId);
  const wantIds = ORDERS.map((o) => o.id);
  assert.deepEqual(gotIds, wantIds);
});

test("each result carries the tier and shipping name for its own order, not another one's", async () => {
  const summary = await enrichOrders(ORDERS);
  const byId = new Map(summary.results.map((r) => [r.orderId, r]));
  assert.equal(byId.get("ord-3001").tier, "gold");
  assert.equal(byId.get("ord-3001").shipTo, "Priya Natarajan");
  assert.equal(byId.get("ord-3006").tier, "bronze");
  assert.equal(byId.get("ord-3006").shipTo, "Callum Reyes");
});
