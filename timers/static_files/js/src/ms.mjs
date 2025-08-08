/**
 * @param {string} input
 * @return {number} the duration in milliseconds
 * @example
 * ```
 * ms('00:10:00'); // 600_000
 * ```
 */
export function ms(input) {
  const segments = input.split(':').map(Number);
  const time = {
    SECONDS: 1000,
    MINUTES: 60 * 1000,
    HOURS: 60 * 60 * 1000,
  };

  switch (segments.length) {
    case 3: {
      const [hours, minutes, seconds] = segments;
      return time.HOURS * hours + time.MINUTES * minutes + time.SECONDS * seconds;
    }
    case 2: {
      const [minutes, seconds] = segments;
      return time.MINUTES * minutes + time.SECONDS * seconds;
    }
    case 1: {
      const [seconds] = segments;
      return time.SECONDS * seconds;
    }
    default:
      throw new Error(`Can't parse "${input}"`);
  }
}
