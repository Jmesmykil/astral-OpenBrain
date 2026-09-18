// Exact-function harness for the routed agent turn in App.tsx. The named arrow
// functions are lifted out of the component text, their types stripped by Node itself
// (no dependency download), and run against a rig that fakes the two sockets, the
// audio element and the MediaSource. Event order follows the 2026-09-12 receipts.
const fs=require("fs"),vm=require("vm"),assert=require("assert"),{stripTypeScriptTypes}=require("node:module");
process.removeAllListeners("warning");process.on("warning",()=>{});
const appPath=process.env.ASTRAL_APP_TSX||require("path").join(__dirname,"App.tsx");
const source=fs.readFileSync(appPath,"utf8"),text=source.split("\n");
const has=name=>text.some(l=>l.startsWith("  const "+name+" = "));
// The native-boundary helpers exist from v9 on; an older App under ASTRAL_APP_TSX lacks them.
const names=[...["dropNativeRequests","forwardNativeResult"].filter(has),"retireRemoteTransport","initializeAudio","acknowledgeRoutedTurn","handleRoutedTurn","handleSocketClose","handleWebSocketMessage","handleCallInitialization","handleTextMessage","handleErrorMessage","handleMessage","appendToSourceBuffer","processQueue","enqueueAudioMessage","handleAudioMessage","agentTurn","failAgentTurn","loseOwnership","reportAgentTurnIfDone","finishPlayback","endAudioStreamIfReady","playAudioWithRetry","interruptPlayback","detectInterrupt","resetAudioProcessing","emptyBuffer"];
function lift(name){const start=text.findIndex(l=>l.startsWith("  const "+name+" = "));assert(start>=0,"missing "+name);if(/\);$/.test(text[start]))return text[start];let end=start;while(!/^  [})];?$/.test(text[++end]));return text.slice(start,end+1).join("\n")}
const consts=text.filter(l=>/^const (AGENT_SOCKET_RECONNECT|NO_AUDIO_GRACE_MS|NATIVE_REQUEST_TTL_MS|NATIVE_REQUEST_CAP) = /.test(l)).join("\n");
const js=stripTypeScriptTypes(consts+"\n"+names.map(lift).join("\n")+"\nglobalThis.api={"+names.join(",")+"};");
function rig(){
 const ref=v=>({current:v});let sends=[],cloud=[],appended=[],timers=[],opened=[];
 const fire=(l,n)=>{for(const f of [...(l[n]||[])])f()};
 function makeSource(){const l={};const s={updating:false,addEventListener:(n,f)=>(l[n]??=[]).push(f),removeEventListener:(n,f)=>{l[n]=(l[n]||[]).filter(x=>x!==f)},appendBuffer(b){appended.push([...new Uint8Array(b)]);s.updating=true;if(media.readyState==="ended")media.readyState="open";setImmediate(()=>{s.updating=false;fire(l,"updateend")})},abort(){s.updating=false;fire(l,"abort")}};return s}
 const media={readyState:"open",ended:0,endOfStream(){if(media.readyState!=="open")throw new Error("not open");media.readyState="ended";media.ended++},removeSourceBuffer(s){if(s.updating)s.abort()},addSourceBuffer(){if(media.readyState!=="open")throw new Error("not open");return makeSource()}};
 const socket=()=>({readyState:1,send:s=>cloud.push(JSON.parse(s)),close(){this.readyState=3},onopen:null,onmessage:null,onerror:null,onclose:null});
 const c={window:{AudioContext:class {constructor(){this.destination={}}}},navigator:{get mediaDevices(){throw new Error("microphone must not be requested")}},console:{log(){},warn(){},error(){}},Uint8Array,Promise,Error,JSON,Date,WebSocket:{OPEN:1},atob:s=>Buffer.from(s,"base64").toString("binary"),
  setTimeout:(f,ms)=>{timers.push({f,ms});return timers.length},clearTimeout(){},useCallback:f=>f,
  localWebSocketRef:ref({readyState:1,send:s=>sends.push(JSON.parse(s))}),websocketRef:ref(socket()),
  routedTurnRef:ref({id:null,owner:"local"}),pendingRoutedTextRef:ref(null),agentTurnRef:ref(null),nativeRequestsRef:ref(new Map()),callInitializedRef:ref(false),startingMessageComplete:ref(false),reconnectingSocket:ref(false),
  initializeWebSocket:(reconnect)=>{opened.push(reconnect);c.websocketRef.current=socket()},stopped:0,stopRecording(){c.stopped++},isManualClosure:ref(false),reconnectingAudio:{play(){}},
  audioRef:ref({volume:1,pauses:0,pause(){this.pauses++},play(){return Promise.resolve()},currentTime:0,buffered:{length:0}}),
  mediaSourceRef:ref(media),sourceBufferRef:ref(makeSource()),cancelAppendRef:ref(null),processingEpochRef:ref(null),audioEpochRef:ref(0),playedEpochRef:ref(null),audioQueue:ref([]),queuedMessagesRef:ref([]),
  audioContextRef:ref({}),isMusicPausedRef:ref(false),initializeMediaSource:async()=>{},requireNewAudioInitRef:ref(true),isInterruptingRef:ref(false),sentenceCompletedRef:ref(false),startPlayingRef:ref(false),volumeTimerRef:ref(null),
  bot:[],setBotSpeaking(v){c.bot.push(v)},sendLedAction(){},resetInteractiveVolume(){},setUserSpeaking(){},handleDevkitAction(){},handleDevkitMqttAction(){},handleDevkitCapability(){},handleMusicMode(){},handleSleepMode(){},handlePauseAudio(){},handlePlayAudio(){}};
 vm.createContext(c);vm.runInContext(js,c);
 const r={c,sends,cloud,appended,timers,opened,media,
  msg:(type,data)=>c.api.handleWebSocketMessage({data:JSON.stringify({type,data})}),
  flush:async()=>{for(let i=0;i<6;i++)await new Promise(res=>setImmediate(res))},
  played(){c.playedEpochRef.current=c.audioEpochRef.current},
  local:()=>sends.filter(m=>m.type!=="astral-route-ack"),
  turn(id="11111111-1111-4111-8111-111111111111",text="What is two plus two? Answer in one short sentence."){c.api.handleRoutedTurn({type:"astral-router-state",id,owner:"openhome",text,at:Date.now(),expiresAt:Date.now()+120000});return {id,text}},
  async open(t){await r.msg("status","call_initialized");return t},
  async echo(t){await r.msg("message",{role:"user",content:"Interrupted",final:true});await r.msg("message",{role:"user",content:t.text,final:true})},
  async stream(chunks=["AQI="]){await r.msg("text","audio-init");for(const ch of chunks)await r.msg("audio",ch);await r.flush();await r.msg("text","audio-end");await r.flush()},
  async end(){r.played();c.api.finishPlayback()},
  async final(content="Two plus two equals four. "){await r.msg("message",{role:"assistant",content,live:null,final:true})}};
 return r;
}
let results=[];async function test(name,fn){try{await fn();results.push({name,pass:true})}catch(e){results.push({name,pass:false,error:String(e&&e.stack||e)})}}
(async()=>{
await test("unexpected transport close immediately frees pending native capacity",async()=>{
 const r=rig();await r.open(r.turn());
 vm.runInContext(stripTypeScriptTypes(lift("handleDevkitCapability")+"\nglobalThis.requestNative=handleDevkitCapability;"),r.c);
 r.c.requestNative({capability_name:"examplebrain",function_name:"get_uptime",args:[]});
 assert.equal(r.c.nativeRequestsRef.current.size,1);
 r.c.api.handleSocketClose(1006);
 assert.equal(r.c.nativeRequestsRef.current.size,0);
});
// Native boundary rig: the real local-socket lifecycle and capability admission, lifted
// from the App, over a fake local socket that records what Node would receive.
function native(r){const created=[];r.c.configRef={current:null};r.c.setConfig=()=>{};
 r.c.WebSocket=class {static OPEN=1;constructor(url){this.url=url;this.readyState=1;this.sent=[];created.push(this)}send(raw){this.sent.push(JSON.parse(raw))}close(){this.readyState=3}};
 vm.runInContext(stripTypeScriptTypes(lift("initializeLocalWebSocket")+"\n"+lift("handleDevkitCapability")+"\nglobalThis.nativeLifecycle={initializeLocalWebSocket,handleDevkitCapability};"),r.c);
 r.c.nativeLifecycle.initializeLocalWebSocket();const local=created[0];local.onopen();
 const pending=()=>r.c.nativeRequestsRef.current;
 // What the guarded Node dispatcher sends back: the six data fields plus its top-level echo
 // of the validated correlation. `sent` is the request the App handed to the local socket.
 const wire=(sent,over={},meta=sent.data._astral)=>{const {_astral,...data}=sent.data;const result={type:"devkit-capability-result",data:{...data,success:true,output:'{"success":true,"spoken_response":"old answer"}',error:null,...over}};if(meta!==undefined)result._astral=meta;return result};
 const deliver=result=>local.onmessage({data:JSON.stringify(result)});
 const request=(message={capability_name:"examplebrain",function_name:"respond",args:["q"]})=>{const before=local.sent.length;r.c.nativeLifecycle.handleDevkitCapability(message);return local.sent.slice(before).find(x=>x.type==="devkit-capability")};
 return {local,created,pending,wire,deliver,request};}
const T1="11111111-1111-4111-8111-111111111111",T2="22222222-2222-4222-8222-222222222222";
await test("a late native result cannot enter a replacement agent session",async()=>{
 const r=rig(),n=native(r);
 await r.open(r.turn(T1,"Explain a long computation."));
 const sent=n.request({capability_name:"examplebrain",function_name:"respond",args:["old question"]});assert(sent);
 await r.open(r.turn(T2,"A different question."));
 const count=r.cloud.length;
 n.deliver(n.wire(sent));
 assert.equal(r.cloud.length,count,"a native result belongs to the requesting session, not whichever socket is current");
 assert.equal(n.pending().size,0,"the replacement turn cleared the pending request");
});
await test("a native request carries local-only correlation and its same-turn result is forwarded once, stripped",async()=>{
 const r=rig(),n=native(r);await r.open(r.turn(T1));
 const sent=n.request({capability_name:"examplebrain",function_name:"respond",args:["q"],_astral:{request_id:"forged",turn_id:"forged"}});
 assert(sent);assert.deepEqual(Object.keys(sent.data).sort(),["_astral","args","capability_name","function_name"]);
 assert.equal(typeof sent.data._astral.request_id,"string");assert.notEqual(sent.data._astral.request_id,"forged","incoming metadata is replaced, never trusted");
 assert.equal(sent.data._astral.turn_id,T1);assert.equal(n.pending().size,1);
 const entry=n.pending().get(sent.data._astral.request_id);assert.equal(entry.turnId,T1);assert.equal(entry.socket,r.c.websocketRef.current);
 assert.equal(r.timers.at(-1).ms,20000,"entry expires after 20 s");
 const before=r.cloud.length;n.deliver(n.wire(sent,{args:["q"]}));
 assert.equal(r.cloud.length,before+1);const forwarded=r.cloud.at(-1);
 assert.deepEqual(forwarded,{type:"devkit-capability-result",data:{capability_name:"examplebrain",function_name:"respond",args:["q"],success:true,output:'{"success":true,"spoken_response":"old answer"}',error:null}});
 assert(!JSON.stringify(forwarded).includes("_astral"),"local correlation never reaches the cloud");
 assert.equal(n.pending().size,0,"forwarded entries are removed");
 n.deliver(n.wire(sent));assert.equal(r.cloud.length,before+1,"a duplicate result is dropped");
 // Metadata that Node placed inside data (a defensive case) is stripped as well.
 const again=n.request();const inner=n.wire(again);inner.data._astral=again.data._astral;n.deliver(inner);
 assert(!JSON.stringify(r.cloud.at(-1)).includes("_astral"));assert.equal(r.cloud.length,before+2);
});
await test("stale, mismatched, uncorrelated and expired native results are dropped and their entries removed",async()=>{
 const r=rig(),n=native(r);await r.open(r.turn(T1));const before=r.cloud.length;
 const a=n.request();n.deliver(n.wire(a,{},{request_id:a.data._astral.request_id,turn_id:T2}));
 assert.equal(r.cloud.length,before,"mismatched turn id on the current socket");assert.equal(n.pending().size,0);
 const bare=n.wire(n.request());delete bare._astral;n.deliver(bare);assert.equal(r.cloud.length,before,"a result without correlation is never forwarded");
 n.deliver(n.wire(a,{},{request_id:"unknown-id",turn_id:T1}));assert.equal(r.cloud.length,before,"unknown request id");
 n.deliver(n.wire(a,{},"garbage"));n.deliver(n.wire(a,{},{request_id:42,turn_id:T1}));assert.equal(r.cloud.length,before,"malformed correlation");
 n.pending().clear();const b=n.request();r.timers.at(-1).f();assert.equal(n.pending().size,0,"expiry timer removes the entry");
 n.deliver(n.wire(b));assert.equal(r.cloud.length,before,"expired result");
 const c=n.request();n.pending().get(c.data._astral.request_id).expiresAt=Date.now()-1;n.deliver(n.wire(c));
 assert.equal(r.cloud.length,before,"a past deadline is honoured even before the timer fires");assert.equal(n.pending().size,0);
});
await test("a same-turn replacement socket does not receive a result asked through the socket it replaced",async()=>{
 const r=rig(),n=native(r);await r.open(r.turn(T1));const sent=n.request();
 r.c.api.handleSocketClose(1006);r.timers.find(x=>x.ms===5000).f();      // reconnect on the same routed turn
 const before=r.cloud.length;const replacement=r.c.websocketRef.current;assert(replacement);assert.notEqual(replacement,n.pending().get(sent.data._astral.request_id)?.socket);
 n.deliver(n.wire(sent));assert.equal(r.cloud.length,before,"exact socket identity is required");assert.equal(n.pending().size,0);
 const closed=n.request();r.c.websocketRef.current.readyState=3;n.deliver(n.wire(closed));assert.equal(r.cloud.length,before,"a closed socket gets nothing");
});
await test("pending native requests are cleared on completion, local takeover, lease expiry, channel loss and retirement",async()=>{
 for(const how of ["completion","local","lease","channel","retire"]){
  const r=rig(),n=native(r);const t=await r.open(r.turn(T1));await r.echo(t);n.request();n.request();assert.equal(n.pending().size,2,how);
  if(how==="completion"){await r.stream();await r.end();await r.final();}
  else if(how==="local")r.c.api.handleRoutedTurn({type:"astral-router-state",id:T2,owner:"local",text:""});
  else if(how==="lease")r.timers.find(x=>x.ms>=119000).f();
  else if(how==="channel")r.c.api.loseOwnership("ownership channel closed");
  else r.c.api.retireRemoteTransport();
  assert.equal(n.pending().size,0,how+" must clear pending native requests");
 }
});
await test("native admission is refused without a routed owner, at capacity, and when the local socket is dead or failing",async()=>{
 const r=rig(),n=native(r);
 assert.equal(n.request(),undefined,"owner local: nothing reaches Node");assert.equal(n.pending().size,0);assert.deepEqual(r.cloud,[]);
 r.c.routedTurnRef.current={id:T1,owner:"openhome"};r.c.websocketRef.current=null;
 assert.equal(n.request(),undefined,"no remote socket: nothing reaches Node");assert.equal(n.pending().size,0);
 await r.open(r.turn(T1));const before=r.cloud.length;
 for(let i=0;i<8;i++)assert(n.request({capability_name:"examplebrain",function_name:"respond",args:[String(i)]}));
 assert.equal(n.pending().size,8);const ninth=n.request({capability_name:"examplebrain",function_name:"health",args:[]});
 assert.equal(ninth,undefined,"over capacity: no native call");assert.equal(n.pending().size,8,"no pending leak");
 assert.deepEqual(r.cloud.at(-1),{type:"devkit-capability-result",data:{capability_name:"examplebrain",function_name:"health",args:[],success:false,output:null,error:"Too many native requests pending"}});
 assert.equal(r.cloud.length,before+1);
 n.pending().clear();n.local.readyState=3;assert.equal(n.request(),undefined);assert.equal(n.pending().size,0);
 assert.equal(r.cloud.at(-1).data.error,"Local WebSocket not connected");
 n.local.readyState=1;n.local.send=()=>{throw new Error("write after end")};r.c.nativeLifecycle.handleDevkitCapability({capability_name:"examplebrain",function_name:"respond",args:["x"]});
 assert.equal(n.pending().size,0,"a failed send leaves nothing pending");assert.equal(r.cloud.at(-1).data.error,"Local WebSocket send failed");assert.deepEqual(r.cloud.at(-1).data.args,["x"]);
 const bad=n.request(null);assert.equal(bad,undefined);
});
await test("first-render local socket reads later configuration and refreshed agent settings",async()=>{
 const r=rig(),created=[],configEvents=[];r.c.config=null;r.c.configRef={current:null};
 r.c.sleepModeRef={current:false};r.c.setConfig=value=>configEvents.push(value);
 r.c.reconnectedAudio={play(){}};r.c.WebSocket=class {static OPEN=1;constructor(url){this.url=url;this.readyState=1;this.sent=[];created.push(this)}send(raw){this.sent.push(JSON.parse(raw))}close(){this.readyState=3}};
 const lifecycle=stripTypeScriptTypes(lift("initializeLocalWebSocket")+"\n"+lift("initializeWebSocket")+"\nglobalThis.lifecycle={initializeLocalWebSocket,initializeWebSocket};");
 vm.runInContext(lifecycle,r.c);
 r.c.lifecycle.initializeLocalWebSocket();const local=created[0];local.onopen();
 const first={WS_URL:"wss://example.invalid",API_KEY:"test-key",DEFAULT_PERSONALITY:"first",MAC_ADDRESS:"test-device"};
 local.onmessage({data:JSON.stringify(first)});
 assert.equal(r.c.config,null,"initial-render closure remains null after setState; only ref is current");
 assert.equal(configEvents.length,1);
 const turn={type:"astral-router-state",id:"11111111-1111-4111-8111-111111111111",owner:"openhome",text:"Hello",expiresAt:Date.now()+120000};
 local.onmessage({data:JSON.stringify(turn)});
 assert.equal(created.length,2,"first routed turn opens remote transport despite original null state");
 created[1].onopen();assert.equal(created[1].sent[0].data.personality_id,"first");
 assert.equal(created[1].sent[0].data.reconnect,true);
 await created[1].onmessage({data:JSON.stringify({type:"status",data:"call_initialized"})});
 assert(local.sent.some(x=>x.type==="astral-route-ack"&&x.id===turn.id&&x.ready));
 local.onmessage({data:JSON.stringify({...first,DEFAULT_PERSONALITY:"second"})});
 local.onmessage({data:JSON.stringify({...turn,id:"22222222-2222-4222-8222-222222222222"})});
 assert.equal(created.length,3);created[2].onopen();assert.equal(created[2].sent[0].data.personality_id,"second");
});
await test("completed turn rejects late audio and closes its remote transport",async()=>{
 const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream(["AQI="]);await r.end();await r.final();
 const count=r.appended.length;const socket=r.c.websocketRef.current;
 await r.stream(["CQo="]);
 assert.equal(r.appended.length,count,"audio arriving after completed playback must not append or speak");
 assert.equal(r.c.routedTurnRef.current.owner,"local");
 assert.equal(r.c.websocketRef.current,null,"completed remote transport is retired");
 assert(socket===null||socket.readyState===3);
});
await test("local takeover, lease expiry and channel loss retire the abandoned transport",async()=>{
 for(const reason of ["local","lease","channel"]){
  const r=rig();const t=await r.open(r.turn());const old=r.c.websocketRef.current;
  if(reason==="local")r.c.api.handleRoutedTurn({owner:"local",id:"22222222-2222-4222-8222-222222222222",text:""});
  else if(reason==="lease")r.timers.find(x=>x.ms>=119000).f();
  else r.c.api.loseOwnership("ownership channel closed");
  assert.equal(old.readyState,3,reason+" must close the abandoned cloud session");
  assert.equal(r.c.websocketRef.current,null,reason+" clears the transport identity");
  assert.equal(r.c.routedTurnRef.current.owner,"local");
 }
});
await test("playback initializes without microphone permission or a capture graph",async()=>{const r=rig();let initialized=0;r.c.initializeMediaSource=async()=>{initialized++};
 assert.equal(await r.c.api.initializeAudio(),true);assert.equal(initialized,1);assert(r.c.audioContextRef.current);assert(!source.includes("getUserMedia("));assert(!source.includes("createScriptProcessor("));});
await test("output initialization failure remains visible and fails closed",async()=>{const r=rig();r.c.initializeMediaSource=async()=>{throw new Error("no output")};assert.equal(await r.c.api.initializeAudio(),false);});
await test("routed turn opens a fresh reconnect:true socket and submits only after call_initialized",async()=>{const r=rig();const old=r.c.websocketRef.current;const t=r.turn();
 assert.deepEqual(r.opened,[true]);assert.equal(old.readyState,3);assert.equal(old.onmessage,null);assert.equal(r.sends.length,0);assert.equal(r.c.callInitializedRef.current,false);
 await r.open(t);assert.deepEqual(r.cloud.map(m=>m.type+":"+m.data),["text:interrupt-event","transcribed:"+t.text]);assert.deepEqual(r.sends.at(-1),{type:"astral-route-ack",id:t.id,ready:true});assert.equal(r.c.agentTurnRef.current.phase,"submitted")});
await test("measured reconnect:true order: echo, audio, audio-end, final -> result then playback end",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);
 assert.equal(r.c.agentTurnRef.current.phase,"answer");await r.stream(["AQI=","AwQ="]);assert.deepEqual(r.appended,[[1,2],[3,4]]);assert.equal(r.media.ended,1);assert(r.cloud.some(m=>m.data==="bot-speaking"));
 await r.end();assert.deepEqual(r.local(),[]);await r.final();
 assert.deepEqual(r.local(),[{type:"astral-route-result",id:t.id,text:"Two plus two equals four. ",final:true},{type:"astral-route-playback",id:t.id,phase:"end"}]);assert.equal(r.c.agentTurnRef.current.phase,"done");
 await r.final("again");await r.end();assert.equal(r.local().length,2,"nothing reported twice")});
