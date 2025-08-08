// @ts-nocheck

import { ms } from './ms.mjs';
import { Timer } from './timer.mjs';

/* placeholder function for syntax highlighting */
const html = (...args) => String.raw(...args);

function wait(timeMs) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, timeMs);
  });
}

/** @return {HTMLElement} */
function $(node, properties = {}, children = []) {
  if (properties instanceof HTMLElement || Array.isArray(properties)) {
    children = [].concat(properties);
    properties = {};
  }

  return children.reduce((root, child) => {
    root.appendChild(child);
    return root;
  }, Object.assign(document.createElement(node), properties));
}

class TimerComponent extends HTMLElement {
  /** @return {Date} */
  get startedAt() {
    const startedAt = this.getAttribute('startedAt');
    if (!startedAt) throw new Error('Missing attribute "startedAt"');

    const startedAtDate = new Date(startedAt);
    if (!Number.isFinite(startedAtDate.getTime())) throw new Error('Invalid Date provided for "startedAt"');

    return startedAtDate;
  }

  /** @return {number[]} */
  get timers() {
    const timersAttribute = (this.getAttribute('timers') ?? '')
      ?.split(',')
      .map((x) => x.trim())
      .filter(Boolean);
    const parsed = timersAttribute.map(ms);

    return parsed;
  }

  get pauses() {
    let pauses = this.getAttribute('pauses');
    if (!pauses) return [];
    pauses = JSON.parse(pauses);

    if (!Array.isArray(pauses)) return [];
    return pauses
      .filter(
        (p) =>
          typeof p === 'object' &&
          p !== null &&
          'startedAt' in p &&
          typeof p.startedAt === 'string' &&
          ('endedAt' in p ? typeof p.endedAt === 'string' : true)
      )
      .map(({ startedAt, endedAt }) => ({
        startedAt: new Date(startedAt),
        endedAt: endedAt ? new Date(endedAt) : null,
      }))
      .filter(
        ({ startedAt, endedAt }) =>
          Number.isFinite(startedAt.getTime()) && (endedAt ? Number.isFinite(endedAt.getTime()) : true)
      );
  }

  /** @type {HTMLElement} */
  #root;

  #timer;

  /** @return {Timer} */
  get timer() {
    if (!this.#timer) {
      this.#timer = new Timer({
        timers: this.timers,
        pauses: this.pauses,
        startedAt: this.startedAt,
      });
    }

    return this.#timer;
  }

  #formatTime(timeMs) {
    const SECONDS = 60_000;
    const MINUTES = 60 * SECONDS;
    const HOURS = 60 * MINUTES;

    const hours = Math.round(timeMs / HOURS);
    const minutes = Math.round((timeMs - hours * HOURS) / MINUTES);
    const seconds = Math.round((timeMs - minutes * MINUTES - hours * HOURS) / SECONDS);

    return (hours > 0 ? [hours, minutes, seconds] : [minutes, seconds])
      .map((x) => x.toString().padStart(2, '0'))
      .join(':');
  }

  connectedCallback() {
    this.initialRender();
  }

  /** @param {TimerRunning | TimerPaused | TimerEnded} was */
  async render(was) {
    for (const state of this.timer) {
      const $arcContainer = this.#root.querySelector('.arc-container');

      if ((state.state === 'paused' || state.state === 'running') && was.state !== state.state) {
        if ($arcContainer) {
          $arcContainer.innerHTML = html`
            <svg xmlns="http://www.w3.org/2000/svg" class="size-12 shrink-0 grow-0">
              ${state.state === 'paused'
                ? html`
                    <use class="dark:block hidden" href="#icon.pause_filled"></use>
                    <use class="dark:hidden block" href="#icon.pause"></use>
                  `
                : html`
                    <use class="dark:block hidden" href="#icon.play_filled"></use>
                    <use class="dark:hidden block" href="#icon.play"></use>
                  `}
            </svg>
          `;
          was.state = state.state;
        }
      }

      const degs = state.state === 'ended' ? 0 : ((state.remainingTimeMs ?? 0) / state.currentTimer) * 360;
      $arcContainer.style.setProperty('--progress', `${degs}deg`);
      this.#root.querySelector('.time').innerText = this.#formatTime(
        state.state === 'ended' ? 0 : state.remainingTimeMs
      );

      await wait(200);
    }

    const $arcContainer = this.#root.querySelector('.arc-container');
    $arcContainer.disabled = true;
    $arcContainer.classList.remove('cursor-pointer');
    $arcContainer.classList.add('cursor-not-allowed');

    this.#root.classList.add('opacity-50');
  }

  async initialRender() {
    const timerState = this.timer.state();

    let $form = $('form', { method: 'POST', action: '', className: 'relative size-[200px]' }, [
      $(
        'button',
        {
          disabled: timerState.state === 'ended',
          className: `arc-container rounded size-full flex justify-center items-center ${
            timerState.state === 'ended' ? 'cursor-not-allowed' : 'cursor-pointer'
          }`,
          innerHTML: html`
            <svg xmlns="http://www.w3.org/2000/svg" class="size-12 shrink-0 grow-0">
              ${timerState.state === 'paused'
                ? html`
                    <use class="dark:block hidden" href="#icon.pause_filled"></use>
                    <use class="dark:hidden block" href="#icon.pause"></use>
                  `
                : html`
                    <use class="dark:block hidden" href="#icon.play_filled"></use>
                    <use class="dark:hidden block" href="#icon.play"></use>
                  `}
            </svg>
          `,
        },
        [
          $('div', { className: 'arc-bg' }),
          $('div', { className: 'arc absolute top-0 bottom-0 left-0 right-0' }),
        ]
      ),
    ]);

    let $csrfInput = this.querySelector('input[type="hidden"]');
    if ($csrfInput) {
      $form.appendChild($csrfInput.cloneNode());
      $csrfInput.remove();
    }

    const degs =
      timerState.state === 'ended' ? 0 : ((timerState.remainingTimeMs ?? 0) / timerState.currentTimer) * 360;
    const styles = $('style', [
      // prettier-ignore
      document.createTextNode(html`
        .arc-container {
          --progress: ${degs}deg;
          --arc-border-width: 20px;
        }

        .arc {
            width: 200px;
            aspect-ratio: 1;
            padding: var(--arc-border-width);
            border-radius: 50%;
            background: var(--color-red-300);
            --_g:/var(--arc-border-width) var(--arc-border-width) no-repeat radial-gradient(50% 50%,#000 97%,#0000);
            mask: top var(--_g),
              calc(50% + 50%*sin(var(--progress))) calc(50% - 50%*cos(var(--progress))) var(--_g),
              linear-gradient(#0000 0 0) content-box intersect,
              conic-gradient(#000 var(--progress),#0000 0);
        }

        .arc-bg {
          position: absolute;
          top: 0; right: 0; bottom: 0; left: 0;
          width: 200px;
          display: block;
          border: var(--arc-border-width) solid var(--color-gray-100);
          border-radius: 50%;
        }
      `),
    ]);

    const $container = $('div', { className: timerState.state === 'ended' ? 'opacity-50' : '' }, [
      styles,
      $form,
      $('div', {
        innerText: this.#formatTime(timerState.state === 'ended' ? 0 : timerState.remainingTimeMs),
        className: 'mt-4 text-5xl font-black text-center tabular-nums time dark:text-white',
      }),
    ]);

    // FLUSH
    this.appendChild($container);
    this.#root = $container;

    await wait(100);
    this.render(timerState);
  }
}

window.customElements.define('mzt-timer', TimerComponent);
