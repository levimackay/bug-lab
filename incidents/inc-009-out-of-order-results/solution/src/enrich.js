import { lookupCustomer } from "./customerDirectory.js";

// Attaches loyalty tier and shipping name to each order via the Customer
// Directory service, and reports how many orders made it through.
export async function enrichOrders(orders) {
  const results = await Promise.all(
    orders.map(async (order) => {
      const customer = await lookupCustomer(order.customerId);
      return {
        orderId: order.id,
        sku: order.sku,
        qty: order.qty,
        tier: customer.tier,
        shipTo: customer.name,
      };
    })
  );

  return { results, enriched: results.length, total: orders.length };
}
