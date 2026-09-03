import { randomUUID } from "node:crypto";
import { postJson, TimeoutError } from "./httpClient.ts";

export interface OrderInput {
  customerId: string;
  sku: string;
  qty: number;
}

export interface CreateOrderResult {
  orderId: string;
}

// Retries once on a client-side timeout: the Order API is occasionally slow
// to answer even after it has already committed the order, so a bare
// timeout on our end doesn't mean the create failed. Every attempt carries
// the same Idempotency-Key, so a retry that reaches an API which already
// has the order gets the original order back instead of creating a second
// one.
export async function createOrder(baseUrl: string, order: OrderInput): Promise<CreateOrderResult> {
  const idempotencyKey = randomUUID();
  const attempt = () =>
    postJson<CreateOrderResult>(`${baseUrl}/orders`, order, {
      timeoutMs: 100,
      headers: { "Idempotency-Key": idempotencyKey },
    });

  try {
    return await attempt();
  } catch (err) {
    if (err instanceof TimeoutError) {
      return await attempt();
    }
    throw err;
  }
}
