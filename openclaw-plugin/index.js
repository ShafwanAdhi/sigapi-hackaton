const unavailable = '[UJI] Layanan belum siap; pesan belum tersimpan sebagai laporan. Coba lagi setelah operator memeriksa layanan.';

export function createHandlers({ token, allowSenders, fetchImpl = fetch }) {
  if (typeof token !== 'string' || token.length < 32 || !Array.isArray(allowSenders) || !allowSenders.length) {
    throw Error('Configure INTERNAL_API_TOKEN and allowSenders before enabling bridge');
  }
  // ponytail: correlation in memory for smoke only; durable spool replaces this in Task 2.
  const facts = new Map();
  const key = (event, ctx) => JSON.stringify([ctx.accountId, ctx.conversationId, ctx.messageId ?? event.messageId]);
  const sender = (event, ctx) => ctx.senderId ?? event.senderId ?? event.from;
  return {
    received(event, ctx) {
      if (ctx.channelId !== 'whatsapp' || !allowSenders.includes(sender(event, ctx))) return;
      const now = Date.now();
      for (const [id, item] of facts) if (now - item.at > 300_000) facts.delete(id);
      if (facts.size >= 1000) facts.delete(facts.keys().next().value);
      facts.set(key(event, ctx), { event, at: now });
    },
    async dispatch(event, ctx) {
      if ((ctx.channelId ?? event.channel) !== 'whatsapp') return undefined;
      if (event.isGroup || !allowSenders.includes(sender(event, ctx))) return { handled: true };
      try {
        const item = facts.get(key(event, ctx));
        if (!item || Date.now() - item.at > 300_000) return { handled: true, text: unavailable };
        const source = item.event;
        if (source.metadata?.fromMe === true) return { handled: true };
        const response = await fetchImpl('http://127.0.0.1:8011/internal/whatsapp/events', {
          method: 'POST', signal: AbortSignal.timeout(5000),
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_id: ctx.accountId, provider_message_id: ctx.messageId ?? source.messageId,
            sender_ref: sender(source, ctx), conversation_id: ctx.conversationId,
            received_at: new Date().toISOString(), text: source.content ?? '', from_me: false,
            location: source.location ? { latitude: source.location.latitude, longitude: source.location.longitude } : null,
            media_refs: (source.media ?? []).map(media => ({
              kind: media.kind ?? 'unknown', content_type: media.contentType ?? null, staged: Boolean(media.path),
            })),
          }),
        });
        if (!response.ok) return { handled: true, text: unavailable };
        const result = await response.json();
        if (result.mode !== 'smoke' || typeof result.reply_text !== 'string' || result.reply_text.length > 1000) {
          return { handled: true, text: unavailable };
        }
        return { handled: true, text: result.reply_text };
      } catch {
        return { handled: true, text: unavailable };
      }
    },
  };
}

export default {
  id: 'sigapi-validation-demo',
  name: 'SIGAPI validation smoke',
  register(api) {
    const handlers = createHandlers({ token: process.env.INTERNAL_API_TOKEN, allowSenders: api.pluginConfig?.allowSenders });
    api.on('message_received', handlers.received);
    api.on('before_dispatch', handlers.dispatch);
  },
};
