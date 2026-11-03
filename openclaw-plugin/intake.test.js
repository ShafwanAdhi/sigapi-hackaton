import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createIntakeBridge } from './intake.js';

function setup(t, overrides={}) {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'sigapi-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const mediaRoot=path.join(root,'media');fs.mkdirSync(mediaRoot);
  const options={token:'x'.repeat(32),allowSenders:['team'],accounts:['demo'],
    spoolRoot:path.join(root,'spool'),mediaRoot, ...overrides};
  return {root,options,bridge:createIntakeBridge(options)};
}
const ctx={channelId:'whatsapp',accountId:'demo',senderId:'team',conversationId:'team-chat',messageId:'message-1'};
const event={from:'team',content:'KETERANGAN: Api di hutan',messageId:'message-1'};

test('spool survives restart and lost receipt; replay sends same durable event identity',async t=>{
  const calls=[];
  const {options,bridge}=setup(t,{fetchImpl:async()=>{throw Error('offline');}});
  bridge.received(event,ctx);
  const first=await bridge.dispatch({}, {...ctx,conversationId:'bot-chat'});
  assert.equal(first.handled,true);assert.match(first.text,/antrean lokal/);
  const recovered=createIntakeBridge({...options,fetchImpl:async(url,opts)=>{
    calls.push(JSON.parse(opts.body));
    return {ok:true,status:202,json:async()=>({mode:'intake',persistent_intake:true,receipt_id:'12345678-1234-4234-8234-123456789abc'})};
  }});
  await recovered.flushSpool();await recovered.flushSpool();
  assert.equal(calls.length,1);assert.equal(calls[0].provider_message_id,'message-1');
  assert.equal(calls[0].conversation_id,'team-chat');
});

test('staged media copied before original disappears, no path sent to API',async t=>{
  const requests=[];
  const {options,bridge}=setup(t,{fetchImpl:async(url,opts)=>{
    requests.push({url,body:opts.body});
    return url.endsWith('/media') ? {ok:true,status:201,json:async()=>({id:'12345678-1234-4234-8234-123456789abc'})} :
      {ok:true,status:202,json:async()=>({mode:'intake',persistent_intake:true,receipt_id:'12345678-1234-4234-8234-123456789abd'})};
  }});
  const original=path.join(options.mediaRoot,'photo.jpg');fs.writeFileSync(original,'photo-bytes');
  bridge.received({...event,media:[{kind:'image',path:original,contentType:'image/jpeg'}]},ctx);
  fs.unlinkSync(original);await bridge.dispatch({},ctx);
  assert.equal(requests.length,2);assert.equal(requests[0].body.toString(),'photo-bytes');
  assert.equal(requests[1].body.includes(options.mediaRoot),false);
});

test('unapproved/self/group input silent and outside media root fails closed',async t=>{
  let called=0;
  const {root,bridge}=setup(t,{fetchImpl:async()=>{called++;throw Error();}});
  assert.deepEqual(await bridge.dispatch({}, {...ctx,senderId:'stranger'}),{handled:true});
  bridge.received({...event,metadata:{fromMe:true}},ctx);
  assert.deepEqual(await bridge.dispatch({isGroup:true},ctx),{handled:true});
  const outside=path.join(root,'outside.jpg');fs.writeFileSync(outside,'private');
  bridge.received({...event,media:[{kind:'image',path:outside}]},ctx);
  assert.match((await bridge.dispatch({},ctx)).text,/belum tersimpan/);
  assert.equal(called,0);
});

test('ambiguous outbound send marked unknown and never blindly sent again',async t=>{
  let sent=0, claimed=false;const finishes=[];
  const item={id:'id',lease_token:'lease',account_id:'demo',sender_ref:'team',text:'[UJI] draft'};
  const {bridge}=setup(t,{sendReply:async()=>{sent++;throw Error('timeout');},fetchImpl:async(url,opts)=>{
    let result={};
    if(url.endsWith('/claim')) {result={item:claimed?null:item};claimed=true;}
    if(url.endsWith('/start'))result={started:true};
    if(url.endsWith('/finish')){finishes.push(JSON.parse(opts.body));result={recorded:true};}
    return {ok:true,status:200,json:async()=>result};
  }});
  await bridge.deliverOne();await bridge.deliverOne();
  assert.equal(sent,1);assert.equal(finishes[0].provider_message_id,null);
});

test('restart and later dispatch preserve original receive order',async t=>{
  const calls=[];
  const {options,bridge}=setup(t,{fetchImpl:async()=>{throw Error('offline');}});
  for(let i=0;i<12;i++)bridge.received({...event,content:'message '+i},{...ctx,messageId:'order-'+i});
  const recovered=createIntakeBridge({...options,fetchImpl:async(url,opts)=>{
    calls.push(JSON.parse(opts.body).text);
    return {ok:true,status:202,json:async()=>({mode:'intake',persistent_intake:true,receipt_id:'12345678-1234-4234-8234-123456789abc'})};
  }});
  await recovered.dispatch({}, {...ctx,messageId:'order-11'});
  assert.deepEqual(calls,Array.from({length:12},(_,i)=>'message '+i));
});

test('oversized text rejected before it can block subsequent spool entries',async t=>{
  let calls=0;
  const {bridge}=setup(t,{fetchImpl:async()=>{calls++;throw Error('offline');}});
  bridge.received({...event,content:'x'.repeat(4001)},ctx);
  assert.match((await bridge.dispatch({},ctx)).text,/belum tersimpan/);
  assert.equal(calls,0);
});

test('outbound recipient receives admitted text without becoming inbound sender',async t=>{
  const sent=[];let claims;
  const {bridge}=setup(t,{outboundRecipients:['authority'],sendReply:async item=>{sent.push(item);return {messageId:'receipt'};},fetchImpl:async(url,opts)=>{
    let result={};
    if(url.endsWith('/claim')){claims=JSON.parse(opts.body);result={item:{id:'id',lease_token:'lease',account_id:'demo',sender_ref:'authority',text:'stale'}};}
    if(url.endsWith('/start'))result={started:true,text:'fresh consent checked'};
    return {ok:true,status:200,json:async()=>result};
  }});
  assert.deepEqual(await bridge.dispatch({}, {...ctx,senderId:'authority'}),{handled:true});
  await bridge.deliverOne();
  assert.ok(claims.senders.includes('authority'));
  assert.equal(sent[0].text,'fresh consent checked');
});
