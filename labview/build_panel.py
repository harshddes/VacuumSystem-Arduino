"""Rebuild editable VIs with Zuehlke/labview-mcp's offline AIXML composer.
Set AIXML_PYLABVIEW to its scripts/aixml-pylabview directory and LABVIEW_ROOT to NI's installation.
"""
import os
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, os.environ["AIXML_PYLABVIEW"])
import aixml2vi as A
import lvheap

OUT = Path(__file__).resolve().parent
OFFLINE = OUT / "offline"
WORK = Path(tempfile.mkdtemp(prefix="maize-native-"))
U32 = "uint32"
VALVES = ["Roughing valve", "Let-up valve", "Turbo gate valve", "Cryo gate valve"]
REQUESTS = ["Roughing OPEN", "Let-up OPEN", "Turbo OPEN", "Cryo OPEN"]
FAULTS = [
    "Normal", "Pressure signal lost", "Actuator air lost", "Roughing pump not ready",
    "Cryopump not ready", "Turbo not at speed", "Turbo backing lost", "Filament ON",
    "Lab enable lost", "Coil-feed inhibit", "Vent process inhibit", "Turbo gate stuck",
    "Cryo gate stuck", "Turbo feedback conflict", "Cryo feedback conflict", "Panel inputs lost",
]
ALARMS = [
    "CLOSE / STOP circuit open or unavailable.",
    "Actuator air permission missing.",
    "Lab opening enable missing.",
    "Independent coil-feed interlock unavailable.",
    "Physical selector or control input unavailable.",
    "Mode selector invalid or unavailable.",
    "Cryo gate reports conflicting end positions.",
    "Turbo gate reports conflicting end positions.",
    "Cryo gate position unknown outside permitted travel.",
    "Turbo gate position unknown outside permitted travel.",
    "Return all four manual selectors to CLOSE before AUTO.",
    "Sequence start conflict or start in wrong mode.",
    "Installation unreleased. Opening outputs inhibited.",
    "Let-up and pump OPEN requested together.",
    "Pump opening blocked. Let-up closure required.",
    "Let-up blocked. Close Roughing, Turbo and Cryo first.",
    "Let-up blocked. Filament OFF unconfirmed.",
    "Roughing pump ready signal missing.",
    "Cryopump cold/ready permission missing.",
    "Turbo at-speed/ready signal missing.",
    "Turbo backing permission missing.",
    "Current qualified chamber pressure unavailable.",
    "Cryo pressure or entry dwell outside operating limit.",
    "Turbo pressure or entry dwell outside operating limit.",
    "Requested pump-path combination lacks permission.",
    "Valve travel or isolation deadline expired.",
    "Sequence pressure unavailable or deadline expired.",
    "Gate position disagrees with the controller output.",
    "Vent gas / process-safe permission missing.",
    "Automatic valve sequence unqualified for this installation.",
    "Opening inhibited. Release requests and arm at the rack.",
]

class Diagram:
    def __init__(self, name, description, directory=OUT):
        self.name = name
        self.directory = directory
        self.root = ET.Element("VI", _name=name+".vi", description=description)
        self.parent = self.root
        self.count = 0
    def add(self, tag, **args):
        self.count += 1
        uid = "n"+str(self.count)
        args = {k:v.replace("OUT.",uid+".") for k,v in args.items()}
        return ET.SubElement(self.parent,tag,uid=uid,uid_parent=self.parent.get("uid","root"),**args)
    def value(self, label, typ, value, con=None):
        kw = {} if con is None else dict(conIdx=str(con),connection="required")
        tag = "Constant" if con is None else "Control"
        return self.add(tag, _name=label, type=typ, value=str(value),outputs="value:OUT.v",**kw).get("uid")+".v"
    def indicator(self,label,typ,wire,con=None):
        kw={} if con is None else dict(conIdx=str(con),connection="recommended")
        self.add("Indicator",_name=label,type=typ,value="",inputs="value:"+wire,**kw)
    def node(self,name,pins,pin="value",tag="Node",**kw):
        args={"inputs":",".join(a+":"+b for a,b in pins),"outputs":pin+":OUT.v"}
        args["target" if tag=="Call" else "_name"]=name
        return self.add(tag,**args,**kw).get("uid")+".v"
    def select(self, condition, yes, no):
        return self.node("Select",[("s",condition),("t",yes),("f",no)],r"s? t\3Af")
    def multi(self,name,pins,outputs,**kw):
        n=self.add("Node",_name=name,inputs=",".join(k+":"+v for k,v in pins),
                   outputs=",".join(k+":OUT.p"+str(i) for i,k in enumerate(outputs)),**kw)
        return [n.get("uid")+".p"+str(i) for i in range(len(outputs))]
    def string(self, s):
        return self.value("Text","string",s)
    def build(self,layout=None):
        source=WORK/(self.name+".xml")
        ET.ElementTree(self.root).write(source,encoding="utf-8")
        c=A.Composer(A.OWN_PARTS)
        c.search_dirs=list(dict.fromkeys(map(str,(self.directory,OUT))))
        c.caller_file=str(self.directory/(self.name+".vi"))
        c.target_major=25
        c.compose(str(source))
        if layout: layout(c)
        dest=WORK/self.name
        dest.mkdir()
        main=c.write(str(dest),self.name)
        A.retarget_version(str(dest),self.name,25)
        lvheap.rebuild(main,str(self.directory/(self.name+".vi")))
        print("Built",self.name,flush=True)

