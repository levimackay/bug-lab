import { recordAttempt } from "./auditLog.ts";

// A fixed-budget token bucket: this window's cap on outbound calls to the
// payments API, shared by every request the client makes concurrently.
// `resetWindow()` is called by the billing-window cron, not exercised here.
export class RateLimiter {
  private readonly clientId: string;
  private readonly capacity: number;
  private tokens: number;

  constructor(clientId: string, capacity: number) {
    this.clientId = clientId;
    this.capacity = capacity;
    this.tokens = capacity;
  }

  async acquire(): Promise<boolean> {
    if (this.tokens <= 0) {
      return false;
    }
    this.tokens -= 1;
    await recordAttempt(this.clientId);
    return true;
  }

  resetWindow(): void {
    this.tokens = this.capacity;
  }

  get remaining(): number {
    return this.tokens;
  }
}
