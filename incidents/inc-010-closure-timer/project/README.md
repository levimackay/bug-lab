# Print Shop Job Scheduler

Schedules a completion notification for each print job against the shop's
clock, so the front-desk dashboard can tell a customer their job is ready the
moment it finishes. Runs on a virtual clock so a day's schedule can be
replayed instantly instead of waiting real minutes for jobs to finish.

    node src/main.js     # schedule and run today's print queue
    node --test           # run the test suite

`JobScheduler.scheduleAll(jobs)` registers one completion callback per job on
the clock; `clock.runAll()` fires them in delay order. Completed jobs collect
in `scheduler.completed`.
