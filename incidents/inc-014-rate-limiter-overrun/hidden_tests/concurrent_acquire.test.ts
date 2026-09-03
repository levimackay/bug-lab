import { test } from "node:test";
import assert from "node:assert/strict";
import { RateLimiter } from "../../src/rateLimiter.ts";
import { PaymentsApiClient } from "../../src/paymentsClient.ts";

test("N concurrent acquire() calls never grant more than the bucket's capacity", async () => {
  const capacity = 5;
  const callers = 20;
  const limiter = new RateLimiter("test-client", capacity);

  // Fire every caller behind the same microtask turn so their check-then-act
  // windows genuinely overlap, the way a retry storm hits the real client.
  const grants = await Promise.all(Array.from({ length: callers }, () => limiter.acquire()));

  const granted = grants.filter(Boolean).length;
  assert.ok(granted <= capacity, `granted ${granted} tokens from a bucket of ${capacity}`);
});

test("a concurrent burst of charges never exceeds the client's window capacity", async () => {
  const capacity = 5;
  const client = new PaymentsApiClient("storefront-01", capacity);
  const orderIds = Array.from({ length: 20 }, (_, i) => `order-${2000 + i}`);

  const results = await Promise.all(orderIds.map((id) => client.charge(id)));
  const charged = results.filter((r) => r.status === "charged");

  assert.ok(charged.length <= capacity, `charged ${charged.length} orders against a capacity of ${capacity}`);
});
