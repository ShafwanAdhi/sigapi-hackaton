import fs from 'node:fs';
const root=process.env.OPENCLAW_STATE_DIR??'/gateway/state';
fs.mkdirSync(root,{recursive:true,mode:0o700});
const file=root+'/openclaw.json';
const team=(process.env.SIGAPI_TEST_SENDERS??'').split(',').filter(Boolean);
const outbound=(process.env.SIGAPI_OUTBOUND_RECIPIENTS??'').split(',').filter(Boolean);
const open=process.env.SIGAPI_WHATSAPP_OPEN==='true';
if(!fs.existsSync(file)){
  const config={logging:{level:'warn',consoleLevel:'error',maxFileBytes:2097152},
    gateway:{mode:'local',bind:'loopback',auth:{mode:'token',token:'${OPENCLAW_GATEWAY_TOKEN}'},controlUi:{enabled:false}},
    agents:{defaults:{heartbeat:{every:'0m'}}},
    channels:{whatsapp:{dmPolicy:open?'open':'allowlist',allowFrom:open?['*']:team,groupPolicy:'disabled',selfChatMode:false,pluginHooks:{messageReceived:true}}},
    plugins:{allow:['whatsapp','sigapi-validation-demo'],load:{paths:['/app/openclaw-plugin','/opt/openclaw/node_modules/@openclaw/whatsapp']},
      entries:{whatsapp:{enabled:true},'sigapi-validation-demo':{enabled:true,config:{allowSenders:team,outboundRecipients:outbound,publicMode:true}}}}};
  fs.writeFileSync(file,JSON.stringify(config,null,2),{mode:0o600,flag:'wx'});
  console.log('Gateway configuration created; WhatsApp pairing still required.');
}else console.log('Existing gateway configuration preserved.');
