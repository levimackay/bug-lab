import { test } from "node:test";
import assert from "node:assert/strict";
import { PaymentsApiClient } from "../src/paymentsClient.ts";

test("a single charge under capacity succeeds with a charge id", async () => {
  const client = new PaymentsApiClient("test-client", 2);
  const result = await client.charge("order-1");
  assert.equal(result.status, "charged");
  assert.ok(result.chargeId);
});

test("charges made one at a time stop once capacity is used up", async () => {
  const client = new PaymentsApiClient("test-client", 2);
  const a = await client.charge("order-1");
  const b = await client.charge("order-2");
  const c = await client.charge("order-3");
  assert.equal(a.status, "charged");
  assert.equal(b.status, "charged");
  assert.equal(c.status, "throttled");
});
