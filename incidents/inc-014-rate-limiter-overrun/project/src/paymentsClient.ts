import { RateLimiter } from "./rateLimiter.ts";

export interface ChargeResult {
  orderId: string;
  status: "charged" | "throttled";
  chargeId?: string;
}

// The payments API cuts the connection for a minute if it sees more than
// `capacity` requests in a window, so every outbound charge goes through
// the shared limiter first.
export class PaymentsApiClient {
  private readonly limiter: RateLimiter;
  private nextChargeId = 1;

  constructor(clientId: string, capacity: number) {
    this.limiter = new RateLimiter(clientId, capacity);
  }

  async charge(orderId: string): Promise<ChargeResult> {
    const allowed = await this.limiter.acquire();
    if (!allowed) {
      return { orderId, status: "throttled" };
    }
    const chargeId = `ch_${this.nextChargeId++}`;
    return { orderId, status: "charged", chargeId };
  }

  get remaining(): number {
    return this.limiter.remaining;
  }
}
