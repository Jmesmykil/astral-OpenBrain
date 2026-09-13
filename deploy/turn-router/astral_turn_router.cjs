"use strict";
// Loopback turn router. The local hub is the only admission authority; this hands ONE
// turn at a time to the single registered browser and records how it ended. A remote
// (openhome) turn is a lease: it ends on playback completion or on a failure — declined,
// unacknowledged, disconnected, reported failed, or expired — and every failure revokes
// the browser's ownership so a late result cannot become the answer.
const http=require("http"),fs=require("fs"),crypto=require("crypto"),path=require("path");
module.exports=function install(wss, options={}) {
 const root=options.root||"/home/openhome/astral-voice/state/turn-router";
 const leaseMs=options.leaseMs??120000;
 // The stock Node service runs as root; the hub runs as the owner of the state
 // directory. Keep private bridge files readable by that same owner after every
 // atomic replacement, rather than silently creating a root-only control plane.
 const stateOwner=fs.statSync(path.dirname(root));
 const own=file=>{if(process.getuid?.()===0)fs.chownSync(file,stateOwner.uid,stateOwner.gid)};
 fs.mkdirSync(root,{recursive:true,mode:0o700});own(root);fs.chmodSync(root,0o700);
 const tokenPath=path.join(root,"token");
 if(!fs.existsSync(tokenPath))fs.writeFileSync(tokenPath,crypto.randomBytes(32).toString("hex"),{mode:0o600,flag:"wx"});
 own(tokenPath);fs.chmodSync(tokenPath,0o600);
 const token=fs.readFileSync(tokenPath,"utf8").trim();
 const clients=new Set(),pending=new Map();let current=null;let response={};let lease=null;
 const resultPath=path.join(root,"response.json");
 const persist=(file,value)=>{const tmp=file+".tmp";fs.writeFileSync(tmp,JSON.stringify(value),{mode:0o600});own(tmp);fs.renameSync(tmp,file)};
 const tell=()=>{for(const w of clients)if(w.readyState===1)try{w.send(JSON.stringify({type:"astral-router-state",...current}))}catch{}};
 // Terminal failure of the current remote turn: ownership returns to local, the browser is
 // told (it cuts playback and the cloud socket), and the hub reads a `failed` record.
 const fail=reason=>{
  if(!current||current.owner!=="openhome"||response.playback_done)return;
  clearTimeout(lease);lease=null;
  current={...current,owner:"local"};
  response={...response,id:current.id,question:current.question,failed:true,reason,at:Date.now()};persist(resultPath,response);
  tell();
 };
 wss.on("connection",ws=>{
  ws.on("close",()=>{if(clients.delete(ws))fail("browser disconnected")});
  ws.on("message",raw=>{
   let m;try{m=JSON.parse(raw.toString())}catch{return}
   if(m.type==="astral-router-register") {clients.add(ws);ws.send(JSON.stringify({type:"astral-router-state",owner:"local",id:null}));return}
   if(!clients.has(ws)||!current||m.id!==current.id)return;
   if(m.type==="astral-route-ack"){
    const p=pending.get(m.id);if(p){pending.delete(m.id);p.ack(m.ready===true)}
    return;
   }
   if(current.owner!=="openhome"||Date.now()>current.expiresAt)return;
   if(m.type==="astral-route-playback"&&m.phase==="end"){clearTimeout(lease);lease=null;response={...response,id:m.id,question:current.question,playback_done:true,at:Date.now()};persist(resultPath,response)}
   else if(m.type==="astral-route-playback"&&m.phase==="failed")fail(typeof m.reason==="string"&&m.reason.length<=200?m.reason:"playback failed");
   else if(m.type==="astral-route-result"&&typeof m.text==="string"&&m.text.length<=16000&&m.final===true){
    response={...response,id:m.id,text:m.text,question:current.question,at:Date.now()};persist(resultPath,response);
   }
  });
 });
 const server=http.createServer((req,res)=>{
  const reply=(status,data)=>{if(!res.writableEnded){res.writeHead(status,{"Content-Type":"application/json"});res.end(JSON.stringify(data))}};
  if(req.headers.authorization!=="Bearer "+token)return reply(403,{ok:false});
  if(req.method==="GET"&&req.url==="/status")return reply(200,{ok:true,connected:[...clients].some(w=>w.readyState===1)});
  if(req.method!=="POST"||req.url!=="/claim"||req.headers["content-type"]!=="application/json")return reply(404,{ok:false});
  let raw="";req.on("data",b=>{raw+=b;if(raw.length>20000){reply(413,{ok:false});req.destroy()}});
  req.on("end",()=>{
   let m;try{m=JSON.parse(raw)}catch{return reply(400,{ok:false})}
   if(!/^[a-f0-9-]{36}$/.test(m.id)||!["local","openhome"].includes(m.owner)||typeof m.text!=="string"||m.text.length>8000)return reply(400,{ok:false});
   const active=[...clients].filter(w=>w.readyState===1);
   if(active.length!==1)return reply(503,{ok:false,reason:active.length?"multiple browser owners":"browser unavailable"});
   // A newer claim supersedes an unacknowledged one: its requester is told so (not
   // "declined", not a timeout), and an openhome turn it had is failed as superseded.
   for(const [id,p] of pending){pending.delete(id);p.cancel()}
   fail("superseded");clearTimeout(lease);lease=null;
   // `text` is what the browser sends (bounded prior agent dialogue + question); `question` is
   // the bare question the hub remembers and speaks about. Never the other way round.
   const question=typeof m.question==="string"&&m.question.length<=8000&&m.question.trim()?m.question:m.text;
   current={id:m.id,owner:m.owner,text:m.text,question,at:Date.now(),expiresAt:Date.now()+leaseMs};response={};
   if(m.owner==="openhome"){lease=setTimeout(()=>{if(current&&current.id===m.id)fail("lease expired")},leaseMs);lease.unref?.()}
   const timer=setTimeout(()=>{pending.delete(m.id);if(current&&current.id===m.id)fail("browser acknowledgement timeout");reply(504,{ok:false,reason:"browser acknowledgement timeout"})},options.ackTimeoutMs??(m.owner==="openhome"?10000:1200));
   pending.set(m.id,{ack:ready=>{clearTimeout(timer);if(!ready&&current&&current.id===m.id)fail("browser declined");reply(ready?200:503,{ok:ready,id:m.id,owner:m.owner,reason:ready?undefined:"browser declined"})},
    cancel:()=>{clearTimeout(timer);reply(503,{ok:false,id:m.id,owner:m.owner,reason:"superseded"})}});
   try{active[0].send(JSON.stringify({type:"astral-router-state",...current}))}catch{pending.delete(m.id);clearTimeout(timer);fail("browser send failed");reply(503,{ok:false,reason:"browser send failed"})}
  });
 });
 server.listen(options.port??3031,"127.0.0.1");return {server,clients,pending};
};
