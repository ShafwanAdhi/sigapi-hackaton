import assert from 'node:assert/strict';
import { test } from 'node:test';
import { confirmationReducer, initialConfirmation } from '../src/features/incidents/confirmation.ts';

test('invalid clears solved and switching back does not restore the claim', () => {
  let state = confirmationReducer(initialConfirmation, { type: 'choice', value: 'valid' });
  state = confirmationReducer(state, { type: 'solved', value: true });
  assert.equal(state.solved, true);
  state = confirmationReducer(state, { type: 'choice', value: 'invalid' });
  assert.equal(state.solved, false);
  state = confirmationReducer(state, { type: 'solved', value: true });
  assert.equal(state.solved, false);
  state = confirmationReducer(state, { type: 'choice', value: 'valid' });
  assert.equal(state.solved, false);
});

test('location transitions preserve observations and never turn a location failure into an invalid answer', () => {
  for (const choice of ['valid', 'invalid'] as const) {
    let state = confirmationReducer(initialConfirmation, { type: 'choice', value: choice });
    state = confirmationReducer(state, { type: 'description', value: 'Pengamatan dari tempat aman.' });
    for (const location of ['requesting', 'denied', 'outside', 'inaccurate', 'ready'] as const) {
      state = confirmationReducer(state, { type: 'location', value: location });
      assert.equal(state.choice, choice);
      assert.equal(state.description, 'Pengamatan dari tempat aman.');
    }
  }
});

test('description is bounded and no initial observation or solved claim is preselected', () => {
  assert.equal(initialConfirmation.choice, null);
  assert.equal(initialConfirmation.solved, false);
  assert.equal(initialConfirmation.location, 'idle');
  assert.equal(confirmationReducer(initialConfirmation, { type: 'description', value: 'a'.repeat(2001) }).description.length, 2000);
});
