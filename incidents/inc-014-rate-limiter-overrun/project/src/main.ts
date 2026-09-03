import { PaymentsApiClient } from "./paymentsClient.ts";

const CAPACITY = 5;
const ORDER_COUNT = 20;

async function main(): Promise<number> {
  // A checkout-page bug retried every pending order at once instead of one
  // at a time; this reproduces that burst against the payments client.
  const client = new PaymentsApiClient("storefront-01", CAPACITY);
  const orderIds = Array.from({ length: ORDER_COUNT }, (_, i) => `order-${1000 + i}`);

  const results = await Promise.all(orderIds.map((id) => client.charge(id)));
  const charged = results.filter((r) => r.status === "charged");
  const throttled = results.filter((r) => r.status === "throttled");

  console.log(`window capacity: ${CAPACITY}`);
  console.log(`orders attempted: ${ORDER_COUNT}`);
  console.log(`charged:   ${charged.length}`);
  console.log(`throttled: ${throttled.length}`);
  for (const r of charged) {
    console.log(`  ${r.orderId} -> ${r.chargeId}`);
  }

  if (charged.length > CAPACITY) {
    console.error(`ERROR: charged ${charged.length} orders against a window capacity of ${CAPACITY}`);
    return 1;
  }
  return 0;
}

main().then((code) => process.exit(code));
