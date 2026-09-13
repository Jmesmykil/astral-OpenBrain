const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const {EventEmitter} = require("node:events");
const {test} = require("node:test");
const source = fs.readFileSync(path.join(__dirname, "astral_capability.cjs"), "utf8");

function fixture(t, spawnFailure = false) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "openhome-dispatch-"));
  t.after(() => fs.rmSync(root, {recursive:true, force:true}));
  const caps = path.join(root, "local_capabilities");
  for (const name of ["alpha", "beta", "astral", "astral-daemon", "exampleaccount"]) {
    fs.mkdirSync(path.join(caps,name), {recursive:true});
    fs.writeFileSync(path.join(caps,name,"devkit_functions.py"), name.toUpperCase());
  }
  const server = path.join(root, "openhome-node-server");
  fs.mkdirSync(server);
  const calls = [], replies = [], logs = [];
  function spawn(executable,args,options) {
    if (spawnFailure) throw new Error("fixture spawn failure");
    const child = new EventEmitter(); child.stdout=new EventEmitter(); child.stderr=new EventEmitter();
    calls.push({executable,args,options,child}); return child;
  }
  const context={__dirname:server, module:{exports:{}},
    process:{env:{LOCAL_CAPABILITIES_DIR:caps}}, console:{error(...parts){logs.push(parts)}},
    require:name=>name==="node:child_process"?{spawn}:require(name)};
  vm.createContext(context); vm.runInContext(source,context);
  const ws={send:value=>replies.push(JSON.parse(value))};
  return {root,caps,server,calls,replies,logs,ws,run:(payload,socket=ws)=>context.module.exports(socket,payload),
    // A paired install has the turn router beside the dispatcher; the token is its own file.
    pair:(withToken=true)=>{fs.writeFileSync(path.join(server,"astral_turn_router.cjs"),"// router");
      if (withToken) fs.writeFileSync(path.join(server,"token"),"secret");},
    unpair:()=>{for (const f of ["astral_turn_router.cjs","token"]) fs.rmSync(path.join(server,f),{force:true})},
    files:()=>fs.readdirSync(root).filter(x=>x.startsWith(".astral-call-"))};
}
const request=(cap="alpha",args=[])=>({capability_name:cap,function_name:"respond",args});
const call=(cap,fn,extra={})=>({capability_name:cap,function_name:fn,args:[],...extra});
const QUIET='{"success":true,"spoken_response":"","data":{},"error":null}';
const ALIASES=["astral","astral-daemon","exampleaccount"], AUTONOMOUS=["respond_now","due_alerts","heard"];
const SIX=["capability_name","function_name","args","success","output","error"];

test("overlapping abilities read their own source and clean up",t=>{
  const f=fixture(t); f.run(request("alpha",["first"])); f.run(request("beta",["second"]));
  assert.equal(f.calls.length,2); assert.notEqual(f.calls[0].args[1],f.calls[1].args[1]);
  for (const call of f.calls) {
    assert.equal(path.dirname(call.args[1]),f.root);
    assert.equal(call.options.timeout,15000);
    call.child.stdout.emit("data",fs.readFileSync(call.args[1])); call.child.emit("close",0);
  }
  assert.deepEqual(f.replies.map(r=>r.data.output),["ALPHA","BETA"]);
  assert.deepEqual(f.files(),[]);
});
test("traversal and malformed requests fail without spawning",t=>{
  const f=fixture(t);
  for (const payload of [request("../escape"),request("/absolute"),request("a/b"),request("alpha",{}),
    request("alpha",[{}]),{capability_name:"alpha",function_name:"bad;name"},null,{}]) {
    f.run(payload); assert.equal(f.replies.at(-1).data.success,false);
  }
  assert.equal(f.calls.length,0); assert.deepEqual(f.files(),[]);
});
test("symlink outside capability tree is refused",t=>{
  const f=fixture(t); const p=path.join(f.caps,"alpha/devkit_functions.py");
  fs.writeFileSync(path.join(f.root,"outside.py"),"OUTSIDE"); fs.unlinkSync(p);
  fs.symlinkSync(path.join(f.root,"outside.py"),p);f.run(request());
  assert.equal(f.calls.length,0); assert.equal(f.replies[0].data.success,false);
});
test("missing capability returns a failure",t=>{
  const f=fixture(t);f.run(request("missing"));assert.equal(f.replies[0].data.success,false);
});
test("normal silent decline remains successful",t=>{
  const f=fixture(t);f.run(request());f.calls[0].child.emit("close",0);
  assert.equal(f.replies[0].data.success,true);assert.equal(f.replies[0].data.output,null);
});
test("child error then close sends one response and cleans up",t=>{
  const f=fixture(t);f.run(request());const c=f.calls[0].child;
  c.emit("error",new Error("fixture error"));c.emit("close",1);
  assert.equal(f.replies.length,1);assert.equal(f.replies[0].data.success,false);assert.deepEqual(f.files(),[]);
});
test("synchronous spawn failure cleans up",t=>{
  const f=fixture(t,true);f.run(request());assert.equal(f.replies[0].data.success,false);assert.deepEqual(f.files(),[]);
});
test("timeout signal and stderr remain failures",t=>{
  const f=fixture(t);f.run(request());f.calls[0].child.emit("close",null,"SIGTERM");
  assert.equal(f.replies[0].data.success,false);assert.match(f.replies[0].data.error,/SIGTERM/);
  f.run(request());f.calls[1].child.stderr.emit("data","failed dependency");f.calls[1].child.emit("close",1);
  assert.equal(f.replies[1].data.error,"failed dependency");assert.deepEqual(f.files(),[]);
});

