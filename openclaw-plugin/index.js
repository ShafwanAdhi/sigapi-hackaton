import { registerIntake } from './intake.js';

const unavailable = '[UJI] Layanan belum siap; pesan belum tersimpan sebagai laporan. Coba lagi setelah operator memeriksa layanan.';

export function createHandlers({ token, allowSenders, fetchImpl = fetch, diagnostic = () => {} }) {
  if (typeof token !== 'string' || token.length < 32 || !Array.isArray(allowSenders) || !allowSenders.length) {
    throw Error('Configure INTERNAL_API_TOKEN and allowSenders before enabling bridge');
  }
  // ponytail: correlation in memory for smoke only; durable spool replaces this in Task 2.
  const facts = new Map();
  const sender = (event, ctx) => ctx.senderId ?? event.senderId ?? event.from;
  // WhatsApp's observation/dispatch hooks can use different conversation IDs for a DM.
  // Only DMs are dispatched; account + sender + provider message ID identify the input.
  const key = (event, ctx) => {
    const parts = [ctx.channelId ?? event.channel, ctx.accountId, sender(event, ctx), ctx.messageId ?? event.messageId];
    return parts.every(part => typeof part === 'string' && part.length) ? JSON.stringify(parts) : null;
  };
  const failed = reason => {
    diagnostic(reason); // Fixed codes only: no message body, identifiers, token, or exception text.
    return { handled: true, text: unavailable };
  };
  return {
    received(event, ctx) {
      if (ctx.channelId !== 'whatsapp' || !allowSenders.includes(sender(event, ctx))) return;
      const now = Date.now();
      for (const [id, item] of facts) if (now - item.at > 300_000) facts.delete(id);
      if (facts.size >= 1000) facts.delete(facts.keys().next().value);
      const id = key(event, ctx);
      if (id) facts.set(id, { event, conversationId: ctx.conversationId, at: now });
    },
    async dispatch(event, ctx) {
      if ((ctx.channelId ?? event.channel) !== 'whatsapp') return undefined;
      if (event.isGroup || !allowSenders.includes(sender(event, ctx))) return { handled: true };
      try {
        const item = facts.get(key(event, ctx));
        if (!item || Date.now() - item.at > 300_000) return failed('FACTS_NOT_FOUND');
        const source = item.event;
        if (source.metadata?.fromMe === true) return { handled: true };
        const response = await fetchImpl('http://127.0.0.1:8011/internal/whatsapp/events', {
          method: 'POST', signal: AbortSignal.timeout(5000),
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_id: ctx.accountId, provider_message_id: ctx.messageId ?? source.messageId,
            sender_ref: sender(source, ctx), conversation_id: item.conversationId,
            received_at: new Date().toISOString(), text: source.content ?? '', from_me: false,
            location: source.location ? { latitude: source.location.latitude, longitude: source.location.longitude } : null,
            media_refs: (source.media ?? []).map(media => ({
              kind: media.kind ?? 'unknown', content_type: media.contentType ?? null, staged: Boolean(media.path),
            })),
          }),
        });
        if (!response.ok) return failed(`BACKEND_HTTP_${response.status}`);
        const result = await response.json();
        if (result.mode !== 'smoke' || typeof result.reply_text !== 'string' || result.reply_text.length > 1000) {
          return failed('INVALID_BACKEND_RESULT');
        }
        return { handled: true, text: result.reply_text };
      } catch {
        return failed('BACKEND_REQUEST_FAILED');
      }
    },
  };
}

export default {
  id: 'sigapi-validation-demo',
  name: 'SIGAPI persistent intake',
  register(api) {
    registerIntake(api);
  },
};
