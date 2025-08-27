const DATA = '#mzt-data';
const CONTAINER = '.mzt-container';
const ARC_CONTAINER = '.mzt-arc-container';
const TIMER = '.mzt-time';
const PAST_TIMERS = '.mzt-timers-past';
const FUTURE_TIMERS = '.mzt-timers-future';

/** @param {number} ms */
function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * @template T
 * @param {string | undefined} data
 * @return {T | null}
 */
function toJson(data) {
  try {
    return JSON.parse(data || '{}');
  } catch (e) {
    console.error(e);
    return null;
  }
}

/**
 * @param {number} duration
 * @return {string}
 */
function formatTimer(duration) {
  const SECONDS = 1_000;
  const MINUTES = 60 * SECONDS;
  const HOURS = 60 * MINUTES;

  const hours = Math.round(duration / HOURS);
  const minutes = Math.round((duration / MINUTES) % 60);
  const seconds = Math.round((duration / SECONDS) % 60);

  return (hours > 0 ? [hours, minutes, seconds] : [minutes, seconds])
    .map((x) => x.toString().padStart(2, '0'))
    .join(':');
}

async function countdown() {
  let now = Date.now();

  /** @type {{ state: 'running' | 'paused' | 'ended'; remainingTime: number; totalRemainingTime: number; currentTimer: number | undefined; pastTimers: number[]; futureTimers: number[] } | null} */
  const timer = toJson(document.querySelector(DATA)?.textContent);

  if (!timer || timer.state === 'ended' || timer.state === 'paused') return;

  let isEnded = false;
  while (!isEnded) {
    await wait(200);
    const newNow = Date.now();
    const ellapsed = newNow - now;

    timer.remainingTime = timer.remainingTime - ellapsed;
    timer.totalRemainingTime = Math.max(timer.totalRemainingTime - ellapsed, 0);

    if (timer.remainingTime <= 0) {
      if (timer.currentTimer) timer.pastTimers.push(timer.currentTimer);
      timer.currentTimer = timer.futureTimers.shift();

      if (!timer.currentTimer) {
        isEnded = true;
      }

      timer.remainingTime = (timer.currentTimer || 0) + timer.remainingTime;

      const lastPastTimer = timer.pastTimers.at(-1);
      if (lastPastTimer) {
        const $li = document.createElement('li');
        $li.classList.add('mzt-timer', 'line-through');
        $li.dataset.timer = String(lastPastTimer);
        $li.innerText = formatTimer(lastPastTimer);

        const $pastTimers = document.querySelector(PAST_TIMERS);
        $pastTimers?.append($li);
      }

      debugger;

      const $futureTimersList = document.querySelector(FUTURE_TIMERS);
      ($futureTimersList?.firstElementChild ?? $futureTimersList?.firstChild)?.remove();
    }

    /** @type {HTMLElement | null} */
    const $timer = document.querySelector(TIMER);
    if ($timer) $timer.innerText = formatTimer(Math.max(timer.remainingTime, 0));

    /** @type {HTMLDivElement | null} */
    const $container = document.querySelector(ARC_CONTAINER);
    $container?.style.setProperty(
      '--progress',
      `${timer.currentTimer ? (timer.remainingTime / timer.currentTimer) * 360 : 0}deg`
    );

    now = newNow;
  }

  // ENDING
  /** @type {HTMLButtonElement | null} */
  const $arcContainer = document.querySelector(ARC_CONTAINER);
  if ($arcContainer) $arcContainer.disabled = true;
  document.querySelector(CONTAINER)?.classList.add('opacity-50');
}

countdown().catch(console.error);
