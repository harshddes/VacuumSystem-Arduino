/* Vacuum Workbench core. No hardware I/O. */
(function(root) {
"use strict";
const positive=x=>typeof x==="number"&&Number.isFinite(x)&&x>0;
const nonnegative=x=>typeof x==="number"&&Number.isFinite(x)&&x>=0;
function pressureState(value) {
  if(typeof value!=="number"||!Number.isFinite(value)||value<=0) return {valid:false,label:"Missing / invalid"};
  if(Math.abs(value-1100)<=1) return {valid:false,label:"Open jack flag"};
  if(value>=9e9) return {valid:false,label:"Filament-off flag"};
  return {valid:true,label:"Pressure"};
}
function convertPressure(value,from,to) {
  const factor={Torr:133.32236842105263,mbar:100,Pa:1};
  if(!Number.isFinite(value)||!factor[from]||!factor[to]) throw Error("Invalid pressure conversion");
  return value*factor[from]/factor[to];
}
function series(values) {
  if(!Array.isArray(values)||!values.length||values.some(x=>!positive(x))) return null;
  return 1/values.reduce((r,x)=>r+1/x,0);
}
function size(i) {
  const out={conductance:null,effectiveSpeed:null,load:null,basePressure:null,pumpdown:null,knudsen:null,regime:"Unresolved",notes:[]};
  const gasMass={N2:28.0134,Ar:39.948,He:4.0026,Air:28.97}[i.gas];
  if(positive(i.diameterCm)&&positive(i.lengthCm)&&positive(i.temperatureK)&&gasMass) {
    // Long, straight circular tube; air 20 C baseline, molecular flow.
    out.conductance=12.1*Math.pow(i.diameterCm,3)/i.lengthCm*Math.sqrt(28.97/gasMass)*Math.sqrt(i.temperatureK/293.15);
    if(i.lengthCm/i.diameterCm<10) out.notes.push("L/D < 10: long-tube formula is a poor approximation; use a transmission factor or measured conductance.");
    if(positive(i.pumpSpeed)) out.effectiveSpeed=series([i.pumpSpeed,out.conductance,...(positive(i.valveConductance)?[i.valveConductance]:[])]);
    else out.notes.push("Enter gas-specific pumping speed.");
  }
  if(positive(i.diameterCm)&&positive(i.operatingPressureTorr)&&positive(i.temperatureK)) {
    // Hard-sphere N2/air estimate only, 0.37 nm collision diameter.
    if(i.gas==="N2"||i.gas==="Air") {
      const lambda=1.380649e-23*i.temperatureK/(Math.sqrt(2)*Math.PI*Math.pow(0.37e-9,2)*convertPressure(i.operatingPressureTorr,"Torr","Pa"));
      out.knudsen=lambda/(i.diameterCm/100);
      out.regime=out.knudsen>10?"Molecular":out.knudsen<0.01?"Continuum":"Transition / slip";
      if(out.regime!=="Molecular") out.notes.push("Molecular conductance is outside its stated regime at this pressure. It is not a roughing-line prediction.");
    } else out.notes.push("Knudsen estimate only supplied for N2/air; other gases need collision data.");
  }
  if(nonnegative(i.flowSccm)&&nonnegative(i.leakLoad)&&nonnegative(i.outgasLoad)&&positive(i.temperatureK)) {
    // sccm defined at 0 C, 1 atm. Chamber throughput scales with T/Tstd.
    out.load=i.flowSccm*0.012666666666666667*(i.temperatureK/273.15)+i.leakLoad+i.outgasLoad;
    if(positive(out.effectiveSpeed)) out.basePressure=out.load/out.effectiveSpeed;
  }
  if(positive(i.volumeL)&&positive(i.initialPressureTorr)&&positive(i.targetPressureTorr)&&positive(out.effectiveSpeed)&&out.basePressure!==null) {
    const peq=out.basePressure;
    if(i.targetPressureTorr>=i.initialPressureTorr) out.notes.push("Target must be below starting pressure.");
    else if(i.targetPressureTorr<=peq) out.notes.push("Target is at or below the model's gas-load pressure floor; no finite pump-down time.");
    else out.pumpdown=i.volumeL/out.effectiveSpeed*Math.log((i.initialPressureTorr-peq)/(i.targetPressureTorr-peq));
  }
  out.notes.push("Constant-speed, isothermal sizing estimate. No cryopump capacity/regeneration, adsorption, water desorption, pump curve, or valve dynamics model.");
  return out;
}
function port(node,id,library) { return library[node.type]?.ports.find(p=>p.id===id); }
function connectionError(graph,a,b,library) {
  const na=graph.nodes.find(n=>n.id===a.node), nb=graph.nodes.find(n=>n.id===b.node);
  if(!na||!nb) return "Missing component";
  if(na.id===nb.id) return "Connect two different components";
  const pa=port(na,a.port,library),pb=port(nb,b.port,library);
  if(!pa||!pb) return "Unknown port";
  if(pa.kind!==pb.kind) return "Incompatible services: "+pa.kind+" / "+pb.kind;
  if(graph.edges.some(e=>(e.a.node===a.node&&e.a.port===a.port&&e.b.node===b.node&&e.b.port===b.port)||(e.b.node===a.node&&e.b.port===a.port&&e.a.node===b.node&&e.a.port===b.port))) return "Connection already exists";
  return null;
}
function validateGraph(graph,library) {
  const issues=[], ids=new Set();
  for(const n of graph.nodes) {
    if(ids.has(n.id)) issues.push("Duplicate component ID "+n.id);
    ids.add(n.id);
    if(!library[n.type]) issues.push("Unknown component type "+n.type);
    if(!Number.isFinite(n.x)||!Number.isFinite(n.y)) issues.push(n.id+": invalid coordinates");
  }
  for(const e of graph.edges) {
    const rest={nodes:graph.nodes,edges:graph.edges.filter(v=>v!==e)};
    const err=connectionError(rest,e.a,e.b,library);
    if(err) issues.push(e.id+": "+err);
  }
  for(const n of graph.nodes) if(!graph.edges.some(e=>e.a.node===n.id||e.b.node===n.id)) issues.push(n.id+": unconnected component");
  return [...new Set(issues)];
}
function gatePosition(reed,busHealthy) { return !busHealthy?"UNKNOWN":reed===true?"CLOSED":reed===false?"NOT_CLOSED":"UNKNOWN"; }
function permissions(s) {
  const failures=[];
  const required={busHealthy:"Controller bus healthy",pressureFresh:"Pressure fresh",cryoReady:"Cryopump ready",airReady:"Actuation service ready",ventClosed:"Vent closure proved",roughClosed:"Roughing closure proved",independentInhibit:"Independent inhibit qualified"};
  Object.entries(required).forEach(([key,label])=>{if(s[key]!==true) failures.push(label);});
  if(!pressureState(s.pressureTorr).valid) failures.push("Valid chamber pressure");
  if(!positive(s.limitTorr)) failures.push("Reviewed pressure limit");
  else if(pressureState(s.pressureTorr).valid&&s.pressureTorr>s.limitTorr) failures.push("Pressure within limit");
  if(s.armed!==true) failures.push("Deliberate re-arm");
  return {allowed:failures.length===0,failures};
}
function stepSimulation(previous,event,s) {
  const next={...previous},p=permissions(s);
  if(event==="reset"||event==="trip"||!s.busHealthy) return {command:false,armed:false,position:gatePosition(s.closedReed,s.busHealthy),message:"Command released; physical closure needs proof."};
  if(event==="arm") { next.armed=true;next.command=false;next.message="Simulation armed. A new open request is required."; }
  else if(event==="close") {next.command=false;next.message="Close request: coil released. Await closed reed.";}
  else if(event==="open") {
    const q=permissions({...s,armed:next.armed});
    next.command=q.allowed; next.message=q.allowed?"Open command accepted in simulation; OPEN is not measured.":"Open blocked: "+q.failures.join("; ");
  }
  if(next.command&&!permissions({...s,armed:next.armed}).allowed) {next.command=false;next.armed=false;next.message="Permission lost. Command released; re-arm required.";}
  next.position=gatePosition(s.closedReed,s.busHealthy);
  return next;
}
function parseCsv(text) {
  // Deliberately scoped to unquoted numeric Hornet logger CSV, not arbitrary spreadsheets.
  const lines=text.replace(/^\uFEFF/,"").trim().split(/\r?\n/);
  if(lines.length<2) throw Error("CSV needs a header and data");
  const head=lines[0].split(",").map(x=>x.trim());
  const cols=["CG1_Torr","CG2_Torr","A2_CG1_Torr","A2_CG2_Torr"];
  if(!head.includes("t_s")||!cols.some(x=>head.includes(x))) throw Error("Expected Hornet CSV: t_s and at least one CG*_Torr column");
  const rows=[];
  for(const line of lines.slice(1)) {
    if(!line.trim()) continue;
    const cells=line.split(",");
    const val=name=>{const j=head.indexOf(name);if(j<0||!cells[j]?.trim())return null;const n=Number(cells[j]);return Number.isFinite(n)?n:null;};
    const t=val("t_s");if(t===null||t<0)continue;
    const row={t};cols.forEach(c=>{const v=val(c);row[c]=pressureState(v).valid?v:null;});rows.push(row);
  }
  if(!rows.length)throw Error("No valid time rows");
  return rows.sort((a,b)=>a.t-b.t);
}
function sanitizeProject(value,library) {
  if(!value||value.schema!=="vacuum-workbench/v1"||!Array.isArray(value.graph?.nodes)||!Array.isArray(value.graph?.edges)) throw Error("Unsupported project file");
  if(value.graph.nodes.length>200||value.graph.edges.length>600) throw Error("Project too large (200 components / 600 connections)");
  for(const n of value.graph.nodes) if(typeof n.id!=="string"||!library[n.type]||typeof n.name!=="string"||n.name.length>120||!Number.isFinite(n.x)||!Number.isFinite(n.y)||n.x<0||n.x>1800||n.y<0||n.y>1300) throw Error("Invalid component");
  const ids=value.graph.nodes.map(n=>n.id);
  if(new Set(ids).size!==ids.length)throw Error("Duplicate component IDs");
  for(const e of value.graph.edges) {
    if(typeof e.id!=="string"||!e.a||!e.b||typeof e.a.node!=="string"||typeof e.b.node!=="string"||typeof e.a.port!=="string"||typeof e.b.port!=="string")throw Error("Invalid connection");
    const error=connectionError({nodes:value.graph.nodes,edges:[]},e.a,e.b,library);
    if(error)throw Error(error);
  }
  const clean=JSON.parse(JSON.stringify(value));
  clean.graph.nodes=clean.graph.nodes.map(n=>({id:n.id,type:n.type,name:n.name,x:n.x,y:n.y,evidence:typeof n.evidence==="string"?n.evidence.slice(0,1000):"",status:["reported","proposed","bench"].includes(n.status)?n.status:"proposed"}));
  clean.graph.edges=clean.graph.edges.map(e=>({id:e.id,a:{node:e.a.node,port:e.a.port},b:{node:e.b.node,port:e.b.port}}));
  const numKeys=["diameterCm","lengthCm","temperatureK","pumpSpeed","valveConductance","flowSccm","leakLoad","outgasLoad","volumeL","initialPressureTorr","targetPressureTorr","operatingPressureTorr"];
  const input={gas:["N2","Air","Ar","He"].includes(value.inputs?.gas)?value.inputs.gas:"N2"};
  numKeys.forEach(k=>{input[k]=typeof value.inputs?.[k]==="number"&&Number.isFinite(value.inputs[k])?value.inputs[k]:null;});
  clean.inputs=input;clean.name=typeof value.name==="string"?value.name.slice(0,120):"Vacuum project";
  return clean;
}
root.VacuumCore={positive,pressureState,convertPressure,series,size,connectionError,validateGraph,gatePosition,permissions,stepSimulation,parseCsv,sanitizeProject};
})(globalThis);