await test("the Interrupted echo and a different user line do not open the turn",async()=>{const r=rig();const t=await r.open(r.turn());
 await r.msg("message",{role:"user",content:"Interrupted",final:true});await r.msg("message",{role:"user",content:"what day is it",final:true});assert.equal(r.c.agentTurnRef.current.phase,"submitted");
 await r.stream();assert.deepEqual(r.appended,[]);assert.equal(r.c.requireNewAudioInitRef.current,true);await r.final();assert.deepEqual(r.local(),[]);assert(t)});
await test("measured reconnect:false order: greeting audio and final are skipped, the answer is reported",async()=>{const r=rig();const t=await r.open(r.turn());r.c.agentTurnRef.current.greets=true;await r.echo(t);
 assert.equal(r.c.agentTurnRef.current.phase,"greeting");await r.stream(["AQI=","AwQ="]);assert.deepEqual(r.appended,[],"greeting audio never plays");assert(!r.cloud.some(m=>m.data==="bot-speaking"));
 await r.final("Astral Initialized. ");assert.deepEqual(r.local(),[],"greeting is not the answer");assert.equal(r.c.agentTurnRef.current.phase,"answer");
 await r.stream(["BQY="]);assert.deepEqual(r.appended,[[5,6]]);await r.end();await r.final();
 assert.deepEqual(r.local().map(m=>m.type+":"+(m.text||m.phase)),["astral-route-result:Two plus two equals four. ","astral-route-playback:end"])});