// --- Paired-install boundary: autonomous daemon functions never reach the shim ---
test("paired install declines every autonomous function for every daemon alias with the exact quiet reply",t=>{
  const f=fixture(t);f.pair();
  for (const alias of ALIASES) for (const fn of AUTONOMOUS) {
    f.run(call(alias,fn,{args:["7 plus 10","extra"]}));
    const reply=f.replies.at(-1);
    assert.equal(reply.type,"devkit-capability-result");
    assert.deepEqual(Object.keys(reply.data),SIX);
    assert.equal(reply.data.success,true,alias+"/"+fn+" outer success");
    assert.equal(reply.data.output,QUIET,alias+"/"+fn+" exact quiet output");
    assert.equal(reply.data.error,null);
    assert.equal("_astral" in reply,false,"no correlation is invented for a legacy request");
    // What the daemon's health predicates will parse: success true, empty answer, no offer.
    const parsed=JSON.parse(reply.data.output);
    assert.deepEqual(parsed,{success:true,spoken_response:"",data:{},error:null});
    assert.equal(parsed.data.offer,undefined);
    const log=f.logs.at(-1);
    assert.ok(log.some(p=>String(p).includes("Declined")));
    assert.deepEqual(log.slice(1),[alias,fn],"alias and function are logged");
    assert.ok(!JSON.stringify(log).includes("7 plus 10"),"args are never logged");
  }
  assert.equal(f.replies.length,9);assert.equal(f.calls.length,0,"no spawn");assert.deepEqual(f.files(),[],"no request file");
});
test("paired install keeps foreground functions of the same alias spawning unchanged",t=>{
  const f=fixture(t);f.pair();
  const foreground=["respond","route_answer","health","telemetry","device_control"];
  for (const fn of foreground) f.run(call("astral",fn,{args:["question"]}));
  assert.equal(f.calls.length,foreground.length);
  assert.deepEqual(f.calls.map(c=>c.args[2]),foreground);
  for (const c of f.calls){assert.equal(c.executable,"sudo");assert.equal(c.args[0],"python3");assert.equal(c.args[3],"question");
    assert.equal(fs.readFileSync(c.args[1],"utf8"),"ASTRAL");c.child.stdout.emit("data","ok");c.child.emit("close",0);}
  assert.deepEqual(f.replies.map(r=>r.data.output),["ok","ok","ok","ok","ok"]);assert.deepEqual(f.files(),[]);
  assert.equal(f.logs.filter(l=>String(l[0]).includes("Declined")).length,0);
});
test("standalone install without the router file runs respond_now unchanged",t=>{
  const f=fixture(t);
  for (const alias of ALIASES) f.run(call(alias,"respond_now",{args:["what time is it"]}));
  assert.equal(f.calls.length,3);assert.deepEqual(f.calls.map(c=>c.args[2]),["respond_now","respond_now","respond_now"]);
  f.calls[0].child.stdout.emit("data",'{"success":true,"spoken_response":"noon"}');f.calls[0].child.emit("close",0);
  assert.equal(f.replies[0].data.output,'{"success":true,"spoken_response":"noon"}');
});
test("the router file is checked per request: pairing and unpairing take effect without a restart, token or not",t=>{
  const f=fixture(t);
  f.run(call("astral","respond_now"));assert.equal(f.calls.length,1,"unpaired: spawns");
  f.pair(false);                                  // router present, its token file missing
  f.run(call("astral","due_alerts"));assert.equal(f.calls.length,1,"paired without token: still declined");
  assert.equal(f.replies.at(-1).data.output,QUIET);
  f.pair(true);
  f.run(call("astral-daemon","heard"));assert.equal(f.calls.length,1,"paired with token: declined");
  fs.rmSync(path.join(f.server,"astral_turn_router.cjs"));   // token left behind, router gone
  f.run(call("astral","respond_now"));assert.equal(f.calls.length,2,"router removed: spawns again");
  f.unpair();f.run(call("exampleaccount","heard"));assert.equal(f.calls.length,3);
  assert.deepEqual(f.files().length,3);
});
test("an unrelated ability using the same function name is not declined on a paired install",t=>{
  const f=fixture(t);f.pair();
  for (const fn of AUTONOMOUS) f.run(call("alpha",fn));
  f.run(call("beta","respond_now"));
  assert.equal(f.calls.length,4,"alias scope is pinned: only the daemon aliases are declined");
  assert.deepEqual(f.calls.map(c=>c.args[2]),["respond_now","due_alerts","heard","respond_now"]);
  assert.equal(f.logs.filter(l=>String(l[0]).includes("Declined")).length,0);
});
test("the decline sits after payload validation: a malformed declined call is still a failure",t=>{
  const f=fixture(t);f.pair();
  for (const payload of [call("astral","respond_now",{args:[{}]}),{capability_name:"astral",function_name:"respond_now;x"},
    call("astral","respond_now",{_astral:"nope"})]) {
    f.run(payload);assert.equal(f.replies.at(-1).data.success,false);assert.notEqual(f.replies.at(-1).data.output,QUIET);
  }
  assert.equal(f.calls.length,0);assert.deepEqual(f.files(),[]);
});

