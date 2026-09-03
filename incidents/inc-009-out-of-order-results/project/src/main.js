import { ORDERS } from "./orders.js";
import { enrichOrders } from "./enrich.js";

function formatSummary({ results, enriched, total }) {
  return [`orders loaded:   ${total}`, `orders enriched: ${enriched}`, `results ready:   ${results.length}`].join("\n");
}

async function main() {
  const summary = await enrichOrders(ORDERS);
  console.log(formatSummary(summary));
  for (const r of summary.results) {
    console.log(`  ${r.orderId} -> ${r.shipTo} (${r.tier})`);
  }
  if (summary.enriched !== summary.total) {
    console.error(`ERROR: enriched ${summary.enriched}/${summary.total} orders, batch incomplete`);
    return 1;
  }
  return 0;
}

main().then((code) => process.exit(code));
