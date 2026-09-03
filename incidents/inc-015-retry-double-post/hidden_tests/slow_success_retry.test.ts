import { test } from "node:test";
import assert from "node:assert/strict";
import { startOrderApiServer } from "../../src/orderApiServer.ts";
import { createOrder } from "../../src/orderClient.ts";

test("a retry triggered by a slow-but-successful create does not double the order", async () => {
  // 150ms is well past the client's 100ms timeout, so the first attempt's
  // response arrives too late and the client retries.
  const server = await startOrderApiServer({ firstRequestDelayMs: 150 });
  try {
    const result = await createOrder(server.url, { customerId: "cus_2201", sku: "RUG-4", qty: 1 });
    assert.ok(result.orderId, "createOrder should resolve with an order id");
    assert.equal(server.orderCount(), 1, "exactly one order should exist after the retry");
  } finally {
    await server.close();
  }
});
