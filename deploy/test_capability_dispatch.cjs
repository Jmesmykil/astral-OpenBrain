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
  for (const name of ["alpha", "beta"]) {
    fs.mkdirSync(path.join(caps,name), {recursive:true});
    fs.writeFileSync(path.join(caps,name,"devkit_functions.py"), name.toUpperCase());
  }
  const calls = [], replies = [];
  function spawn(executable,args,options) {
    if (spawnFailure) throw new Error("fixture spawn failure");
    const child = new EventEmitter(); child.stdout=new EventEmitter(); child.stderr=new EventEmitter();
    calls.push({executable,args,options,child}); return child;
  }
  const context={__dirname:path.join(root,"openhome-node-server"), module:{exports:{}},
    process:{env:{LOCAL_CAPABILITIES_DIR:caps}}, console:{error(){}},
    require:name=>name==="node:child_process"?{spawn}:require(name)};
  vm.createContext(context); vm.runInContext(source,context);
  const ws={send:value=>replies.push(JSON.parse(value))};
  return {root,caps,calls,replies,run:payload=>context.module.exports(ws,payload),
    files:()=>fs.readdirSync(root).filter(x=>x.startsWith(".astral-call-"))};
}
const request=(cap="alpha",args=[])=>({capability_name:cap,function_name:"respond",args});

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