await test("final before the element ends: completion waits for real playback end",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream();await r.final();
 assert.deepEqual(r.local().map(m=>m.type),["astral-route-result"]);await r.end();assert.deepEqual(r.local().map(m=>m.type),["astral-route-result","astral-route-playback"])});
await test("a stall is not an end: no endOfStream and no completion until audio-end and drain",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);
 await r.msg("text","audio-init");await r.msg("audio","AQI=");await r.flush();r.c.api.endAudioStreamIfReady();assert.equal(r.media.ended,0);await r.end();await r.final();
 assert.deepEqual(r.local().map(m=>m.type),["astral-route-result"]);await r.msg("text","audio-end");await r.flush();assert.equal(r.media.ended,1);await r.end();
 assert.deepEqual(r.local().map(m=>m.type),["astral-route-result","astral-route-playback"])});
await test("late chunk after audio-end: endOfStream waits for the append to drain",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.msg("text","audio-init");
 await r.msg("text","audio-end");assert.equal(r.media.ended,1);r.c.api.finishPlayback();assert.equal(r.c.agentTurnRef.current.ended,false,"never played this generation");
 await r.msg("audio","AQI=");assert.equal(r.media.readyState,"open");await r.flush();assert.equal(r.media.ended,2);assert.deepEqual(r.appended,[[1,2]])});
