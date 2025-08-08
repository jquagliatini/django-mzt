import { ms } from './ms.mjs';

/**
 * @typedef {{ state: 'ended'; endedAt: Date; pastTimers: number[] }} TimerEnded
 * @typedef {{ state: 'paused'; remainingTimeMs: number; pastTimers: number[]; currentTimer: number; futureTimers: number[] }} TimerPaused
 * @typedef {{ state: 'running'; remainingTimeMs: number; totalRemainingTimeMs: number; pastTimers: number[]; currentTimer: number; futureTimers: number[] }} TimerRunning
 */

/** @implements {Iterable<TimerRunning | TimerPaused | TimerEnded>} */
export class Timer {
  /** @type {number[]} */
  timers;

  /** @type {Date} */
  startedAt;

  /** @type {{ startedAt: Date; endedAt: Date | null }[]} */
  pauses;

  isPaused() {
    return this.pauses.length > 0 && this.pauses.at(-1)?.endedAt == null;
  }

  /** @return {Date | null} */
  endsAt() {
    if (this.isPaused()) return null;

    const pauseTime = this.pauses.reduce(
      (total, { startedAt, endedAt }) => total + ((endedAt?.getTime() ?? 0) - startedAt.getTime()),
      0
    );
    const totalDuration = this.timers.reduce((total, timer) => total + timer, 0);
    const estimatedEnd = new Date(this.startedAt.getTime() + pauseTime + totalDuration);

    return estimatedEnd;
  }

  /** @param {Date} [now=new Date()] */
  isEnded(now = new Date()) {
    const estimatedEnd = this.endsAt();

    if (estimatedEnd == null) return false;
    return estimatedEnd <= now;
  }

  /**
   * @param {Object} props
   * @param {(number | string)[]} [props.timers=[]]
   * @param {Date | string | number} props.startedAt
   * @param {{ startedAt: Date; endedAt: Date | null }[]} [props.pauses=[]]
   */
  constructor(props) {
    this.subscribers = [];

    if (props.startedAt == null) throw new Error(`Missing "startedAt"`);

    this.startedAt = new Date(props.startedAt);
    this.pauses = props.pauses || [];
    this.timers = (props.timers || [])
      .map((x) =>
        typeof x === 'string' ? ms(x) : typeof x === 'number' && Number.isFinite(x) ? x : undefined
      )
      .filter((x) => x != null);
  }

  elapsedTime(now = new Date()) {
    if (this.isPaused()) {
      const totalPauseDuration = this.pauses
        .slice(0, -1)
        .reduce((total, pause) => total + (pause.endedAt?.getTime() ?? 0) - pause.startedAt.getTime(), 0);
      return (this.pauses.at(-1)?.startedAt.getTime() ?? 0) - this.startedAt.getTime() - totalPauseDuration;
    }

    const totalPauseDuration = this.pauses.reduce(
      (total, pause) => total + (pause.endedAt?.getTime() ?? 0) - pause.startedAt.getTime(),
      0
    );
    return now.getTime() - this.startedAt.getTime() - totalPauseDuration;
  }

  /** @return {TimerEnded | TimerPaused | TimerRunning} */
  state(now = new Date()) {
    const endedAt = this.endsAt();
    if (endedAt && endedAt <= now) {
      return { state: 'ended', endedAt, pastTimers: Array.from(this.timers) };
    }

    let remainingTimeMs = 0;
    let currentTimerIndex = 0;

    let duration = this.elapsedTime(now);

    const totalRemainingTimeMs = endedAt
      ? endedAt.getTime() - this.startedAt.getTime() - duration
      : undefined;
    for (; currentTimerIndex < this.timers.length; currentTimerIndex++) {
      const timer = this.timers[currentTimerIndex];

      remainingTimeMs = timer - duration;
      if (remainingTimeMs > 0) {
        break;
      }

      duration = Math.max(duration - timer, 0);
    }

    const pastTimers = this.timers.slice(0, currentTimerIndex);
    const currentTimer = this.timers[currentTimerIndex];
    const futureTimers = this.timers.slice(currentTimerIndex + 1);

    if (this.isPaused() || totalRemainingTimeMs == null) {
      return { state: 'paused', currentTimer, futureTimers, pastTimers, remainingTimeMs };
    }

    return {
      state: 'running',
      remainingTimeMs,
      totalRemainingTimeMs,
      pastTimers,
      currentTimer,
      futureTimers,
    };
  }

  [Symbol.iterator]() {
    const timer = this;
    return {
      next(now = new Date()) {
        const value = timer.state(now);
        return { done: value.state === 'ended', value };
      },
    };
  }
}
