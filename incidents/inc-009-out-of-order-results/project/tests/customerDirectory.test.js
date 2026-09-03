import { test } from "node:test";
import assert from "node:assert/strict";
import { lookupCustomer } from "../src/customerDirectory.js";

test("lookupCustomer resolves known customers with tier and name", async () => {
  const customer = await lookupCustomer("cus_1001");
  assert.equal(customer.tier, "gold");
  assert.equal(customer.name, "Priya Natarajan");
});

test("lookupCustomer rejects unknown customers", async () => {
  await assert.rejects(() => lookupCustomer("cus_9999"), /unknown customer/);
});
