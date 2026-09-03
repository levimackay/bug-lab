import { EventEmitter } from "node:events";

// The webhook handler publishes every ticket change here; every dashboard
// request waiting on a specific ticket subscribes to it for the duration
// of that wait.
export const ticketBus = new EventEmitter();
