/* Browser-only design tool. No serial, network commands or equipment actuation. */
(function(){
"use strict";
const C=globalThis.VacuumCore,D=globalThis.VacuumData,L=D.library,$=s=>document.querySelector(s),KEY="maize-vacuum-designer-v1",clone=x=>JSON.parse(JSON.stringify(x));
const colors={vacuum:"#147f86",pneumatic:"#c78839",helium:"#9878c4",logic5:"#bd5e53",logicGround:"#77838f",SDA:"#337c9a",SCL:"#538caa",uartT:"#337f99",uartR:"#6095ad",rsPlus:"#ac8053",rsMinus:"#b18f6d",busGround:"#a88e7e",logicSignal:"#587fb3",field24:"#bc7150",fieldReturn:"#a88574",usb:"#8a87ac"};
const blankInputs={gas:"N2",diameterCm:null,lengthCm:null,temperatureK:null,pumpSpeed:null,valveConductance:null,flowSccm:null,leakLoad:null,outgasLoad:null,volumeL:null,initialPressureTorr:null,targetPressureTorr:null,operatingPressureTorr:null};
let state={schema:"vacuum-workbench/v1",name:"MAIZE vacuum system",graphs:clone(D.presets),inputs:{...blankInputs},review:{},sourceCommit:D.commit,example:false};
let view="process",selected=null,pending=null,zoom=1,history=[],drag=null,replayRows=[],toastTimer;
let sim={},simState={command:false,armed:false,position:"UNKNOWN",message:"Set simulated conditions, then deliberately re-arm."};
const permissionFields={busHealthy:["Controller bus healthy","Includes expander communication; loss releases the simulated command."],pressureFresh:["Chamber pressure fresh","Freshness limit must be reviewed for the installed controller."],cryoReady:["Cryopump cold / ready","Compressor ON alone is not readiness."],airReady:["Actuation service available","Minimum pressure and power/air-loss behavior need measurement."],ventClosed:["Vent closure proved","Not a requested or assumed closure."],roughClosed:["Roughing path isolated","Every bypass must be surveyed."],independentInhibit:["Independent inhibit qualified","A display and Arduino request are not an independent shutdown."],closedReed:["Closed reed made","B3 is the sole current gate position input."]};
const reviewItems=[
["asbuilt","Survey chamber and every connected path","Actual volume, flange sizes, isolation, vent, bypasses and cryopump pre-evacuation route."],
["gateid","Identify gate and pilot ports","Gate internal diameter and actuator C/O mapping; observe power loss and air loss separately."],
["closed","Verify B3 closed-reed truth table","A4/B4 and the damaged open switch remain disconnected. Absence of CLOSED never proves OPEN."],
["ground","Review power and isolation boundaries","Current 24 V return stays off logic ground; RS485 isolated reference stays separate."],
["wiring","Resolve conflicting historical wiring records","Newer Hornet prose says T→T/R→R and A→9/B→6. Older table/diagram differs."],
["pressure","Qualify each pressure channel and range","Gauge firmware/manual mismatch, location, unit, sentinel, freshness and unplug tests."],
["cryo","Qualify cryogenic readiness","Temperature/readout, permitted gas load/capacity, CTI services and regeneration."],
["driver","Review output protection and installation","Driver/contact ratings, flyback, fusing, secured wiring, enclosure and supply sizing."],
["interlock","Implement independent inhibition and closure","Complete opening/vent permissions on all manual and automatic paths."],
["limits","Establish reviewed limits and travel timing","Pressure thresholds, age, timeout and fault-recovery conditions."],
["acceptance","Record physical acceptance tests","Bench software checks do not certify valve motion or fault response."],
["sizing","Validate gas-specific performance model","Measured conductance/pump curves, gas load, cryopump capacity and actual duty cycle."]
];
function cleanDesign(value){
 if(!value||!value.graphs)throw Error("Project must contain both vacuum and electrical drawings");
 const graphs={};
 for(const key of ["process","electrical"]){
   const cleaned=C.sanitizeProject({schema:value.schema,name:value.name,graph:value.graphs[key],inputs:value.inputs},L);
   graphs[key]=cleaned.graph;
 }
 const safe=C.sanitizeProject({schema:value.schema,name:value.name,graph:graphs.process,inputs:value.inputs},L);
 return {...state,name:safe.name,graphs,inputs:safe.inputs,review:Object.fromEntries(reviewItems.map(([id])=>[id,value.review?.[id]===true])),sourceCommit:D.commit,example:value.example===true};
}
try{const stored=localStorage.getItem(KEY);if(stored)state=cleanDesign(JSON.parse(stored));}catch{toast("Saved project unavailable. Loaded the pinned starting drawings.");}
function graph(){return state.graphs[view];}
function toast(message){const el=$("#toast");if(!el)return;el.textContent=message;el.style.display="block";clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.style.display="none",5500);}
function persist(){try{localStorage.setItem(KEY,JSON.stringify(state));$("#save-status").textContent="Saved on this browser";}catch{$("#save-status").textContent="Storage unavailable · export to keep changes";} }
function checkpoint(){history.push(JSON.stringify(state));if(history.length>30)history.shift();$("#undo").disabled=false;}
function esc(x){return String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function sci(n,unit=""){return typeof n==="number"&&Number.isFinite(n)?(Math.abs(n)>=.01&&Math.abs(n)<10000?Number(n.toPrecision(4)).toString():n.toExponential(3))+(unit?" "+unit:""):"Unresolved";}
function download(name,content,type){const blob=new Blob([content],{type}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function csv(rows){return rows.map(row=>row.map(value=>{let s=String(value??"");if(/^[=+@\t\r]/.test(s)||/^-(?!\d)/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}).join(",")).join("\r\n");}
function nav(){
 const page=location.hash.slice(1)||"schematic";
 if(!["schematic","sizing","interlocks","connections","review","sources"].includes(page)){location.hash="schematic";return;}
 document.querySelectorAll(".page").forEach(el=>el.hidden=el.id!=="page-"+page);
 document.querySelectorAll(".nav").forEach(el=>{el.classList.toggle("active",el.dataset.page===page);if(el.dataset.page===page)el.setAttribute("aria-current","page");else el.removeAttribute("aria-current");});
 const labels={schematic:["Vacuum system designer","Build the gas path. Trace the control chain. Keep every assumption visible."],sizing:["Flow & pump sizing","See what line resistance and gas load do to effective pumping speed."],interlocks:["Interlock simulator","Explore permissions and fault recovery before a physical acceptance test."],connections:["Connections & I/O","Trace the current bench circuit from the screen to the pilot coil."],review:["Design review","Track unresolved interfaces, review evidence, and export the component inventory."],sources:["Sources & evidence","Follow every design choice back to the engineering basis and repository snapshot."]};
 $("#page-title").innerHTML=esc(labels[page][0])+"<span>.</span>";$("#page-subtitle").textContent=labels[page][1];
 if(page==="review")renderReview();
}
document.querySelectorAll(".nav").forEach(b=>b.onclick=()=>{location.hash=b.dataset.page;});
window.addEventListener("hashchange",nav);
$("#scope-review").onclick=()=>location.hash="sources";
function library(){
 const query=$("#component-search").value.toLowerCase(),groups=[...new Set(Object.values(L).map(v=>v.group))];let count=0;
 $("#library").innerHTML=groups.map(group=>{
   const parts=Object.entries(L).filter(([id,d])=>d.group===group&&(d.name+" "+d.detail).toLowerCase().includes(query));
   count+=parts.length;
   return parts.length?'<div class="library-group">'+esc(group)+'</div>'+parts.map(([id,d])=>'<button class="part" data-add="'+id+'" title="'+esc(d.detail)+'"><span class="part-icon">'+({Vacuum:"◎",Pneumatic:"⌁",Electrical:"▦",Services:"◇"}[group])+'</span><span>'+esc(d.name)+'</span><b>+</b></button>').join(""):"";
 }).join("");
 $("#library-count").textContent=count;
 $("#library").querySelectorAll("[data-add]").forEach(b=>b.onclick=()=>{
   if(graph().nodes.length>=200){toast("Component limit reached");return;}
   checkpoint();const type=b.dataset.add;let n=1;while(graph().nodes.some(v=>v.id==="N"+n))n++;
   const node={id:"N"+n,type,name:L[type].name,x:100+(graph().nodes.length%5)*220,y:80+(Math.floor(graph().nodes.length/5)%6)*170,status:"proposed",evidence:""};
   graph().nodes.push(node);selected={type:"node",id:node.id};pending=null;persist();render();toast("Component added. Drag to position, then connect its ports.");
 });
}
$("#component-search").oninput=library;
function point(n,portId){
 const ports=L[n.type].ports,p=ports.find(p=>p.id===portId),same=ports.filter(v=>v.side===p.side),i=same.indexOf(p),f=(i+1)/(same.length+1),w=180,h=160;
 return {x:n.x+(p.side==="right"?w:p.side==="left"?0:f*w),y:n.y+(p.side==="bottom"?h:p.side==="top"?0:f*h),side:p.side,kind:p.kind};
}
function symbol(type){
 const lines={
 chamber:'<path d="M65 0h50v32H65zM70 6h40v20H70z"/>',
 gate:'<path d="M63 0l54 32V0L63 32zM90 -7v46"/>',
 valve:'<path d="M63 0l54 32V0L63 32zM90 0v-12m-12 0h24"/>',
 cryo:'<circle cx="90" cy="16" r="22"/><path d="M90 -2v36M74 6l32 20m0-20L74 26"/>',
 pump:'<circle cx="90" cy="16" r="23"/><path d="M74 1l32 15-32 15z"/>',
 turbo:'<circle cx="90" cy="16" r="23"/><path d="M73 3l34 26m-34 0l34-26M90 -7v46"/>',
 gauge:'<circle cx="90" cy="16" r="22"/><path d="M90 16l12-12M90 38v10"/>',
 pipe:'<path d="M55 10h70M55 22h70"/>',tee:'<path d="M55 10h70M90 10v30"/>',
 trap:'<path d="M64 -4h52v40H64zM69 3l42 26m-42 0l42-26"/>',
 cylinder:'<path d="M75 0q15-13 30 0v34H75zM83 -7v-8h14v8"/>',
 regulator:'<path d="M65 -5h50v40H65zM71 28l38-25M90 -5v-10"/>',
 pilot:'<path d="M52 -6h76v42H52zM90 -6v42M60 26l21-24m18 0l21 24"/>',
 exhaust:'<path d="M70 3h40M75 11h30M80 19h20M85 27h10"/>',
 compressor:'<circle cx="90" cy="16" r="23"/><path d="M73 27l17-30 17 30z"/>',
 board:'<rect x="64" y="-5" width="52" height="42" rx="4"/><path d="M56 4h8m-8 12h8m-8 12h8m52-24h8m-8 12h8m-8 12h8M76 6h28v20H76z"/>',
 instrument:'<rect x="60" y="-6" width="60" height="44" rx="4"/><path d="M69 4h42v14H69zM71 28h5m11 0h5m11 0h5"/>',
 supply:'<rect x="60" y="-6" width="60" height="44"/><path d="M68 6h14m-7-7v14m17 12h14"/>',
 relay:'<path d="M55 -6h70v44H55zM88 -6v44M61 9h18v14H61zM96 26l19-22M96 26h-4m24 0h-4" stroke-dasharray="none"/>',
 coil:'<path d="M60 24c0-30 15-30 15 0c0-30 15-30 15 0c0-30 15-30 15 0c0-30 15-30 15 0"/>',
 diode:'<path d="M55 16h70M77 0v32l28-16zM105 0v32"/>',
 contact:'<path d="M55 25h20l30-25M109 25h16"/>',
 computer:'<rect x="59" y="-9" width="62" height="42" rx="3"/><path d="M90 33v10M70 43h40"/>'
 };
 return lines[type]||lines.board;
}
function nodeMarkup(n){
 const ports=L[n.type].ports.map(p=>{const pt=point(n,p.id),x=pt.x-n.x,y=pt.y-n.y,isSide=p.side==="left"||p.side==="right";
 const tx=p.side==="left"?9:p.side==="right"?171:x,ty=p.side==="bottom"?y-9:p.side==="top"?y+13:y-7,anchor=p.side==="left"?"start":p.side==="right"?"end":"middle";
 return '<text class="port-label" x="'+tx+'" y="'+ty+'" text-anchor="'+anchor+'">'+esc(p.label)+'</text><circle class="port '+(pending?.node===n.id&&pending.port===p.id?"pending":"")+'" cx="'+x+'" cy="'+y+'" r="5" stroke="'+colors[p.kind]+'" data-port="'+esc(p.id)+'" data-node="'+esc(n.id)+'" tabindex="0" role="button" aria-label="'+esc(n.name+" port "+p.label+", "+p.kind)+'"/>';}).join("");
 const name=n.name.length>24?[n.name.slice(0,24),n.name.slice(24,48)]:[n.name];
 return '<g class="node '+(selected?.type==="node"&&selected.id===n.id?"selected":"")+'" transform="translate('+n.x+' '+n.y+')" data-node="'+esc(n.id)+'" tabindex="0" role="button" aria-label="'+esc(n.id+" "+n.name)+'"><rect class="body" width="180" height="160" rx="7"/><text class="id" x="90" y="31" text-anchor="middle">'+esc(n.id)+" · "+esc(n.status.toUpperCase())+'</text>'+name.map((v,i)=>'<text class="name" x="90" y="'+(64+i*15)+'" text-anchor="middle">'+esc(v)+'</text>').join("")+'<g class="symbol" transform="translate(0 95)">'+symbol(L[n.type].symbol)+'</g>'+ports+'</g>';
}
function renderCanvas(){
 const g=graph();let edges="";
 for(const e of g.edges){
  const a=g.nodes.find(n=>n.id===e.a.node),b=g.nodes.find(n=>n.id===e.b.node);if(!a||!b)continue;
  const pa=point(a,e.a.port),pb=point(b,e.b.port),mx=(pa.x+pb.x)/2;
  const path=pa.side==="top"||pa.side==="bottom"?"M"+pa.x+" "+pa.y+"V"+((pa.y+pb.y)/2)+"H"+pb.x+"V"+pb.y:"M"+pa.x+" "+pa.y+"H"+mx+"V"+pb.y+"H"+pb.x;
  const id=esc(e.id);edges+='<g data-edge="'+id+'"><path class="edge-hit" d="'+path+'"/><path class="edge '+(selected?.type==="edge"&&selected.id===e.id?"selected":"")+'" stroke="'+colors[pa.kind]+'" d="'+path+'"><title>'+esc(e.a.node+":"+e.a.port+" → "+e.b.node+":"+e.b.port)+'</title></path></g>';
 }
 $("#drawing").innerHTML='<text class="drawing-label" x="24" y="1220">'+(view==="process"?"CONCEPT TOPOLOGY · PNEUMATIC C/O ROUTING REQUIRES CONFIRMATION":"CURRENT BENCH RECORDS · FIELD HARNESS NOT RELEASED")+'</text>'+edges+g.nodes.map(nodeMarkup).join("");
 $("#drawing").style.width=(zoom*100)+"%";
 $("#drawing-label").textContent=view==="process"?"01 / VACUUM & PNEUMATICS":"02 / ELECTRICAL & CONTROL";
 $("#drawing-count").textContent=g.nodes.length+" COMPONENTS · "+g.edges.length+" CONNECTIONS";
 $("#component-total").textContent=g.nodes.length;$("#connection-total").textContent=g.edges.length;
 $("#zoom-label").textContent=Math.round(zoom*100)+"%";
 $("#view-process").classList.toggle("selected",view==="process");$("#view-electrical").classList.toggle("selected",view==="electrical");
 $("#cancel-connection").hidden=!pending;
 const issues=C.validateGraph(g,L);$("#graph-status").textContent=issues.length?issues.length+" connectivity item(s) to review":"Typed connections consistent · physical design unqualified";
 const kinds=[...new Set(g.nodes.flatMap(n=>L[n.type].ports.map(p=>p.kind)))];
 $("#legend").innerHTML=kinds.map(k=>'<span><i style="background:'+colors[k]+'"></i>'+esc(k)+'</span>').join("");
}
function inspector(){
 const holder=$("#inspector");
 if(!selected){holder.innerHTML='<div class="inspector-body"><div><span class="tag">START HERE</span><p>Select a component to inspect its ports, provenance and unresolved details.</p><p>Add a library component, then select a port and a second port of the same service to connect them.</p></div><div class="notice">Line crossings do not create junctions. Connections exist only between explicit ports.</div></div>';return;}
 if(selected.type==="edge"){
  const e=graph().edges.find(v=>v.id===selected.id);if(!e){selected=null;inspector();return;}
  holder.innerHTML='<div class="inspector-body"><div><h2>'+esc(e.id)+'</h2><p>'+esc(e.a.node+":"+e.a.port)+" → "+esc(e.b.node+":"+e.b.port)+'</p><button id="delete-selected" class="button danger">Remove connection</button></div></div>';
 }else{
  const n=graph().nodes.find(v=>v.id===selected.id);if(!n){selected=null;inspector();return;}
  holder.innerHTML='<div class="inspector-body"><div><span class="tag">'+esc(L[n.type].group)+'</span><p>'+esc(L[n.type].detail)+'</p><label>Component label<input id="component-name" maxlength="120" value="'+esc(n.name)+'"></label><label>Evidence status<select id="component-status">'+["proposed","reported","bench"].map(s=>'<option '+(n.status===s?"selected":"")+'>'+s+'</option>').join("")+'</select></label><label>Evidence / unresolved detail<input id="component-evidence" maxlength="1000" value="'+esc(n.evidence)+'" placeholder="Observation or source"></label><button id="delete-selected" class="button danger">Remove component</button></div><div><dl><dt>COMPONENT ID</dt><dd>'+esc(n.id)+'</dd><dt>PORTS · SELECT TO CONNECT</dt></dl><div class="port-list">'+L[n.type].ports.map(p=>'<button class="port-button '+(pending?.node===n.id&&pending.port===p.id?"pending":"")+'" data-connect="'+esc(p.id)+'">'+esc(p.label)+'<br><small>'+esc(p.kind)+'</small></button>').join("")+'</div><p class="note">Bench/reported status records provenance; it is not an acceptance sign-off.</p></div></div>';
  $("#component-name").onchange=e=>{checkpoint();n.name=e.target.value.trim()||L[n.type].name;persist();render();};
  $("#component-status").onchange=e=>{checkpoint();n.status=e.target.value;persist();render();};
  $("#component-evidence").onchange=e=>{checkpoint();n.evidence=e.target.value;persist();};
  holder.querySelectorAll("[data-connect]").forEach(b=>b.onclick=()=>connect(n.id,b.dataset.connect));
 }
 $("#delete-selected").onclick=()=>{
  checkpoint();
  if(selected.type==="node"){graph().nodes=graph().nodes.filter(n=>n.id!==selected.id);graph().edges=graph().edges.filter(e=>e.a.node!==selected.id&&e.b.node!==selected.id);}
  else graph().edges=graph().edges.filter(e=>e.id!==selected.id);
  selected=null;pending=null;persist();render();
 };
}
function render(){renderCanvas();inspector();$("#undo").disabled=!history.length;}
function connect(node,port){
 const endpoint={node,port};
 if(!pending){pending=endpoint;selected={type:"node",id:node};toast("Choose another port of the same service.");render();return;}
 if(pending.node===node&&pending.port===port){pending=null;render();return;}
 const error=C.connectionError(graph(),pending,endpoint,L);if(error){toast(error);return;}
 checkpoint();let id=1;while(graph().edges.some(e=>e.id==="C"+id))id++;
 graph().edges.push({id:"C"+id,a:pending,b:endpoint});pending=null;persist();render();
}
$("#drawing").addEventListener("click",e=>{
 const port=e.target.closest("[data-port]");if(port){connect(port.dataset.node,port.dataset.port);return;}
 const edge=e.target.closest("[data-edge]");if(edge){selected={type:"edge",id:edge.dataset.edge};render();return;}
 const node=e.target.closest("g.node");if(node){selected={type:"node",id:node.dataset.node};render();return;}
 selected=null;render();
});
$("#drawing").addEventListener("keydown",e=>{
 const port=e.target.closest("[data-port]");if(port&&(e.key==="Enter"||e.key===" ")){e.preventDefault();connect(port.dataset.node,port.dataset.port);return;}
 const el=e.target.closest("g.node");if(!el)return;
 if(e.key==="Enter"||e.key===" "){e.preventDefault();selected={type:"node",id:el.dataset.node};render();return;}
 if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(e.key)){
  e.preventDefault();checkpoint();const n=graph().nodes.find(n=>n.id===el.dataset.node),step=e.shiftKey?30:10;
  n.x=Math.max(0,Math.min(1370,n.x+(e.key==="ArrowLeft"?-step:e.key==="ArrowRight"?step:0)));
  n.y=Math.max(0,Math.min(1070,n.y+(e.key==="ArrowUp"?-step:e.key==="ArrowDown"?step:0)));
  selected={type:"node",id:n.id};persist();render();Array.from($("#drawing").querySelectorAll("g.node")).find(el=>el.dataset.node===n.id)?.focus();
 }
});
function svgPoint(e){const p=$("#drawing").createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform($("#drawing").getScreenCTM().inverse());}
$("#drawing").addEventListener("pointerdown",e=>{
 if(e.button!==0||e.target.closest("[data-port]"))return;const el=e.target.closest("g.node");if(!el)return;
 const n=graph().nodes.find(n=>n.id===el.dataset.node),p=svgPoint(e);checkpoint();drag={node:n,dx:p.x-n.x,dy:p.y-n.y};selected={type:"node",id:n.id};$("#drawing").setPointerCapture(e.pointerId);inspector();
});
$("#drawing").addEventListener("pointermove",e=>{if(!drag)return;const p=svgPoint(e);drag.node.x=Math.max(0,Math.min(1370,Math.round(p.x-drag.dx)));drag.node.y=Math.max(0,Math.min(1070,Math.round(p.y-drag.dy)));renderCanvas();});
function endDrag(){if(drag){drag=null;persist();render();}}
$("#drawing").addEventListener("pointerup",endDrag);$("#drawing").addEventListener("pointercancel",endDrag);
$("#cancel-connection").onclick=()=>{pending=null;render();};
document.addEventListener("keydown",e=>{if(e.key==="Escape"){pending=null;drag=null;render();}});
function setView(v){view=v;selected=null;pending=null;zoom=1;render();}
$("#view-process").onclick=()=>setView("process");$("#view-electrical").onclick=()=>setView("electrical");
$("#zoom-in").onclick=()=>{zoom=Math.min(3,zoom+.25);renderCanvas();};$("#zoom-out").onclick=()=>{zoom=Math.max(.5,zoom-.25);renderCanvas();};$("#fit").onclick=()=>{zoom=1;$("#canvas-wrap").scrollTo(0,0);renderCanvas();};
$("#undo").onclick=()=>{if(!history.length)return;state=JSON.parse(history.pop());selected=null;pending=null;persist();render();renderInputs();sizing();};
$("#reset-drawing").onclick=()=>{if(!confirm("Restore this drawing to the pinned starting topology? Undo can recover your current drawing."))return;checkpoint();state.graphs[view]=clone(D.presets[view]);selected=null;pending=null;persist();render();};
$("#export-svg").onclick=()=>{const copy=$("#drawing").cloneNode(true);copy.setAttribute("xmlns","http://www.w3.org/2000/svg");copy.removeAttribute("style");copy.setAttribute("width","1550");copy.setAttribute("height","1250");const style=document.createElementNS("http://www.w3.org/2000/svg","style");style.textContent='.edge{fill:none;stroke-width:2.5}.edge-hit{display:none}.node .body{fill:white;stroke:#b4c9d4;stroke-width:1.5}.node text{font:12px sans-serif;fill:#445e71}.node .id,.node .port-label{font-size:8px}.symbol{stroke:#426d7a;stroke-width:2;fill:none}.port{fill:white;stroke-width:2}.drawing-label{font:10px sans-serif;fill:#708090}';copy.prepend(style);download("MAIZE-"+view+"-concept.svg",new XMLSerializer().serializeToString(copy),"image/svg+xml");};
$("#export-project").onclick=()=>download("MAIZE-vacuum-project.json",JSON.stringify(state,null,2),"application/json");
$("#import-project").onclick=()=>$("#project-file").click();
$("#project-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>1500000)throw Error("Project exceeds 1.5 MB");const next=cleanDesign(JSON.parse(await file.text()));checkpoint();state=next;selected=null;pending=null;persist();render();renderInputs();sizing();renderReview();toast("Project imported. Simulated states remain separate.");}catch(err){toast("Import failed: "+err.message);}finally{e.target.value="";}};
const inputFields=[
["gas","Process gas","select"],["temperatureK","Gas temperature (K)","number"],["diameterCm","Straight line inside diameter (cm)","number"],["lengthCm","Straight line length (cm)","number"],["pumpSpeed","Gas-specific pump speed (L/s)","number"],["valveConductance","Molecular valve conductance (L/s, optional)","number"],["operatingPressureTorr","Regime check pressure (Torr)","number"],["volumeL","Connected chamber volume (L)","number"],["flowSccm","Gas flow (SCCM, 0 °C, 1 atm)","number"],["leakLoad","Leak load (Torr·L/s)","number"],["outgasLoad","Outgassing load (Torr·L/s)","number"],["initialPressureTorr","Starting pressure, molecular interval (Torr)","number"],["targetPressureTorr","Target pressure (Torr)","number"]
];
function renderInputs(){
 $("#sizing-inputs").innerHTML=inputFields.map(([key,label,type])=>'<label>'+esc(label)+(type==="select"?'<select data-input="'+key+'">'+["N2","Air","Ar","He"].map(g=>'<option '+(state.inputs.gas===g?"selected":"")+'>'+g+'</option>').join("")+'</select>':'<input type="number" data-input="'+key+'" min="0" step="any" value="'+(state.inputs[key]??"")+'" placeholder="Unresolved">')+'</label>').join("");
 $("#sizing-inputs").querySelectorAll("[data-input]").forEach(el=>el.onchange=()=>{
  checkpoint();state.inputs[el.dataset.input]=el.dataset.input==="gas"?el.value:el.value.trim()===""?null:Number(el.value);state.example=false;persist();sizing();
 });
}
function sizing(){
 const r=C.size(state.inputs),inRegime=r.regime==="Molecular";
 const metrics=[["Tube molecular conductance",r.conductance,"L/s"],["Effective pumping speed",r.effectiveSpeed,"L/s"],["Gas-load pressure floor",r.basePressure,"Torr"],["Idealized interval time",r.pumpdown,"s"]];
 $("#sizing-results").innerHTML=metrics.map(([label,value,unit])=>'<div class="metric"><span>'+label+'</span><strong>'+sci(value)+'</strong><small>'+unit+" · "+(state.example?"LABELLED EXAMPLE":inRegime?"Molecular-flow estimate":"Regime applicability unresolved")+'</small></div>').join("");
 let notes=[...r.notes];if(!state.inputs.valveConductance)notes.unshift("Valve loss omitted until a positive measured/manufacturer conductance is supplied.");if(r.regime==="Unresolved")notes.unshift("Flow regime not established. Enter pressure, diameter and temperature; Kn estimate is provided for N2/air only.");
 const regimes=[state.inputs.initialPressureTorr,state.inputs.targetPressureTorr].filter(C.positive).map(p=>C.size({...state.inputs,operatingPressureTorr:p}).regime);
 if(regimes.some(x=>x!=="Molecular"))notes.unshift("Entered pump-down interval is not entirely confirmed molecular flow. Time is a mathematical estimate outside a validated regime.");
 $("#sizing-notes").innerHTML='<div class="notice '+(!inRegime?"amber":"")+'"><b>Regime: '+esc(r.regime)+'</b> · Kn '+sci(r.knudsen)+'</div>'+notes.map(n=>'<p class="muted">'+esc(n)+'</p>').join("");
}
$("#example-inputs").onclick=()=>{checkpoint();state.inputs={gas:"N2",diameterCm:10,lengthCm:100,temperatureK:293.15,pumpSpeed:1000,valveConductance:500,flowSccm:0,leakLoad:1e-7,outgasLoad:1e-5,volumeL:100,initialPressureTorr:1e-5,targetPressureTorr:1e-6,operatingPressureTorr:1e-5};state.example=true;persist();renderInputs();sizing();toast("Example only: these are not MAIZE equipment specifications.");};
function renderSimControls(){
 $("#sim-controls").innerHTML=Object.entries(permissionFields).map(([key,[label,detail]])=>'<label class="check-row"><input type="checkbox" data-sim="'+key+'"><span>'+esc(label)+'<small>'+esc(detail)+'</small></span></label>').join("");
 $("#sim-controls").querySelectorAll("[data-sim]").forEach(el=>el.onchange=()=>{sim[el.dataset.sim]=el.checked;runSim("check");});
}
function simInputs(){return {...sim,pressureTorr:$("#sim-pressure").value===""?null:Number($("#sim-pressure").value),limitTorr:$("#sim-limit").value===""?null:Number($("#sim-limit").value),armed:simState.armed};}
function runSim(event){
 simState=C.stepSimulation(simState,event,simInputs());
 $("#sim-command").textContent=simState.command?"ENERGIZED":"RELEASED";$("#sim-position").textContent=simState.position;$("#sim-message").textContent=simState.message;
 const p=C.permissions({...simInputs(),armed:simState.armed});
 $("#sim-permissions").innerHTML='<div class="permission '+(p.allowed?"pass":"")+'">'+(p.allowed?"✓ Open request permitted in simulation":"○ Open blocked")+'</div>'+p.failures.map(f=>'<div class="permission">○ '+esc(f)+'</div>').join("");
 if(event!=="check"||simState.message.startsWith("Permission lost")){const li=document.createElement("li");li.textContent=new Date().toLocaleTimeString()+" · "+simState.message;$("#sim-log").prepend(li);while($("#sim-log").children.length>12)$("#sim-log").lastChild.remove();}
}
$("#sim-pressure").oninput=()=>runSim("check");$("#sim-limit").oninput=()=>runSim("check");
for(const [id,event] of [["arm","arm"],["open","open"],["close","close"],["trip","trip"]])$("#sim-"+id).onclick=()=>runSim(event);
$("#sim-reset").onclick=()=>{sim={};simState={command:false,armed:false,position:"UNKNOWN",message:"Reset. No simulated conditions are proved."};$("#sim-pressure").value="";$("#sim-limit").value="";renderSimControls();runSim("reset");};
const wireRows=[
["P-01 / P-02","SG closed reed","5346 B3 / logic GND","B3 = index 11; grounded=true. D13 onboard L follows this reed."],
["P-03 / P-04","Melted open switch / expander A4, B4","No terminal / no wire","Not a sensor; NOT_CLOSED does not mean OPEN."],
["P-05","Uno 5V","Relay DC+","Module logic supply; onboard relay driver."],
["P-06","Uno GND","Relay DC−","Logic return only."],
["P-07","Uno D8","Relay IN","H/L jumper H; HIGH requests coil; LOW releases."],
["P-08","24 V positive","Relay COM","Field power on dry contacts."],
["P-09","Relay NO","Humphrey lead A","NC empty; not a direct Uno load."],
["P-10","Humphrey lead B","24 V negative","Do not join to Uno GND in this circuit."],
["P-11","1N400x cathode stripe / anode","Humphrey positive lead / negative lead","Diode across Humphrey coil, not across relay contacts."],
["MCP address","5346 D0 address pin","Uno 5 V, or +1 solder jumper","Select 0x21. Board D0 is not Uno D0."],
["I2C","Uno A4 / A5","5346 SDA/SCL; DFR0627 D/C","Shared bus; MCP at 0x21. Uno A4 differs from expander A4."],
["R-01…R-06","Uno 5V / GND","DFR0627 +/−; DFR0845 logic +/−","Logic side only. DFR0845 12 V screws stay empty."],
["R-07 newer prose","DFR0627 UART1 T","DFR0845 logic T","Latest successful trial; older wire schedule conflicts."],
["R-08 newer prose","DFR0627 UART1 R","DFR0845 logic R","Latest successful trial; remove loopback jumpers."],
["RS485+ newer prose","DFR0845 A (+)","Hornet DE9 pin 9, DATA B (+)","Vendor letters differ; match polarity, not letter."],
["RS485− newer prose","DFR0845 B (−)","Hornet DE9 pin 6, DATA A (−)","Older Mermaid conflicts; interface still under qualification."],
["RS485 reference","DFR0845 bus ground beside A/B","Hornet DE9 pin 4","Isolated reference; separate from logic − and shell GND."],
["Hornet supply","Existing approved supply","Existing power connection","Do not add power to RS485 pin 2; pin 2 empty in trial."],
["Gate button","5346 A0 / GND","Momentary contact","Press edge toggles bench memory; USB o opens, c/x releases."]
];
$("#wire-table").innerHTML=wireRows.map(row=>'<tr>'+row.map(cell=>'<td>'+esc(cell)+'</td>').join("")+'</tr>').join("");
$("#export-wires").onclick=()=>download("MAIZE-bench-connections.csv",csv([["ID","From","To","Meaning"],...wireRows]),"text/csv");
$("#io-table").innerHTML='<table><tbody>'+[
["D8","Coil command; HIGH=requested, not position"],
["MCP B3","Closed reed; LOW=CLOSED"],
["D13 onboard L","Follows the closed reed"],
["MCP A4 / B4","Empty; damaged open switch disconnected"],
["MCP A2","Simulated closed jumper, not the real gate"],
["MCP A0","Gate request button"],
["o / c / x","Bench serial request open / release / release"],
["Expander loss","Current sketch releases coil after 300 ms silence; reconnection does not reopen"],
["D5 / D6 / D7","Disconnected; reported failures"]
].map(row=>'<tr>'+row.map(cell=>'<td>'+esc(cell)+'</td>').join("")+'</tr>').join("")+'</tbody></table>';
const replay=document.createElement("div");replay.className="panel padded replay";replay.innerHTML='<div class="panel-heading"><div><h2>Replay a Hornet log</h2><p class="muted">Import the repo logger CSV to inspect pressure history. Replay never drives equipment or grants permission.</p></div><button class="button subtle" id="load-csv">Import log CSV</button></div><p id="csv-status" class="muted">No log loaded. Missing, 1100 Torr and filament-off flags are excluded from the plot.</p><svg id="csv-chart" viewBox="0 0 900 240" class="csv-chart" aria-label="Imported pressure history"></svg>';
$("#page-connections").append(replay);
$("#load-csv").onclick=()=>$("#csv-file").click();
$("#csv-file").onchange=async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>10000000)throw Error("CSV exceeds 10 MB");replayRows=C.parseCsv(await f.text());renderReplay();$("#csv-status").textContent=f.name+" · "+replayRows.length+" time rows · logarithmic pressure (Torr).";}catch(err){toast("Log import failed: "+err.message);}finally{e.target.value="";}};
function renderReplay(){
 const cols=["CG1_Torr","CG2_Torr","A2_CG1_Torr","A2_CG2_Torr"],pal=["#084594","#d94801","#6baed6","#fdae6b"],all=replayRows.flatMap(r=>cols.map(c=>r[c]).filter(C.positive));
 if(!all.length){$("#csv-chart").innerHTML="";$("#csv-status").textContent="No valid pressure samples";return;}
 let lo=Infinity,hi=-Infinity;for(const v of all){const x=Math.log10(v);lo=Math.min(lo,x);hi=Math.max(hi,x);}if(hi-lo<1){hi+=.5;lo-=.5;}
 const t0=replayRows[0].t,t1=replayRows[replayRows.length-1].t,dt=Math.max(1,t1-t0),x=t=>60+780*(t-t0)/dt,y=p=>190-150*(Math.log10(p)-lo)/(hi-lo);
 let html='<path d="M60 30V190H840" fill="none" stroke="#aab8c7"/>';
 for(let i=0;i<5;i++){const p=lo+(hi-lo)*i/4;html+='<text x="5" y="'+(193-150*i/4)+'" font-size="10" fill="#738294">'+Math.pow(10,p).toExponential(1)+'</text><path d="M60 '+(190-150*i/4)+'H840" stroke="#edf1f5"/>';}
 html+='<text x="60" y="211" font-size="10">'+sci(t0)+" s"+'</text><text x="780" y="211" font-size="10">'+sci(t1)+" s"+'</text>';
 cols.forEach((col,i)=>{let path="",pen=false;const stride=Math.max(1,Math.floor(replayRows.length/2000));for(let j=0;j<replayRows.length;j++){const r=replayRows[j];if(!C.positive(r[col])){pen=false;continue;}if(j%stride!==0&&j!==replayRows.length-1)continue;path+=(pen?"L":"M")+x(r.t).toFixed(2)+" "+y(r[col]).toFixed(2);pen=true;}html+='<path d="'+path+'" fill="none" stroke="'+pal[i]+'" stroke-width="1.8"/><text x="'+(60+i*190)+'" y="235" font-size="10" fill="'+pal[i]+'">'+col+'</text>';});
 $("#csv-chart").innerHTML=html;
}
function inventory(){return Object.entries(state.graphs).flatMap(([drawing,g])=>g.nodes.map(n=>[drawing,n.id,n.name,L[n.type].name,n.status,n.evidence||L[n.type].detail]));}
function renderReview(){
 const done=reviewItems.filter(([id])=>state.review[id]).length;$("#review-count").textContent=(reviewItems.length-done)+" / "+reviewItems.length;
 $("#review-checklist").innerHTML=reviewItems.map(([id,label,detail])=>'<label class="check-row"><input type="checkbox" data-review="'+id+'" '+(state.review[id]?"checked":"")+'><span>'+esc(label)+'<small>'+esc(detail)+'</small></span></label>').join("");
 $("#review-checklist").querySelectorAll("[data-review]").forEach(el=>el.onchange=()=>{state.review[el.dataset.review]=el.checked;persist();renderReview();});
 $("#bom-table").innerHTML='<div class="table-scroll"><table><thead><tr><th>Drawing / ID</th><th>Symbol</th><th>Evidence</th></tr></thead><tbody>'+inventory().map(row=>'<tr><td>'+esc(row[0]+" / "+row[1])+'</td><td>'+esc(row[2])+'</td><td>'+esc(row[4])+'</td></tr>').join("")+'</tbody></table></div>';
 for(const key of ["process","electrical"]){const issues=C.validateGraph(state.graphs[key],L);if(issues.length){const n=document.createElement("div");n.className="notice amber";n.textContent=key+": "+issues.join("; ");$("#bom-table").prepend(n);}}
}
$("#export-bom").onclick=()=>download("MAIZE-drawing-component-inventory.csv",csv([["Drawing","ID","Label","Type","Evidence status","Detail"],...inventory()]),"text/csv");
$("#print-review").onclick=()=>{renderReview();window.print();};
$("#sources").innerHTML=D.sources.map(s=>'<article class="source"><small>'+esc(s.id)+'</small><a target="_blank" rel="noopener" href="'+esc(s.url)+'">'+esc(s.title)+' ↗</a><p>'+esc(s.use)+'</p></article>').join("");
library();render();renderInputs();sizing();renderSimControls();runSim("check");renderReview();nav();persist();
})();