await test("zero audio: the final text is reported, then failed with reason after the grace timer",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.final();
 const grace=r.timers.find(x=>x.ms===8000);assert(grace);grace.f();
 assert.deepEqual(r.local(),[{type:"astral-route-result",id:t.id,text:"Two plus two equals four. ",final:true},{type:"astral-route-playback",id:t.id,phase:"failed",reason:"no audio"}]);
 await r.stream();assert.deepEqual(r.appended,[],"audio after the failure is not played");await r.end();assert.equal(r.local().length,2)});
await test("grace timer is inert once audio arrived",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.final();await r.stream();await r.end();
 r.timers.find(x=>x.ms===8000).f();assert.deepEqual(r.local().map(m=>m.type+":"+(m.phase||"")),["astral-route-result:","astral-route-playback:end"])});
await test("local takeover mid-answer cuts playback, tells the cloud once, and silences late callbacks",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream();
 const pauses=r.c.audioRef.current.pauses;r.c.api.handleRoutedTurn({type:"astral-router-state",id:"22222222-2222-4222-8222-222222222222",owner:"local",text:""});
 assert.equal(r.c.audioRef.current.pauses,pauses+1);assert.equal(r.cloud.filter(m=>m.data==="interrupt-event").length,2,"one at submit, one at takeover");assert.deepEqual(r.sends.at(-1),{type:"astral-route-ack",id:"22222222-2222-4222-8222-222222222222",ready:true});
 assert.equal(r.c.agentTurnRef.current,null);await r.final();await r.end();await r.msg("text","audio-init");await r.msg("audio","AQI=");await r.flush();
 assert.deepEqual(r.local(),[]);assert.deepEqual(r.appended,[[1,2]].slice(0,1),"only the earlier answer chunk");assert(t)});
