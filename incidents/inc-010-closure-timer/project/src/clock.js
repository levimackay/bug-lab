// A virtual clock for the scheduler. Production runs on real wall-clock
// time; this lets the scheduler (and its tests) advance time deterministically
// instead of racing real timers, and the shop floor dashboard replays a
// day's schedule against it for planning without waiting for it to happen.
export class VirtualClock {
  constructor() {
    this._now = 0;
    this._queue = [];
  }

  now() {
    return this._now;
  }

  setTimeout(callback, delayMs) {
    const entry = { at: this._now + delayMs, callback };
    this._queue.push(entry);
    return entry;
  }

  // Fires every callback due at or before `time`, earliest first; callbacks
  // scheduled for the same instant fire in the order they were registered.
  advanceTo(time) {
    this._now = time;
    const due = this._queue.filter((e) => e.at <= time);
    this._queue = this._queue.filter((e) => e.at > time);
    due.sort((a, b) => a.at - b.at);
    for (const e of due) e.callback();
  }

  // Runs the clock forward until every scheduled callback has fired.
  runAll() {
    while (this._queue.length > 0) {
      const next = Math.min(...this._queue.map((e) => e.at));
      this.advanceTo(next);
    }
  }
}
