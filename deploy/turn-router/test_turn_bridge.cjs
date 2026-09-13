const {EventEmitter}=require("events"),fs=require("fs"),os=require("os"),path=require("path"),assert=require("assert"),crypto=require("crypto");
const install=require("./astral_turn_router.cjs");
(async()=>{
const root=fs.mkdtempSync(path.join(os.tmpdir(),"astral-turn-test-")),wss=new EventEmitter();
const router=install(wss,{root,port:0,ackTimeoutMs:80,leaseMs:120});await new Promise(r=>router.server.once("listening",r));
const url="http://127.0.0.1:"+router.server.address().port,token=fs.readFileSync(path.join(root,"token"),"utf8");
let controls=[];const check=(name,ok)=>{assert(ok,name);controls.push(name)};
const record=()=>JSON.parse(fs.readFileSync(path.join(root,"response.json")));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function request(payload,authorized=true){let r=await fetch(url+"/claim",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(authorized?token:"wrong")},body:JSON.stringify(payload)});return {status:r.status,data:await r.json()}}
const turn=(owner="local")=>({id:crypto.randomUUID(),owner,text:"what day is it"});
class Client extends EventEmitter{constructor(){super();this.readyState=1;this.ack=true;this.messages=[]}send(raw){const m=JSON.parse(raw);this.messages.push(m);if(m.id&&this.ack===true)setImmediate(()=>this.emit("message",JSON.stringify({type:"astral-route-ack",id:m.id,ready:true})));if(m.id&&this.ack==="decline")setImmediate(()=>this.emit("message",JSON.stringify({type:"astral-route-ack",id:m.id,ready:false})))}register(){wss.emit("connection",this);this.emit("message",JSON.stringify({type:"astral-router-register"}))}}
const say=(c,m)=>c.emit("message",JSON.stringify(m));
let c;
try{
check("unauthorized claim rejected",(await request(turn(),false)).status===403);
check("missing browser rejected",(await request(turn())).status===503);
c=new Client();c.register();let t=turn();check("local ownership acknowledged",(await request(t)).status===200);
check("arbitrary owner rejected",(await request({...turn(),owner:"everybody"})).status===400);
let extra=new Client();extra.register();check("two browser owners rejected",(await request(turn())).status===503);extra.emit("close");
t=turn("openhome");check("selected agent ownership acknowledged",(await request(t)).status===200);
say(c,{type:"astral-route-result",id:t.id,text:"Saturday",final:true});
check("text alone is not playback completion",!record().playback_done);
say(c,{type:"astral-route-playback",id:t.id,phase:"end"});check("completion carries answer and playback evidence",record().text==="Saturday"&&record().playback_done);
say(c,{type:"astral-route-result",id:crypto.randomUUID(),text:"STALE",final:true});check("foreign turn rejected",record().text==="Saturday");
await sleep(150);check("completed turn is not failed by lease expiry",record().playback_done===true&&!record().failed);
c.ack=false;t=turn("openhome");check("unacknowledged claim times out",(await request(t)).status===504);
check("timeout records a terminal failure",record().id===t.id&&record().failed===true&&record().reason==="browser acknowledgement timeout");
say(c,{type:"astral-route-result",id:t.id,text:"LATE",final:true});check("timeout revokes result authority",record().text===undefined);check("timeout sends local cut",c.messages.at(-1).owner==="local"&&c.messages.at(-1).id===t.id);
c.ack="decline";t=turn("openhome");let declined=await request(t);check("ready:false is refused",declined.status===503&&declined.data.reason==="browser declined");
check("ready:false records a terminal failure",record().id===t.id&&record().failed===true&&record().reason==="browser declined");
say(c,{type:"astral-route-result",id:t.id,text:"LATE2",final:true});say(c,{type:"astral-route-playback",id:t.id,phase:"end"});
check("ready:false revokes late result and playback",record().text===undefined&&!record().playback_done);check("ready:false sends local cut",c.messages.at(-1).owner==="local");
c.ack=true;t=turn("openhome");check("lease turn acknowledged",(await request(t)).status===200);await sleep(150);
check("lease expiry records a terminal failure",record().id===t.id&&record().failed===true&&record().reason==="lease expired");
say(c,{type:"astral-route-result",id:t.id,text:"EXPIRED",final:true});check("expired turn rejects late result",record().text===undefined);check("lease expiry sends local cut",c.messages.at(-1).owner==="local");
t=turn("openhome");check("failed-playback turn acknowledged",(await request(t)).status===200);
say(c,{type:"astral-route-result",id:t.id,text:"four",final:true});say(c,{type:"astral-route-playback",id:t.id,phase:"failed",reason:"no audio"});
check("reported playback failure keeps text with reason",record().failed===true&&record().reason==="no audio"&&record().text==="four");
say(c,{type:"astral-route-playback",id:t.id,phase:"end"});check("failure is terminal: late end ignored",!record().playback_done);
t=turn("openhome");check("disconnect turn acknowledged",(await request(t)).status===200);c.emit("close");
check("browser disconnect records a terminal failure",record().id===t.id&&record().failed===true&&record().reason==="browser disconnected");
check("status reports no browser",(await (await fetch(url+"/status",{headers:{Authorization:"Bearer "+token}})).json()).connected===false);
c=new Client();c.register();
t=turn("openhome");check("superseded turn acknowledged",(await request(t)).status===200);let local=turn();check("local takeover acknowledged",(await request(local)).status===200);
check("superseded remote turn recorded failed",record().id===t.id&&record().failed===true&&record().reason==="superseded");
say(c,{type:"astral-route-result",id:t.id,text:"OLD",final:true});check("superseded result rejected",record().text===undefined);
// Supersession, with an observed barrier instead of a timing guess: a second router whose ACK
// timeout cannot fire during the control, and the new claim is issued only after the browser has
// RECEIVED the old one. A 504 here would be the timeout control, not this one, and is a failure.
{const wss2=new EventEmitter(),root2=fs.mkdtempSync(path.join(os.tmpdir(),"astral-turn-test2-"));
 const r2=install(wss2,{root:root2,port:0,ackTimeoutMs:5000,leaseMs:5000});await new Promise(r=>r2.server.once("listening",r));
 const url2="http://127.0.0.1:"+r2.server.address().port,token2=fs.readFileSync(path.join(root2,"token"),"utf8");
 const request2=payload=>fetch(url2+"/claim",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token2},body:JSON.stringify(payload)}).then(async r=>({status:r.status,data:await r.json()}));
 class Client2 extends Client{register(){wss2.emit("connection",this);this.emit("message",JSON.stringify({type:"astral-router-register"}))}}
 const c2=new Client2();c2.register();c2.ack=false;
 try{
  const old=turn("openhome"),pendingOld=request2(old);
  for(let i=0;i<200&&!c2.messages.some(m=>m.id===old.id);i++)await sleep(5);
  check("old claim observed by the browser before supersession",c2.messages.some(m=>m.id===old.id&&m.owner==="openhome"));
  c2.ack=true;const current=turn();const took=await request2(current);check("new local turn takes over",took.status===200);
  const superseded=await pendingOld;check("superseded claim rejected as superseded",superseded.status===503&&superseded.data.reason==="superseded");
  const rec=JSON.parse(fs.readFileSync(path.join(root2,"response.json")));check("superseded pending remote turn recorded failed",rec.id===old.id&&rec.failed===true&&rec.reason==="superseded");
  const q=turn("openhome");q.question="bare question";q.text="Earlier in this conversation with you:\nUser: a\nYou: b\nUser: bare question";check("context-bearing claim acknowledged",(await request2(q)).status===200);
  c2.emit("message",JSON.stringify({type:"astral-route-result",id:q.id,text:"c",final:true}));c2.emit("message",JSON.stringify({type:"astral-route-playback",id:q.id,phase:"end"}));
  const rq=JSON.parse(fs.readFileSync(path.join(root2,"response.json")));check("record carries the bare question, not the sent context",rq.question==="bare question"&&rq.text==="c"&&rq.playback_done);
 }finally{c2.emit("close");r2.server.closeAllConnections();await new Promise(r=>r2.server.close(r));fs.rmSync(root2,{recursive:true,force:true})}}
console.log(JSON.stringify({passed:controls.length,controls},null,2));
}finally{c?.emit("close");router.server.closeAllConnections();await new Promise(r=>router.server.close(r));fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