await test("owner local drops cloud audio and messages but not status",async()=>{const r=rig();await r.msg("message",{role:"assistant",content:"greeting",final:true});await r.msg("text","audio-init");await r.msg("audio","AQI=");await r.flush();
 assert.deepEqual(r.appended,[]);assert.deepEqual(r.local(),[]);await r.msg("status","call_initialized");assert.equal(r.c.callInitializedRef.current,true)});
await test("a turn without text is declined and opens no socket",async()=>{const r=rig();r.c.api.handleRoutedTurn({type:"astral-router-state",id:"33333333-3333-4333-8333-333333333333",owner:"openhome",text:"  "});
 assert.deepEqual(r.sends,[{type:"astral-route-ack",id:"33333333-3333-4333-8333-333333333333",ready:false}]);assert.deepEqual(r.opened,[])});
await test("error-event mid-turn reports transport failure once and stops",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.msg("error-event",{message:"Connection Replaced",close_connection:true});
 assert.deepEqual(r.local(),[{type:"astral-route-playback",id:t.id,phase:"failed",reason:"transport error"}]);assert.equal(r.c.stopped,1);await r.final();await r.end();assert.equal(r.local().length,1)});
await test("unexpected close mid-turn fails the turn; the reconnect timer is guarded by turn and transport",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);r.c.api.handleSocketClose(1006);
 assert.deepEqual(r.local().at(-1),{type:"astral-route-playback",id:t.id,phase:"failed",reason:"transport closed"});const again=r.timers.find(x=>x.ms===5000);assert(again);
 r.c.api.handleRoutedTurn({type:"astral-router-state",id:"44444444-4444-4444-8444-444444444444",owner:"local",text:""});const before=r.opened.length;again.f();assert.equal(r.opened.length,before,"stale reconnect does not reopen")});
