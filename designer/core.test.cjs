/* Run: node designer/core.test.cjs (Node 18+). No dependencies. */
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const sandbox = {};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
for (const file of ["core.js","data.js"]) vm.runInContext(fs.readFileSync(path.join(__dirname,file),"utf8"),sandbox);
function runTests(C,D) {
let count=0;const failures=[];
function test(name,fn){try{fn();count++;}catch(e){failures.push(name+": "+e.message);}}
function ok(v,msg="assertion failed"){if(!v)throw Error(msg);}
function near(a,b,tol=1e-8){ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(b)),a+" != "+b);}
for(const v of [null,undefined,NaN,Infinity,0,-1,1100,1099,1101,9.9e9]) test("reject pressure "+v,()=>ok(!C.pressureState(v).valid));
test("real atmosphere allowed",()=>ok(C.pressureState(800).valid));
test("small positive pressure allowed",()=>ok(C.pressureState(1e-10).valid));
test("pressure conversion",()=>near(C.convertPressure(760,"Torr","mbar"),1013.25));
test("pressure roundtrip",()=>near(C.convertPressure(C.convertPressure(3,"Torr","Pa"),"Pa","Torr"),3));
test("series speed",()=>near(C.series([100,100]),50));
test("blank inputs unresolved",()=>{const r=C.size({gas:"N2"});ok(r.effectiveSpeed===null&&r.pumpdown===null);});
const inputs={gas:"Air",diameterCm:10,lengthCm:100,temperatureK:293.15,pumpSpeed:1000,valveConductance:500,flowSccm:0,leakLoad:1e-7,outgasLoad:1e-5,volumeL:100,initialPressureTorr:1e-5,targetPressureTorr:1e-6,operatingPressureTorr:1e-5};
test("conductance baseline units",()=>near(C.size(inputs).conductance,121));
test("effective speed includes valve loss",()=>near(C.size(inputs).effectiveSpeed,1/(1/1000+1/121+1/500)));
test("mass square root scaling",()=>{const a=C.size({...inputs,gas:"N2"}),b=C.size({...inputs,gas:"He"});near(b.conductance/a.conductance,Math.sqrt(28.0134/4.0026));});
test("temperature scaling",()=>near(C.size({...inputs,temperatureK:1172.6}).conductance,242));
test("sccm chamber throughput reference",()=>near(C.size({...inputs,temperatureK:273.15,flowSccm:1,leakLoad:0,outgasLoad:0}).load,0.012666666666666667));
test("reachable molecular interval",()=>{const r=C.size(inputs);ok(r.pumpdown>0&&r.regime==="Molecular");});
test("continuum interval flagged",()=>ok(C.size({...inputs,operatingPressureTorr:760}).regime==="Continuum"));
test("floor cannot be reached",()=>{const r=C.size({...inputs,targetPressureTorr:1e-12});ok(r.pumpdown===null&&r.notes.some(v=>v.includes("no finite")));});
test("load must be supplied",()=>ok(C.size({...inputs,leakLoad:null}).basePressure===null));
test("single reed cannot prove open",()=>ok(C.gatePosition(false,true)==="NOT_CLOSED"));
test("offline position unknown",()=>ok(C.gatePosition(true,false)==="UNKNOWN"));
const s={busHealthy:true,pressureFresh:true,cryoReady:true,airReady:true,ventClosed:true,roughClosed:true,independentInhibit:true,armed:true,pressureTorr:.001,limitTorr:.01,closedReed:true};
test("complete simulated permissions",()=>ok(C.permissions(s).allowed));
for(const key of ["busHealthy","pressureFresh","cryoReady","airReady","ventClosed","roughClosed","independentInhibit","armed"])test("fail closed on "+key,()=>ok(!C.permissions({...s,[key]:false}).allowed));
for(const p of [1100,9.9e9,null,0,.1])test("reject open pressure "+p,()=>ok(!C.permissions({...s,pressureTorr:p}).allowed));
test("missing reviewed limit blocks",()=>ok(!C.permissions({...s,limitTorr:null}).allowed));
test("open command retains position distinction",()=>{const r=C.stepSimulation({command:false,armed:true},"open",{...s,closedReed:false});ok(r.command&&r.position==="NOT_CLOSED");});
test("bus loss releases and disarms",()=>{const r=C.stepSimulation({command:true,armed:true},"check",{...s,busHealthy:false});ok(!r.command&&!r.armed&&r.position==="UNKNOWN");});
for(const key of ["pressureFresh","cryoReady","airReady","ventClosed","roughClosed","independentInhibit"])test("active command trips on "+key,()=>{const r=C.stepSimulation({command:true,armed:true},"check",{...s,[key]:false});ok(!r.command&&!r.armed);});
test("trip and reconnect never reopen",()=>{const a=C.stepSimulation({command:true,armed:true},"trip",s),b=C.stepSimulation(a,"check",s);ok(!b.command&&!b.armed);});
test("release does not assert closed",()=>{const r=C.stepSimulation({command:true,armed:true},"close",{...s,closedReed:false});ok(!r.command&&r.position==="NOT_CLOSED");});
for(const [key,g] of Object.entries(D.presets))test("preset typed graph "+key,()=>ok(C.validateGraph(g,D.library).length===0));
test("reject 5V to 24V connection",()=>{const g=D.presets.electrical;ok(!!C.connectionError(g,{node:"U1",port:"5V"},{node:"PS1",port:"+24V"},D.library));});
test("reject logic/field returns",()=>{const g=D.presets.electrical;ok(!!C.connectionError(g,{node:"U1",port:"GND"},{node:"PS1",port:"0V"},D.library));});
test("reject air to helium connection",()=>{const g=D.presets.process;ok(!!C.connectionError(g,{node:"AIR1",port:"out"},{node:"HE1",port:"He supply"},D.library));});
test("reject duplicate link",()=>{const g=D.presets.process,e=g.edges[0];ok(!!C.connectionError(g,e.a,e.b,D.library));});
test("reject missing port",()=>{const g=D.presets.process;ok(!!C.connectionError(g,{node:"CH1",port:"missing"},{node:"G1",port:"chamber"},D.library));});
test("CSV masks flags and gaps",()=>{const rows=C.parseCsv("t_s,CG1_Torr,CG2_Torr\n0,1100,0.01\n1,9.9E9,\n2,1e-4,2e-4");ok(rows.length===3&&rows[0].CG1_Torr===null&&rows[1].CG1_Torr===null&&rows[1].CG2_Torr===null&&rows[2].CG1_Torr===1e-4);});
test("CSV invalid schema rejected",()=>{let thrown=false;try{C.parseCsv("x,y\n1,2");}catch{thrown=true;}ok(thrown);});
test("sanitize roundtrip",()=>{const r=C.sanitizeProject({schema:"vacuum-workbench/v1",name:"Test",graph:D.presets.process,inputs},D.library);ok(r.graph.nodes.length===D.presets.process.nodes.length&&r.inputs.gas==="Air");});
test("bad imported port rejected",()=>{let thrown=false;const g=JSON.parse(JSON.stringify(D.presets.process));g.edges[0].a.port="fake";try{C.sanitizeProject({schema:"vacuum-workbench/v1",graph:g},D.library);}catch{thrown=true;}ok(thrown);});
test("import duplicate node rejected",()=>{let thrown=false;const g=JSON.parse(JSON.stringify(D.presets.process));g.nodes.push(g.nodes[0]);try{C.sanitizeProject({schema:"vacuum-workbench/v1",graph:g},D.library);}catch{thrown=true;}ok(thrown);});
test("empty numeric inputs remain null",()=>{const r=C.sanitizeProject({schema:"vacuum-workbench/v1",graph:D.presets.process,inputs:{flowSccm:"",leakLoad:"bad"}},D.library);ok(r.inputs.flowSccm===null&&r.inputs.leakLoad===null);});
return {passed:count,failures};
}
const result=runTests(sandbox.VacuumCore,sandbox.VacuumData);
console.log(result.passed+" passed");
for(const failure of result.failures)console.error(failure);
if(result.failures.length)process.exitCode=1;
