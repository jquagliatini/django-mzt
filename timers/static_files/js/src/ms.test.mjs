import { it, describe } from 'node:test';
import * as assert from 'node:assert/strict';

import { ms } from './ms.mjs';

const SECONDS = 1_000;
const MINUTES = 60 * SECONDS;
const HOURS = 60 * MINUTES;

describe('ms', () => {
  it('should parse 0:0:10 into 60_000', () => {
    assert.equal(ms('0:0:10'), 10 * SECONDS);
  });

  it('should parse 00:10:00 into 600_000', () => {
    assert.equal(ms('00:10:00'), 10 * MINUTES);
  });

  it('should parse 10:10:10 into 36_610_000', () => {
    assert.equal(ms('10:10:10'), 10 * HOURS + 10 * MINUTES + 10 * SECONDS);
  });

  it('should parse 10:00 into 60_000', () => {
    assert.equal(ms('10:00'), 10 * MINUTES);
  });

  it('should parse 10 into 10_000', () => {
    assert.equal(ms('10'), 10 * SECONDS);
  });
});