def permissions():
    d=Diagram("Vacuum permissions","Opening permission checks shared with the local Opta.")
    pins=[(v,d.value(v,U32,0,i)) for i,v in enumerate(["attempt","pos","status","site","events"])]
    code=(OUT/"firmware/OptaTelemetry/PermissionRules.h").read_text()
    val=d.node("Formula Node",pins,"alarms",text="uInt32 alarms;\n"+code)
    d.indicator("alarms",U32,val,15)
    d.build()

def messages():
    d=Diagram("Interlock messages","Decode every set permissive or fault bit in priority order.")
    w=d.value("Fault bits",U32,0,0)
    zero=d.value("Zero",U32,0)
    enabled=[]
    for i in range(len(ALARMS)):
        mask=d.value("Mask",U32,1<<i)
        hit=d.node("And",[("x",w),("y",mask)],"x .and. y?")
        enabled.append(d.node("Not Equal?",[("x",hit),("y",zero)],"x != y?"))
    blank=d.string("")
    rows=[d.select(b,d.string(msg+"\n"),blank) for b,msg in zip(enabled,ALARMS)]
    val=d.node("Concatenate Strings",[("string",s) for s in rows],"concatenated string")
    d.indicator("Messages","string",val,15)
    d.build()

def lamp(offline=False):
    d=Diagram("Offline valve lamp" if offline else "Valve pilot lamp",
              "Render valve position. Grey means unavailable or between endpoints.",
              OFFLINE if offline else OUT)
    pos=d.value("Position word",U32,0,0)
    shift=d.value("Bit offset",U32,0,1)
    selectors=d.value("Physical selectors",U32,0,2)
    known=d.value("Selector quality",U32,0,3)
    code="""uInt32 color, state, lever;
state=(pos >> shift) & 3;
color=0x696F71;
if(state==1) color=0x129747;
if(state==2) color=0xD32430;
lever=0;
if((known >> (shift/2)) & 1) {
  lever=1+((selectors >> (shift/2)) & 1);
  if(shift==6) lever=lever+2;
}"""
    color,state,lever=d.multi("Formula Node",[("pos",pos),("shift",shift),("known",known),("selectors",selectors)],
                              ["color","state","lever"],text=code)
    fill=d.value("Fill","bool","true")
    rect="cluster{int16.left,int16.top,int16.right,int16.bottom}"
    def bounds(box):
        return d.value("Bounds",rect,"["+",".join(map(str,box))+"]")
    def oval(pic,r,col):
        pins=[("rect",r),("fill?(F)",fill),("color(black)",col)]
        if pic: pins.append(("picture",pic))
        return d.node("Draw Oval.vi",pins,"new picture","Call")
    pic=None
    if not offline:
        for box,col in [((13,7,52,46),0x485153),((15,9,50,44),0xC5C6C1),((19,13,46,40),0x343A3A)]:
            pic=oval(pic,bounds(box),d.value("Bezel",U32,col))
    offset=66 if offline else 0
    for box,col in [((73,9,109,45),0x464E4F),((75,11,107,43),0xC4C9C6),((78,14,104,40),0x303636),
                    ((80,16,102,38),None)]:
        left,top,right,bottom=box
        pic=oval(pic,bounds((left-offset,top,right-offset,bottom)),color if col is None else d.value("Bezel",U32,col))
    if not offline:
        # Vertical throws on the upper plate, horizontal throws on the Cryo plate.
        throws=[(0,0,0,0),(26,26,37,49),(27,3,38,29),(32,21,58,32),(6,21,33,32)]
        for boxes,col in [(throws,0x53595A),([tuple((a+2,b+2,c-2,e-2)) if c else (0,0,0,0) for a,b,c,e in throws],0xBFC2BD)]:
            arr=d.node("Build Array",[("element",bounds(box)) for box in boxes],"appended array")
            r=d.node("Index Array",[("array",arr),("index",lever)],"element")
            pic=oval(pic,r,d.value("Toggle",U32,col))
    labels=d.node("Build Array",[("element",d.string(k)) for k in ("UNKNOWN","CLOSED","OPEN","CONFLICT")],"appended array")
    word=d.node("Index Array",[("array",labels),("index",state)],"element")
    pt=d.value("Text origin","cluster{int16.x,int16.y}",f"[{116-offset},18]")
    pic=d.node("Draw Text at Point.vi",[("picture",pic),("origin",pt),("text",word)],"new picture","Call")
    d.indicator("Lamp","picture",pic,15)
    d.build()

