import test from 'node:test';
import assert from 'node:assert/strict';
import { grant } from '../src/save.mjs';
test('SAVE-1: confirmation waits for save success', async () => {
  let release; let confirmed = 0;
  const pending = grant(() => new Promise(resolve => {release = resolve;}), () => confirmed++);
  assert.equal(confirmed, 0);
  release(); await pending; assert.equal(confirmed, 1);
});
test('SAVE-2: save rejection leaves reward unconfirmed', async () => {
  let confirmed = 0;
  await assert.rejects(grant(() => Promise.reject(new Error('disk')), () => confirmed++), /disk/);
  assert.equal(confirmed, 0);
});
