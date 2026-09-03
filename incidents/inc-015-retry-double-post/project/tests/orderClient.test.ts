import { test } from "node:test";
import assert from "node:assert/strict";
import { startOrderApiServer } from "../src/orderApiServer.ts";
import { createOrder } from "../src/orderClient.ts";

test("createOrder against a healthy API creates exactly one order", async () => {
  const server = await startOrderApiServer();
  try {
    const result = await createOrder(server.url, { customerId: "cus_1", sku: "LAMP-9", qty: 1 });
    assert.ok(result.orderId);
    assert.equal(server.orderCount(), 1);
  } finally {
    await server.close();
  }
});

test("createOrder rejects when the API is unreachable", async () => {
  await assert.rejects(() => createOrder("http://127.0.0.1:1", { customerId: "cus_1", sku: "LAMP-9", qty: 1 }));
});
