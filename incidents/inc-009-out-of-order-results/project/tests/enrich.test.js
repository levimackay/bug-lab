import { test } from "node:test";
import assert from "node:assert/strict";
import { enrichOrders } from "../src/enrich.js";

test("enrichOrders on an empty batch returns an empty, complete summary", async () => {
  const summary = await enrichOrders([]);
  assert.deepEqual(summary, { results: [], enriched: 0, total: 0 });
});
