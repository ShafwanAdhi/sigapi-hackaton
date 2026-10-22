import test from 'node:test';
import assert from 'node:assert/strict';
import { createHandlers } from './index.js';

const ctx = { channelId: 'whatsapp', accountId: 'demo', conversationId: 'chat', messageId: 'm1', senderId: 'team' };
const event = { messageId: 'm1', from: 'team', content: 'uji', media: [{ kind: 'image', path: '/private/photo.jpg' }], location: { latitude: -1, longitude: 110 } };

test('rich facts correlated by account, conversation and message, no paths exposed', async () => {
  let sent;
  const handlers = createHandlers({ token: 'x'.repeat(32), allowSenders: ['team'], fetchImpl: async (_, options) => {
    sent = JSON.parse(options.body);
    return { ok: true, json: async () => ({ mode: 'smoke', reply_text: '[UJI] diterima' }) };
  } });
  handlers.received(event, ctx);
  assert.deepEqual(await handlers.dispatch({}, ctx), { handled: true, text: '[UJI] diterima' });
  assert.equal(sent.media_refs.length, 1);
  assert.equal(sent.location.latitude, -1);
  assert.equal(JSON.stringify(sent).includes('/private'), false);
  const missing = await handlers.dispatch({}, { ...ctx, accountId: 'other' });
  assert.equal(missing.handled, true);
  assert.match(missing.text, /belum tersimpan/);
});

test('backend unavailable never falls through to ordinary agent', async () => {
  const handlers = createHandlers({ token: 'x'.repeat(32), allowSenders: ['team'], fetchImpl: async () => { throw Error('private token'); } });
  handlers.received(event, ctx);
  const result = await handlers.dispatch({}, ctx);
  assert.equal(result.handled, true);
  assert.match(result.text, /belum tersimpan/);
  assert.equal(result.text.includes('private token'), false);
});

test('self and unapproved sender silent; another channel unaffected', async () => {
  const handlers = createHandlers({ token: 'x'.repeat(32), allowSenders: ['team'] });
  handlers.received({ ...event, metadata: { fromMe: true } }, ctx);
  assert.deepEqual(await handlers.dispatch({}, ctx), { handled: true });
  assert.deepEqual(await handlers.dispatch({}, { ...ctx, senderId: 'stranger' }), { handled: true });
  assert.equal(await handlers.dispatch({}, { ...ctx, channelId: 'telegram' }), undefined);
});

test('invalid configuration fails closed', () => {
  assert.throws(() => createHandlers({ token: '', allowSenders: ['team'] }));
  assert.throws(() => createHandlers({ token: 'x'.repeat(32), allowSenders: [] }));
});
