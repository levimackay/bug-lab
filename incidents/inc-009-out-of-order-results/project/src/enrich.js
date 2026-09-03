import { lookupCustomer } from "./customerDirectory.js";

// Attaches loyalty tier and shipping name to each order via the Customer
// Directory service, and reports how many orders made it through.
export async function enrichOrders(orders) {
  const results = [];
  let enriched = 0;

  orders.forEach(async (order) => {
    const customer = await lookupCustomer(order.customerId);
    results.push({
      orderId: order.id,
      sku: order.sku,
      qty: order.qty,
      tier: customer.tier,
      shipTo: customer.name,
    });
    enriched++;
  });

  return { results, enriched, total: orders.length };
}