def offline_inputs(d, last):
    buttons=[]
    for name in [*REQUESTS, "Arm / Reset", "Pumpdown", "Vent sequence", "Close / Stop"]:
        momentary={"style":"latched"} if name not in REQUESTS else {}
        item=d.add("Control",_name=name,type="bool",value="false",outputs="value:OUT.v",**momentary)
        buttons.append(item.get("uid")+".v")
    values=[d.select(v,d.value("Bit",U32,1<<i),d.value("Clear",U32,0)) for i,v in enumerate(buttons)]
    terms=[(f"b{i}",v) for i,v in enumerate(values)]
    flags=d.node("Formula Node",terms,"flags",text="uInt32 flags;\nflags="+ "+".join(n for n,_ in terms)+";")
    mode=d.add("Control",_name="Mode",type="uint16{OFF,MANUAL,AUTO}",value="1",outputs="value:OUT.v").get("uid")+".v"
    fault=d.add("Control",_name="Test condition",type="uint16{"+",".join(FAULTS)+"}",value="0",
                outputs="value:OUT.v").get("uid")+".v"
    fmt=lambda v:d.node("Number To Decimal String",[("number",v)],"decimal integer string")
    parts=(fmt(flags),d.string(" "),fmt(mode),d.string(" "),fmt(fault),d.string(" "),last)
    return d.node("Concatenate Strings",[("string",v) for v in parts],"concatenated string")

