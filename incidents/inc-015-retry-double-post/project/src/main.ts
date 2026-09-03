import { startOrderApiServer } from "./orderApiServer.ts";
import { createOrder } from "./orderClient.ts";

async function main(): Promise<number> {
  // The Order API answered this slowly during this morning's traffic spike;
  // 150ms is past the client's 100ms timeout.
  const server = await startOrderApiServer({ firstRequestDelayMs: 150 });
  try {
    const result = await createOrder(server.url, { customerId: "cus_2201", sku: "RUG-4", qty: 1 });
    console.log(`createOrder resolved with orderId ${result.orderId}`);
    console.log(`orders on server: ${server.orderCount()}`);
    if (server.orderCount() !== 1) {
      console.error(`ERROR: expected exactly 1 order for this checkout, server has ${server.orderCount()}`);
      return 1;
    }
    return 0;
  } finally {
    await server.close();
  }
}

main().then((code) => process.exit(code));