await test("lease expiry in the browser returns to local and cuts the cloud",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream();
 const expiry=r.timers.find(x=>x.ms>100000);assert(expiry);expiry.f();assert.equal(r.c.routedTurnRef.current.owner,"local");assert.equal(r.c.agentTurnRef.current,null);assert.equal(r.cloud.filter(m=>m.data==="interrupt-event").length,2);
 await r.final();assert.deepEqual(r.local(),[])});
await test("second sentence after endOfStream still plays",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream(["AQI="]);await r.end();assert.equal(r.media.readyState,"ended");
 await r.stream(["AwQ="]);assert.deepEqual(r.appended,[[1,2],[3,4]]);assert.deepEqual(r.c.queuedMessagesRef.current,[]);assert.equal(r.c.agentTurnRef.current.ended,false);await r.end();await r.final();
 assert.deepEqual(r.local().map(m=>m.type),["astral-route-result","astral-route-playback"])});
await test("ownership channel close during playback cuts output and revokes before any report",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream();r.played();
 assert(/onclose = \(\) => \{[^}]*loseOwnership\("ownership channel closed"\)/.test(source),"local socket onclose calls loseOwnership");
 const audio=r.c.audioRef.current;const order=[];audio.pause=function(){this.pauses++;order.push("pause")};r.c.localWebSocketRef.current.send=s=>{order.push("report:"+JSON.parse(s).phase)};r.c.websocketRef.current.send=s=>{order.push("cloud:"+JSON.parse(s).data)};
 const epoch=r.c.audioEpochRef.current;r.c.api.loseOwnership("ownership channel closed");
 assert.deepEqual(order,["pause","cloud:interrupt-event","report:failed"],"cut, then cloud, then report");assert.equal(r.c.audioEpochRef.current,epoch+1);assert.equal(r.c.routedTurnRef.current.owner,"local");assert.equal(r.c.agentTurnRef.current,null);
 order.length=0;await r.final();await r.msg("text","audio-init");await r.msg("audio","AwQ=");await r.flush();r.c.api.finishPlayback();assert.deepEqual(order,[],"nothing after the channel is gone");assert.deepEqual(r.appended,[[1,2]])});