def panel(offline=False):
    if offline:
        d=Diagram("MAIZE Offline Console","Offline MAIZE operator console with modeled equipment and the shared controller.",OFFLINE)
    else:
        d=Diagram("MAIZE Vacuum Console","MAIZE vacuum rack. Four read-only valve lamps and the local controller interlocks.")
    memory=d.string("")
    loop=d.add("Structure",_name="While Loop",count="scan.i")
    d.parent=loop
    register=d.add("ShiftReg")
    d.parent=register
    last=d.add("Left",inputs="value:"+memory,outputs="value:OUT.v").get("uid")+".v"
    d.parent=loop
    vp=d.node("Current VI's Path",[],"path")
    folder=d.node("Strip Path",[("path",vp)],"stripped path")
    program="MAIZE.Offline.exe" if offline else "MAIZE.Telemetry.exe"
    exe=d.node("Build Path",[("base path",folder),("name or relative path",d.string(program))],"appended path")
    path=d.node("Path To String",[("path",exe)],"string")
    q=d.string('"')
    cmd=d.node("Concatenate Strings",[("string",v) for v in (q,path,q)],"concatenated string")
    request=offline_inputs(d,last) if offline else last
    text=d.node("System Exec.vi",[("command line",cmd),("standard input",request),("working directory",folder)],"standard output","Call")
    ar=d.node("Spreadsheet String To Array",[("delimiter (Tab)",d.string("|")),("spreadsheet string",text),
        ("array type (2D Dbl)",d.value("Strings","array{string}","[]")),("format string",d.string("%s"))],"array")
    f=d.multi("Index Array",[("array",ar)]+[("index","")]*15,["element"]*15)
    d.parent=register
    d.add("Right",inputs="value:"+f[0],outputs="value:OUT.v")
    d.parent=loop
    zero=d.value("Zero",U32,0)
    num=[d.node("Decimal String To Number",[("string",s),("default (0L)",zero)],"number") for s in f[4:12]]
    attempt,pos,status,site,events,latched,controller,online=num
    valid=d.node("Not Equal?",[("x",online),("y",zero)],"x != y?")
    alarm=d.node("Vacuum permissions.vi",list(zip(["attempt","pos","status","site","events"],num[:5])),"alarms","Call")
    def describe(w):
        return d.node("Interlock messages.vi",[("Fault bits",w)],"Messages","Call")
    current=describe(alarm)
    mismatch=d.node("Not Equal?",[("x",alarm),("y",controller)],"x != y?")
    diff=d.select(mismatch,d.string("Controller and LabVIEW permission results differ.\n"),d.string(""))
    current=d.select(d.node("Equal To 0?",[("x",alarm)],"x = 0?"),d.string("No active interlocks."),current)
    current=d.node("Concatenate Strings",[("string",diff),("string",current)],"concatenated string")
    lat=d.select(d.node("Equal To 0?",[("x",latched)],"x = 0?"),d.string("None"),describe(latched))
    unavailable=d.string("No current controller sample.")
    def show(label,wire):
        d.indicator(label,"string",wire)
    empty=d.node("Empty String/Path?",[("string/path",f[1])],"empty?")
    link_label="Model status" if offline else "Controller link"
    link_error="Model executable unavailable" if offline else "OFFLINE - Acquisition helper unavailable"
    show(link_label,d.select(empty,d.string(link_error),f[1]))
    show("Operating state",d.select(valid,f[2],d.string("Unknown")))
    show("Chamber pressure",d.select(valid,f[3],d.string("Unavailable")))
    show("Opening outputs",d.select(valid,f[12],d.string("Unknown")))
    show("Active interlocks",d.select(valid,current,unavailable))
    show("Latched faults",d.select(valid,lat,unavailable))
    sel=d.node("Decimal String To Number",[("string",f[13]),("default (0L)",zero)],"number")
    quality=d.node("Decimal String To Number",[("string",f[14]),("default (0L)",zero)],"number")
    for i,name in enumerate(VALVES):
        pin=d.value("Offset",U32,i*2)
        picture=d.node("Offline valve lamp.vi" if offline else "Valve pilot lamp.vi",
                       [("Position word",pos),("Bit offset",pin),("Physical selectors",sel),
                                              ("Selector quality",quality)],"Lamp","Call")
        d.indicator(name,"picture",picture)
    d.node("Wait (ms)",[("milliseconds to wait",d.value("Scan interval",U32,200 if offline else 300))],"millisecond timer value")
    stop=d.add("Control",_name="End session",type="bool",style="latched",value="false",outputs="value:OUT.v")
    d.add("Condition",inputs="value:"+stop.get("uid")+".v",value="stop")
    d.build(lambda c:layout(c,offline))

