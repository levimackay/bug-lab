// Schedules a completion notification for each print job against the shop's
// clock, so the dashboard can announce a job the moment it finishes.
export class JobScheduler {
  constructor(clock) {
    this.clock = clock;
    this.completed = [];
  }

  scheduleAll(jobs) {
    for (var i = 0; i < jobs.length; i++) {
      var job = jobs[i];
      this.clock.setTimeout(() => {
        this.completed.push({ id: job.id, name: job.name, printer: job.printer, ranAt: this.clock.now() });
      }, job.delayMs);
    }
  }
}
