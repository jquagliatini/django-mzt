import * as assert from 'node:assert/strict';
import { describe, it, mock } from 'node:test';
import { setTimeout as wait } from 'node:timers/promises';

import { Timer } from './timer.mjs';

const SECONDS = 1_000;
const MINUTES = 60 * SECONDS;

describe('Timer', () => {
  it('should compute the running state correctly', () => {
    const now = new Date('2025-07-01T10:15:00Z');

    const startedAt = new Date(now);
    startedAt.setTime(startedAt.getTime() - 15 * MINUTES);

    const timer = new Timer({
      startedAt,
      timers: ['00:10:00', '00:25:00', '00:10:00'],
    });

    assert.deepEqual(timer.state(now), {
      state: 'running',
      totalRemainingTimeMs: 30 * MINUTES,
      remainingTimeMs: 20 * MINUTES,
      pastTimers: [10 * MINUTES],
      currentTimer: 25 * MINUTES,
      futureTimers: [10 * MINUTES],
    });
  });

  it('should compute the elapsed time', () => {
    const now = new Date('2025-07-01T10:15:00Z');

    const startedAt = new Date(now);
    startedAt.setTime(startedAt.getTime() - 15 * MINUTES);

    const timer = new Timer({
      startedAt,
      pauses: [{ startedAt: new Date(startedAt.getTime() + 5 * MINUTES), endedAt: null }],
      timers: ['00:10:00', '00:25:00'],
    });

    const elapsedTime = timer.elapsedTime(now);
    assert.equal(elapsedTime, 5 * MINUTES);
  });

  it('should compute the paused state correctly', () => {
    const now = new Date('2025-07-01T10:15:00Z');

    const startedAt = new Date(now);
    startedAt.setTime(startedAt.getTime() - 15 * MINUTES);

    const timer = new Timer({
      startedAt,
      pauses: [{ startedAt: new Date(startedAt.getTime() + 5 * MINUTES), endedAt: null }],
      timers: ['00:10:00', '00:25:00', '00:10:00'],
    });

    assert.deepEqual(timer.state(now), {
      state: 'paused',
      remainingTimeMs: 5 * MINUTES,
      pastTimers: [],
      currentTimer: 10 * MINUTES,
      futureTimers: [25 * MINUTES, 10 * MINUTES],
    });
  });

  it('should tick', async () => {
    let call = mock.fn();
    const timer = new Timer({ startedAt: new Date(), timers: ['00:00:01', '00:00:01'] });

    for (const _ of timer) {
      await wait(100);
      call();
    }

    assert.equal(call.mock.callCount(), 20);
  });
});