// --- Correlation: local-only metadata is validated, echoed at top level, never mixed into data ---
test("valid correlation is echoed as top-level _astral while the data result keeps its six fields",t=>{
  const f=fixture(t);const meta={request_id:"11111111-1111-4111-8111-111111111111",turn_id:"22222222-2222-4222-8222-222222222222"};
  f.run(call("alpha","respond",{args:["q"],_astral:{...meta,extra:"ignored"}}));
  assert.equal(f.calls.length,1);assert.deepEqual([...f.calls[0].args.slice(2)],["respond","q"],"metadata never reaches the child");
  f.calls[0].child.stdout.emit("data","ANSWER");f.calls[0].child.emit("close",0);
  const reply=f.replies[0];
  assert.deepEqual(reply._astral,meta,"only the two validated ids are echoed");
  assert.deepEqual(Object.keys(reply.data),SIX);assert.equal(reply.data.output,"ANSWER");
  // Failure paths keep the echo too, so the App can settle its pending entry.
  f.run(call("missing","respond",{_astral:meta}));assert.equal(f.replies[1].data.success,false);assert.deepEqual(f.replies[1]._astral,meta);
  f.pair();f.run(call("astral","respond_now",{_astral:meta}));assert.equal(f.replies[2].data.output,QUIET);assert.deepEqual(f.replies[2]._astral,meta);
});
test("legacy requests without correlation keep standalone behavior and gain no _astral",t=>{
  const f=fixture(t);f.run(request("alpha",["x"]));f.calls[0].child.emit("close",0);
  assert.equal("_astral" in f.replies[0],false);assert.deepEqual(Object.keys(f.replies[0]),["type","data"]);
});
test("malformed correlation fails before realpath, copy or spawn",t=>{
  const f=fixture(t);
  const bad=[null,"x",42,[],{},{request_id:"a"},{turn_id:"b"},{request_id:1,turn_id:"b"},{request_id:"a",turn_id:{}},
    {request_id:"",turn_id:"b"},{request_id:"a b",turn_id:"b"},{request_id:"a",turn_id:"b;c"},{request_id:"a".repeat(129),turn_id:"b"}];
  for (const _astral of bad) {
    f.run(call("alpha","respond",{_astral}));const reply=f.replies.at(-1);
    assert.equal(reply.data.success,false,JSON.stringify(_astral));assert.match(reply.data.error,/correlation/);
    assert.equal("_astral" in reply,false,"invalid metadata is not echoed");
  }
  assert.equal(f.calls.length,0);assert.deepEqual(f.files(),[]);
});
test("a result for a closed or failing local socket is discarded without throwing and still cleans up",t=>{
  const f=fixture(t);
  const closed={readyState:3,send(){throw new Error("must not be called")}};
  f.run(request("alpha"),closed);assert.equal(f.calls.length,1);
  assert.doesNotThrow(()=>{f.calls[0].child.stdout.emit("data","late");f.calls[0].child.emit("close",0)});
  assert.deepEqual(f.files(),[],"request file removed even though nobody is listening");
  const throwing={readyState:1,send(){throw new Error("socket write after end")}};
  f.run(request("beta"),throwing);assert.doesNotThrow(()=>f.calls[1].child.emit("close",0));
  f.pair();assert.doesNotThrow(()=>f.run(call("astral","respond_now"),closed));
  assert.equal(f.replies.length,0);assert.ok(f.logs.some(l=>String(l[0]).includes("closed before")));
  assert.ok(f.logs.some(l=>String(l[0]).includes("Could not deliver")));
});