def layout(c,offline=False):
    from struct import pack
    def place(name,x,y,w,h):
        o=c.fp_info[name][2].find("ddo")
        parts=o.findall("partsList/SL__arrayElement")
        if o.get("class")=="stdPict":
            width=125 if offline else 195
            o.find("bounds").text=str((0,0,57,width))
            coords={"9":(0,0,57,width),"28":(2,2,55,width-2),"16":(-19,0,-2,150)}
            for p in parts:
                code=p.findtext("partID")
                if code in coords:p.find("bounds").text=str(coords[code])
                if code=="28":p.find("bgColor").text="00E4E3DB"
                if code=="9":
                    p.find("image/ImageResID").text="-239"
                    p.find("bgColor").text="00E4E3DB"
                if code=="16":
                    p.find("image/ImageResID").text="-619"
                    p.find("bgColor").text="00E9D77F"
                    p.find("textRec/bgColor").text="00E9D77F"
                    if offline:
                        p.find("objFlags").text=str(int(p.findtext("objFlags")) | 8)
            for key in ("srcRect","totalBounds"):
                o.find(key).text=pack(">4h",0,0,53,width-4).hex().upper()
        elif o.get("class")=="stdString":
            o.find("bounds").text=str((0,0,h,w))
            for p in parts:
                code=p.findtext("partID")
                if code=="11":
                    p.find("bounds").text=str((18,4,h-4,w-4))
                if code=="9":p.find("bounds").text=str((15,0,h,w))
                if code=="16":
                    p.find("bounds").text=str((0,0,15,w))
        elif o.get("class")=="stdRing" and w:
            t,l,b,r=lvheap.parse_bounds(o.findtext("bounds"))
            o.find("bounds").text=str((t,l,b,l+w))
            for p in parts:
                if p.findtext("partID") in ("9","12"):
                    t,l,b,r=lvheap.parse_bounds(p.findtext("bounds"))
                    p.find("bounds").text=str((t,l,b,w-2))
        A.place_obj(o,y,x)
    def strip(msg,y,x,w,col,height=22,behind=False):
        lab=ET.Element("SL__arrayElement",{"class":"label","uid":str(c.alloc())})
        ET.SubElement(lab,"objFlags").text=c.LABEL_FLAGS
        ET.SubElement(lab,"howGrow").text="240"
        ET.SubElement(lab,"bounds").text=str((y-46,x,y-46+height,x+w))
        img=ET.SubElement(lab,"image",{"class":"Image"})
        ET.SubElement(img,"ImageResID").text="-619"
        ET.SubElement(lab,"bgColor").text=col
        rec=ET.SubElement(lab,"textRec",{"class":"textHair"})
        ET.SubElement(rec,"mode").text=c.LABEL_MODE
        ET.SubElement(rec,"text").text='"'+msg+'"'
        ET.SubElement(rec,"bgColor").text=col
        if behind: c.pane_z.append(lab)
        else: c.pane_z.insert(0,lab)
    strip("",41,18,829,"00E4E3DB",117,True)
    strip("",160,18,829,"00E4E3DB",118,True)
    strip("MAIZE     /     OFFLINE SIMULATION" if offline else "MAIZE     /     Vacuum control",7,18,829,"00E8CA70")
    for name,request,x,y in zip(VALVES,REQUESTS,(48,303,558,606 if offline else 618),(84,84,84,211)):
        place(name,x+105 if offline else x,y,0,0)
        if offline:
            place(request,x,y,0,0)
    strip("Click a valve request to toggle CLOSED / OPEN" if offline else "Levers follow the physical toggles",190,48,405,"00E4E3DB")
    strip("OPEN   Red        CLOSED   Green        UNKNOWN   Grey",224,48,405,"00E4E3DB")
    fields=[
        ("Controller link",18,302,395,39),("Operating state",430,302,255,39),
        ("Chamber pressure",18,352,242,39),("Opening outputs",277,352,570,39),
        ("Active interlocks",18,408,435,205),("Latched faults",470,408,377,205),
        ("End session",744,302,0,0)]
    if offline:
        fields=[
            ("Mode",18,291,156,0),("Arm / Reset",196,291,0,0),("Close / Stop",314,291,0,0),
            ("Pumpdown",436,291,0,0),("Vent sequence",546,291,0,0),("End session",742,291,0,0),
            ("Test condition",18,346,250,0),("Operating state",287,346,305,38),
            ("Chamber pressure",612,346,235,38),("Model status",18,393,250,38),
            ("Opening outputs",287,393,560,38),
            ("Active interlocks",18,447,435,185),("Latched faults",470,447,377,185)]
    for name,x,y,w,h in fields:
        place(name,x,y,w,h)
    c.fp.find("pBounds").text="(46, 0, 735, 895)"
    c.fp.find("origin").text="(50, 95)"
    pane=c.fp.find("root/paneHierarchy")
    pane.find("bounds").text="(46, 0, 735, 895)"
    for part in pane.findall("partsList/SL__arrayElement"):
        coords={"39":(0,878,672,895),"38":(672,0,689,878),"44":(672,878,689,895),"28":(0,0,672,878)}
        k=part.findtext("partID")
        if k in coords:part.find("bounds").text=str(coords[k])
        if k=="28" and part.find("bgColor") is not None:part.find("bgColor").text="00DFDFD8"

if __name__=="__main__":
    if sys.argv[1:]==["--offline"]:
        lamp(offline=True)
        panel(offline=True)
    else:
        permissions()
        messages()
        lamp()
        panel()
