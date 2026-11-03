import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const unavailable='[UJI] Layanan belum siap; pesan belum tersimpan. Coba lagi setelah operator memeriksa layanan.';
const queued='[UJI] Pesan diamankan di antrean lokal; server belum mengonfirmasi penerimaan. Belum divalidasi.';
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const sender=(e,c)=>c.senderId??e.senderId??e.from;

function atomicJson(file,value) {
  const tmp=file+'.'+crypto.randomUUID()+'.tmp';
  const fd=fs.openSync(tmp,'wx',0o600);
  try {fs.writeFileSync(fd,JSON.stringify(value));fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
  fs.renameSync(tmp,file);
}

export function createIntakeBridge({token,allowSenders,outboundRecipients=[],accounts=['default'],spoolRoot,mediaRoot,
  publicMode=false,backendUrl='http://127.0.0.1:8011',fetchImpl=fetch,sendReply,diagnostic=()=>{}}) {
  if(typeof token!=='string'||token.length<32||(!publicMode&&!allowSenders?.length)||!spoolRoot||!mediaRoot)throw Error('INTAKE_CONFIG_REQUIRED');
  const admittedSender=value=>publicMode ? /^\+[1-9][0-9]{7,14}$/.test(value??'') : allowSenders.includes(value);
  const root=path.resolve(spoolRoot), media=path.resolve(mediaRoot);
  const recipients=[...new Set([...allowSenders,...outboundRecipients])];
  fs.mkdirSync(root,{recursive:true,mode:0o700});
  const identity=(e,c)=>{
    const parts=[c.accountId,sender(e,c),c.messageId??e.messageId];
    return parts.every(x=>typeof x==='string'&&x.length) ? crypto.createHash('sha256').update(JSON.stringify(parts)).digest('hex'):null;
  };
  const allowed=(e,c)=>(c.channelId??e.channel)==='whatsapp'&&accounts.includes(c.accountId)&&admittedSender(sender(e,c));
  const manifest=id=>path.join(root,id,'event.json');
  const read=id=>JSON.parse(fs.readFileSync(manifest(id),'utf8'));
  const entries=()=>fs.readdirSync(root).filter(n=>/^[0-9a-f]{64}$/.test(n)).map(id=>({id,item:read(id)}));
  let flushChain=Promise.resolve();
  function flushOrdered() {
    const task=flushChain.then(async()=>{
      const blocked=new Set();
      for(const {id,item} of entries().sort((a,b)=>(a.item.order??0)-(b.item.order??0))) {
        const owner=JSON.stringify([item.event.account_id,item.event.sender_ref]);
        if(item.receipt||blocked.has(owner))continue;
        try {await forward(id);}catch {blocked.add(owner);diagnostic('INTAKE_RETRY_PENDING');}
      }
    });
    flushChain=task.catch(()=>{});
    return task;
  }
  const request=async(route,body)=>{
    const r=await fetchImpl(backendUrl+'/internal/'+route,{method:'POST',signal:AbortSignal.timeout(5000),
      headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(!r.ok)throw Error('BACKEND_UNAVAILABLE');
    return {status:r.status,value:await r.json()};
  };
  const forwarding=new Map();
  async function forward(id) {
    if(forwarding.has(id))return forwarding.get(id);
    const operation=(async()=>{
      const item=read(id);
      if(item.receipt)return true;
      if(!accounts.includes(item.event.account_id)||!admittedSender(item.event.sender_ref))return false;
      if(publicMode&&!item.admitted) {
        await request('admission',{account_id:item.event.account_id,sender_ref:item.event.sender_ref,provider_message_id:item.event.provider_message_id});
        item.admitted=true;atomicJson(manifest(id),item);
      }
      for(const file of item.files) {
        if(file.id)continue;
        if(!/^[0-9]+\.bin$/.test(file.file)||!['image','video'].includes(file.kind))throw Error('INVALID_SPOOL');
        const response=await fetchImpl(backendUrl+'/internal/media',{
          method:'POST',signal:AbortSignal.timeout(10000),headers:{Authorization:`Bearer ${token}`,
            'Content-Type':file.contentType??'application/octet-stream','X-Account-Id':item.event.account_id,
            'X-Sender-Ref':item.event.sender_ref,'X-Provider-Message-Id':item.event.provider_message_id,
            'X-Media-Slot':String(file.slot),'X-Media-Kind':file.kind},
          body:fs.readFileSync(path.join(root,id,file.file))});
        if(!response.ok)throw Error('MEDIA_UPLOAD_FAILED');
        const result=await response.json();
        if(!uuid.test(result.id??''))throw Error('INVALID_MEDIA_RECEIPT');
        file.id=result.id;atomicJson(manifest(id),item);
      }
      const payload={...item.event,media_refs:item.files.map(f=>({id:f.id}))};
      const {status,value}=await request('whatsapp/events',payload);
      if(status!==202||value.mode!=='intake'||value.persistent_intake!==true||!uuid.test(value.receipt_id??''))throw Error('INVALID_RECEIPT');
      item.receipt=value.receipt_id;atomicJson(manifest(id),item);
      // Backend has committed the receipt and owns independent media copies.
      for(const file of item.files)fs.rmSync(path.join(root,id,file.file),{force:true});
      return true;
    })();
    forwarding.set(id,operation);
    try{return await operation;}finally{forwarding.delete(id);}
  }
  const bridge={
    received(e,c) {
      if(!allowed(e,c)||e.isGroup||e.metadata?.fromMe||c.conversationId?.endsWith('@g.us'))return;
      const id=identity(e,c);
      if(!id||fs.existsSync(manifest(id)))return;
      let staging;
      try {
        if(typeof (e.content??'')!=='string'||[...(e.content??'')].length>4000||
           typeof c.conversationId!=='string'||!c.conversationId.length)throw Error('INVALID_ENVELOPE');
        if(e.location&&(!Number.isFinite(e.location.latitude)||Math.abs(e.location.latitude)>90||
          !Number.isFinite(e.location.longitude)||Math.abs(e.location.longitude)>180))throw Error('INVALID_LOCATION');
        const pending=fs.readdirSync(root).filter(n=>/^[0-9a-f]{64}$/.test(n));
        let bytes=0,count=0;
        for(const name of pending) {
          const old=read(name);if(old.receipt)continue;count++;
          for(const file of old.files)if(/^[0-9]+\.bin$/.test(file.file))bytes+=fs.statSync(path.join(root,name,file.file)).size;
        }
        if(count>=500)throw Error('SPOOL_LIMIT');
        const files=[];
        for(const source of (e.media??[])) {
          const kind=source.kind??(source.contentType?.startsWith('image/')?'image':source.contentType?.startsWith('video/')?'video':null);
          if(!['image','video'].includes(kind)||!source.path){diagnostic('MEDIA_NOT_STAGED');continue;}
          const actual=fs.realpathSync(source.path), allowedRoot=fs.realpathSync(media);
          const relative=path.relative(allowedRoot,actual);
          if(!relative||relative.startsWith('..')||path.isAbsolute(relative))throw Error('MEDIA_OUTSIDE_ROOT');
          const stat=fs.statSync(actual);
          if(!stat.isFile()||stat.size>(kind==='image'?10:20)*1024*1024||files.length>=10)throw Error('MEDIA_LIMIT');
          bytes+=stat.size;if(bytes>256*1024*1024)throw Error('SPOOL_LIMIT');
          files.push({source:actual,kind,slot:files.length,file:files.length+'.bin',contentType:source.contentType});
        }
        staging=path.join(root,'.tmp-'+crypto.randomUUID());fs.mkdirSync(staging,{mode:0o700});
        for(const file of files) {
          const fd=fs.openSync(path.join(staging,file.file),'wx',0o600);
          try{fs.writeFileSync(fd,fs.readFileSync(file.source));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
          delete file.source;
        }
        const order=Math.max(Date.now(),...entries().map(x=>(x.item.order??0)+1));
        const item={order,event:{account_id:c.accountId,provider_message_id:c.messageId??e.messageId,
          sender_ref:sender(e,c),conversation_id:c.conversationId,received_at:new Date().toISOString(),
          text:e.content??'',from_me:false,
          location:e.location?{latitude:e.location.latitude,longitude:e.location.longitude}:null},files};
        atomicJson(path.join(staging,'event.json'),item);fs.renameSync(staging,path.join(root,id));
      } catch {diagnostic('SPOOL_FAILED');}
    },
    async dispatch(e,c) {
      if((c.channelId??e.channel)!=='whatsapp')return undefined;
      if(!allowed(e,c)||e.isGroup)return {handled:true};
      const id=identity(e,c);
      if(!id||!fs.existsSync(manifest(id)))return {handled:true,text:unavailable};
      try {await flushOrdered();if(!read(id).receipt)throw Error('PENDING_RECEIPT');return {handled:true};}
      catch {diagnostic('INTAKE_QUEUED');return {handled:true,text:queued};}
    },
    flushSpool:flushOrdered,
    async deliverOne(isCurrent=()=>true) {
      if(!sendReply||!isCurrent())return;
      const {value}=await request('outbox/claim',{accounts,senders:recipients,...(publicMode?{public_reporters:true}:{})});
      const item=value.item;
      if(!item)return;
      if(!accounts.includes(item.account_id)||(publicMode ? item.recipient_authorized!==true||!admittedSender(item.sender_ref) : !recipients.includes(item.sender_ref))||
         typeof item.text!=='string'||item.text.length>1500||!isCurrent())return;
      const start=await request(`outbox/${item.id}/start`,{lease_token:item.lease_token});
      if(!start.value.started||!isCurrent())return;
      if(start.value.text!==undefined)item.text=start.value.text;
      if(typeof item.text!=='string'||item.text.length>1500)return;
      let messageId=null;
      try {
        const result=await sendReply(item);
        if(typeof result?.messageId==='string'&&result.messageId.length&&result.messageId.length<=300&&
           (!result.outcome||result.outcome==='sent'))messageId=result.messageId;
      } catch {diagnostic('OUTBOX_SEND_UNKNOWN');}
      await request(`outbox/${item.id}/finish`,{lease_token:item.lease_token,provider_message_id:messageId});
    },
  };
  return bridge;
}

export function registerIntake(api) {
  const state=process.env.OPENCLAW_STATE_DIR;
  if(!state)throw Error('OPENCLAW_STATE_DIR_REQUIRED');
  let serviceContext, running=false, timer, inflight;
  const bridge=createIntakeBridge({token:process.env.INTERNAL_API_TOKEN,allowSenders:api.pluginConfig?.allowSenders??[],
    publicMode:api.pluginConfig?.publicMode===true,backendUrl:process.env.SIGAPI_INTERNAL_URL??'http://127.0.0.1:8011',
    outboundRecipients:api.pluginConfig?.outboundRecipients??[],
    spoolRoot:path.resolve(state,'../transport-spool'),mediaRoot:path.join(state,'media/inbound'),
    diagnostic:code=>api.logger.warn(`[sigapi] ${code}`),
    sendReply:async item=>{
      const adapter=await api.runtime.channel.outbound.loadAdapter('whatsapp');
      if(!adapter?.sendText)throw Error('WHATSAPP_NOT_READY');
      return adapter.sendText({cfg:serviceContext.config,to:item.sender_ref,text:item.text,accountId:item.account_id});
    }});
  api.on('message_received',bridge.received);
  api.on('before_dispatch',bridge.dispatch);
  let lastHeartbeat=0;
  const tick=()=>{
    if(!running)return;
    inflight=(async()=>{
      try {
        if(Date.now()-lastHeartbeat>30000){
          const response=await fetch((process.env.SIGAPI_INTERNAL_URL??'http://127.0.0.1:8011')+'/internal/heartbeat',{
            method:'POST',headers:{Authorization:'Bearer '+process.env.INTERNAL_API_TOKEN,'Content-Type':'application/json'},
            body:JSON.stringify({service:'gateway'}),signal:AbortSignal.timeout(5000)});
          if(response.ok){lastHeartbeat=Date.now();fs.writeFileSync(path.resolve(state,'../heartbeat'),String(lastHeartbeat),{mode:0o600});}
        }
        await bridge.flushSpool();if(running)await bridge.deliverOne(()=>running);
      }
      catch {api.logger.warn('[sigapi] OUTBOX_OR_BACKEND_UNAVAILABLE');}
      finally {if(running){timer=setTimeout(tick,2000);timer.unref();}}
    })();
  };
  api.registerService({id:'sigapi-intake-outbox',
    start(ctx){serviceContext=ctx;running=true;timer=setTimeout(tick,1000);timer.unref();},
    async stop(){running=false;clearTimeout(timer);await inflight;}});
}
