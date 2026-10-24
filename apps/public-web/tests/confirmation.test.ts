import assert from 'node:assert/strict';
import { test } from 'node:test';
import { canPreview, confirmationReducer, initialConfirmation } from '../src/features/incidents/confirmation.ts';

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

test('both choices require an eligible simulated location; rejection is not an invalid vote', () => {
  for (const choice of ['valid', 'invalid'] as const) {
    let state = confirmationReducer(initialConfirmation, { type: 'choice', value: choice });
    assert.equal(canPreview(state), false);
    for (const location of ['denied', 'outside'] as const) {
      state = confirmationReducer(state, { type: 'location', value: location });
      assert.equal(canPreview(state), false);
      assert.equal(state.choice, choice);
      assert.equal(confirmationReducer(state, { type: 'preview' }).previewed, false);
    }
    state = confirmationReducer(state, { type: 'location', value: 'ready' });
    assert.equal(canPreview(state), true);
    assert.equal(confirmationReducer(state, { type: 'preview' }).previewed, true);
  }
});

test('editing invalidates the previous preview and description is bounded', () => {
  const state = { ...initialConfirmation, choice: 'valid' as const, location: 'ready' as const, previewed: true };
  const edited = confirmationReducer(state, { type: 'description', value: 'a'.repeat(2001) });
  assert.equal(edited.previewed, false);
  assert.equal(edited.description.length, 2000);
  assert.equal(confirmationReducer(state, { type: 'edited' }).previewed, false);
});