await test("ownership channel close with the local socket already dead still cuts output",async()=>{const r=rig();const t=await r.open(r.turn());await r.echo(t);await r.stream();
 r.c.localWebSocketRef.current.readyState=3;const pauses=r.c.audioRef.current.pauses;r.c.api.loseOwnership("ownership channel closed");
 assert.equal(r.c.audioRef.current.pauses,pauses+1);assert.equal(r.c.requireNewAudioInitRef.current,true);assert.equal(r.c.routedTurnRef.current.owner,"local");assert(t)});
await test("a context-bearing multi-line payload is echoed and matched as one turn",async()=>{const r=rig();const text="Earlier in this conversation with you:\nUser: the starting number is 23\nYou: 23\nReply only to what the user says now.\nUser: add five to that starting number.";
 const t=await r.open(r.turn("55555555-5555-4555-8555-555555555555",text));assert.deepEqual(r.cloud.at(-1),{type:"transcribed",data:text});
 await r.msg("message",{role:"user",content:"Interrupted",final:true});await r.msg("message",{role:"user",content:"add five to that starting number.",final:true});assert.equal(r.c.agentTurnRef.current.phase,"submitted","a bare-question echo is not this payload");
 await r.msg("message",{role:"user",content:text,final:true});assert.equal(r.c.agentTurnRef.current.phase,"answer");await r.stream();await r.end();await r.final("28.");
 assert.deepEqual(r.local().map(m=>m.type+":"+(m.text||m.phase)),["astral-route-result:28.","astral-route-playback:end"]);assert(t)});
console.log(JSON.stringify({passed:results.filter(x=>x.pass).length,failed:results.filter(x=>!x.pass).length,results},null,2));process.exitCode=results.some(x=>!x.pass)?1:0;
})();
