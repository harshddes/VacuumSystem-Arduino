"""Rebuild editable development diagrams; Python standard library only.
SVGs use vacuum/IEC-style connection symbols with an explicit convention note.
All field drawings are conceptual until the equipment survey is complete.
"""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent
W,H=842,595
INK='#111111'; GRAY='#404040'; LIGHT='#D8D8D4'; TEAL='#1F6F5F'
class Sheet:
 def __init__(self,title,subtitle,number,slug):
  self.ops=[];self.title=title;self.number=number;self.slug=slug
  self.text(30,30,title,18,bold=True)
  self.text(30,50,subtitle,9,color=GRAY)
  self.line(30,62,812,62,color=LIGHT)
  self.line(30,556,812,556,color=LIGHT)
  self.text(30,574,'MAIZE  |  Uno R3  |  9 Oct 2026  |  Concept / bench only; not a field wiring release',8.5,color=GRAY)
  self.text(812,574,f'{number} / 4',9,align='right',color=GRAY)
 def line(self,x1,y1,x2,y2,color=INK,width=1.4,dash=False):
  self.ops.append(dict(kind='line',x1=x1,y1=y1,x2=x2,y2=y2,color=color,width=width,dash=dash))
 def poly(self,pts,close=False,color=INK,width=1.4,fill=None):
  self.ops.append(dict(kind='poly',pts=pts,close=close,color=color,width=width,fill=fill))
 def rect(self,x,y,w,h,fill='white',color=INK,width=1.2,r=0):
  self.ops.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,color=color,width=width,r=r))
 def circle(self,x,y,r,fill='white',color=INK,width=1.4):
  self.ops.append(dict(kind='circle',x=x,y=y,r=r,fill=fill,color=color,width=width))
 def text(self,x,y,s,size=10,bold=False,color=INK,align='left'):
  self.ops.append(dict(kind='text',x=x,y=y,s=s,size=size,bold=bold,color=color,align=align))
 def lines(self,x,y,lines,size=10,leading=15,**kw):
  for i,t in enumerate(lines): self.text(x,y+i*leading,t,size,**kw)
 def block(self,x,y,w,h,head,body):
  self.rect(x,y,w,h,color=GRAY)
  self.text(x+10,y+18,head,10,bold=True)
  self.lines(x+10,y+34,body,8.5,12)
 def gauge(self,x,y,tag,label):
  self.circle(x,y,15)
  self.poly([(x-8,y-7),(x,y+8),(x+8,y-7)])
  self.line(x-7,y,x+7,y)
  self.text(x+24,y-3,tag,10,bold=True)
  self.text(x+24,y+11,label,8.5)
 def valve(self,x,y,tag,label,vertical=False,gate=True,act=None,labels=True):
  def p(u,v): return (x-v,y+u) if vertical else (x+u,y+v)
  self.poly([p(-13,-10),p(0,0),p(-13,10)],close=True,fill='white')
  self.poly([p(13,-10),p(0,0),p(13,10)],close=True,fill='white')
  if gate:self.poly([p(0,-10),p(0,10)])
  if act:
   self.poly([p(0,0),p(0,-28)])
   if act=='manual':self.poly([p(-7,-28),p(7,-28)])
   else:
    q=[p(-5,-42),p(5,-42),p(5,-28),p(-5,-28)]
    self.poly(q,close=True,fill='white')
    if act=='solenoid':self.poly([p(-5,-42),p(5,-28)])
  if labels:
   if vertical:self.lines(x+57,y-3,[tag,label],9,14)
   else:self.lines(x-13,y+27,[tag,label],9,14)
 def pump(self,x,y,kind,tag,label,r=27,labelSide='right'):
  self.circle(x,y,r)
  self.poly([(x-r*.9,y-r*.43),(x-r*.38,y+r*.88)])
  self.poly([(x+r*.9,y-r*.43),(x+r*.38,y+r*.88)])
  if kind=='cryo':
   self.line(x-12,y+9,x+12,y+9)
   for a in range(0,360,60):
    aa=math.radians(a); dx,dy=math.cos(aa),math.sin(aa)
    self.line(x,y-5,x+10*dx,y-5+10*dy,width=1)
    for side in [-1,1]:
     self.line(x+7*dx,y-5+7*dy,x+5*dx+side*3*dy,y-5+5*dy-side*3*dx,width=.9)
  elif kind=='turbo':
   self.circle(x,y-3,10);self.circle(x,y-3,5)
  elif kind=='scroll':
   pts=[]
   for n in range(100):
    a=n*math.pi*3.8/99; rr=2+8*n/99;pts.append((x+rr*math.cos(a),y-3+rr*math.sin(a)))
   self.poly(pts,width=1)
  if labelSide=='right':self.lines(x+r+12,y-2,[tag,label],9,14)
  else:self.lines(x,y+r+20,[tag,label],9,14,align='center')
 def restriction(self,x,y):
  self.poly([(x-12,y-10),(x-5,y-3),(x+5,y-3),(x+12,y-10)])
  self.poly([(x-12,y+10),(x-5,y+3),(x+5,y+3),(x+12,y+10)])
 def chamber(self,x,y,w,h,tag,sub):
  self.rect(x,y,w,h,r=18)
  self.text(x+w/2,y+h/2-3,tag,12,bold=True,align='center')
  self.text(x+w/2,y+h/2+16,sub,9,align='center')
 def vacuumLegend(self):
  self.line(30,496,812,496,color=LIGHT)
  self.lines(30,512,['Solid lines: vacuum/gas path. Tags: C chamber; G gauge; V valve; P pump. Junctions join; no hidden bypass assumed.',
   'Valve/gauge conventions adapted from Leybold. Pump family marks are explanatory; not a standards certification.',
   'Port sizes, gate models, operating limits, pilot supply and failure behavior: verify before field wiring.'],8.5,14,color=GRAY)

s1=Sheet('One real cryo gate first','Proposed test stand · reported Cryo-Torr 8 / IDP-15 / IGM402YFD · gate and plumbing require survey.',1,'test-stand-concept')
s1.chamber(323,142,194,86,'C-101  Test chamber','Volume and ports: TBD')
s1.line(420,111,420,142);s1.gauge(420,96,'G-101','IGM402YFD + CG if present')
s1.line(420,228,420,271);s1.line(420,297,420,365)
s1.valve(420,284,'V-101  Cryo gate','Pilot / actuation: verify',vertical=True,act='pneumatic')
s1.text(484,323,'OPEN + CLOSED proof: identify',8.5,color=GRAY)
s1.pump(420,395,'cryo','P-101','Cryo-Torr 8 (reported)',r=30,labelSide='below')
s1.text(420,475,'Reported installed',10,bold=True,color=TEAL,align='center')
s1.line(323,182,150,182);s1.line(150,182,150,271);s1.line(150,297,150,365)
s1.valve(150,284,'V-102','Rough isolation',vertical=True,gate=False,act='manual')
s1.pump(150,395,'scroll','P-102','IDP-15 (proposed)',r=30,labelSide='right')
s1.line(150,425,150,468);s1.text(150,483,'To approved exhaust',8.5,align='center')
s1.lines(35,112,['Identify a pre-evacuation route.','This branch is not confirmed installed.'],9,14,color=GRAY)
s1.line(517,182,601,182);s1.line(627,182,699,182);s1.line(723,182,796,182)
s1.valve(614,182,'V-103','Vent; type TBD',gate=False)
s1.restriction(711,182);s1.text(711,222,'Metered flow',8.5,align='center')
s1.lines(780,135,['Approved vent gas','Route / source TBD'],9,14,align='right')
s1.lines(565,365,['LIVE TEST REQUIRES', 'Valid chamber pressure + cryo cold/ready', 'Known roughing/vent state and allowed Δp', 'Real valve feedback; verified fault response'],9,16)
s1.vacuumLegend()

s2=Sheet('Future MAIZE vacuum paths','Functional concept · do not infer the actual backing/roughing routing from this proposed arrangement.',2,'maize-vacuum-concept')
s2.chamber(248,124,345,74,'C-201  MAIZE','All chamber-to-pump paths must be surveyed')
s2.line(340,110,340,124);s2.gauge(340,95,'G-201','Chamber pressure')
# Cryo and roughing branches leave the chamber laterally; turbo leaves its bottom.
s2.poly([(248,157),(145,157),(145,270)])
s2.line(145,296,145,332)
s2.valve(145,283,'V-201','Cryo gate',vertical=True,act='pneumatic')
s2.pump(145,361,'cryo','P-201','Cryopump',r=29,labelSide='below')
s2.line(420,198,420,257);s2.line(420,283,420,303)
s2.valve(420,270,'V-202','Turbo gate',vertical=True,act='pneumatic')
s2.pump(420,332,'turbo','P-202','Turbopump',r=29)
s2.line(420,361,420,426)
s2.line(420,397,491,397);s2.gauge(506,397,'G-202','Foreline; if required')
s2.pump(420,450,'general','P-204','Backing source; arrangement TBD',r=24,labelSide='right')
s2.line(420,474,420,483);s2.text(408,484,'Exhaust',8.5,align='right')
s2.poly([(566,198),(665,198),(665,270)])
s2.line(665,296,665,332)
s2.valve(665,283,'V-203','Rough gate',vertical=True,act='pneumatic')
s2.pump(665,361,'scroll','P-203','Scroll roughing',r=29,labelSide='right')
s2.line(665,390,665,434);s2.text(665,449,'To approved exhaust',8.5,align='center')
s2.line(593,151,685,151);s2.line(711,151,753,151);s2.line(777,151,808,151)
s2.valve(698,151,'V-204','Vent',gate=False)
s2.restriction(765,151);s2.text(785,108,'Approved vent gas',8.5,align='right')
s2.lines(30,437,['Backing shown as a separate function.', 'A shared scroll requires verified routing', 'and additional branch interlocks.'],8.5,14,color=GRAY)
s2.vacuumLegend()

s3=Sheet('Uno R3 decisions; separate field interfaces','Functional electrical / pneumatic architecture · this is not a connector pinout or released coil wiring.',3,'control-architecture')
s3.block(30,100,195,65,'Panel requests',['MANUAL / OFF / AUTO; ARM','Existing switches: contacts to verify'])
s3.block(30,202,195,71,'Physical position proofs',['OPEN and CLOSED per valve','Electrical type / healthy state: TBD'])
s3.block(30,311,195,65,'Equipment readiness',['Cryo cold; turbo ready; backing','Pumps keep their existing controls'])
s3.block(294,204,160,117,'Arduino Uno R3',['One permission function','Manual requests now','Sequence requests later','Boot: opening inhibited'])
s3.block(294,100,160,59,'Readout: laptop first',['Pressure + unit + validity','Panel readout in final assembly'])
s3.block(30,417,195,67,'Commercial gauge/controller',['Hornet IGM402YFD + CG','Model / protocol / range: verify'])
s3.block(272,417,188,67,'Conditioned pressure interface',['Hornet RS485; isolated interface','Validate channel, units and age'])
s3.block(520,204,120,88,'Rated coil driver',['Independent inhibit','Load + suppression','matched to pilot'])
s3.block(690,204,120,88,'Pilot solenoid',['One or two coils?','Spool / ports: TBD','Voltage: TBD'])
s3.block(515,100,185,59,'Separate field power',['Rated supply + protection','Uno R3 does not power the coil'])
s3.block(600,335,210,62,'Regulated actuator gas',['Correct gas and pressure from manual','Supply loss / stored energy: assess'])
s3.block(570,428,240,56,'Gate actuator + position sensors',['Actual motion must agree with command','Fail position depends on installed hardware'])
for y in [132,237,344]:
 s3.poly([(225,y),(258,y),(258,250),(294,250)],color=GRAY,width=1)
s3.text(30,394,'Field inputs require appropriate conditioning / isolation.',8.5,color=GRAY)
s3.line(374,204,374,159,color=TEAL,width=1.6,dash=True)
s3.line(454,248,520,248,color=TEAL,width=1.6,dash=True)
s3.line(640,248,690,248,width=2)
s3.poly([(578,159),(578,204)],width=2)
s3.poly([(750,335),(750,292)],color=GRAY,width=1.8)
s3.poly([(810,260),(822,260),(822,413),(735,413),(735,428)],color=GRAY,width=1.8)
s3.line(225,450,272,450,color=TEAL,dash=True)
s3.poly([(366,417),(366,321)],color=TEAL,width=1.6)
s3.text(370,366,'Validated data',8.5)
s3.line(30,502,812,502,color=LIGHT)
s3.lines(30,519,['Signals: fine lines; Uno R3 output/display links dashed. Coil power: heavy lines. Pneumatic route: grey heavy line at right.',
 'OPEN drive needs independent supervision. Position proofs return through inputs. Cryogenic services are separate.'],8.5,16,color=GRAY)

s4=Sheet('USB bench: switches in, LEDs out','Arduino Uno R3, 5 V · simulated two-branch exercise · no live panel, gauge, driver or valve connections.',4,'phase1-uno')
s4.rect(298,104,205,376)
s4.text(400,126,'Arduino Uno R3',12,bold=True,align='center')
s4.text(400,144,'INPUT_PULLUP on D2–D11',8.5,align='center')
s4.text(400,472,'GND',9,align='center')
s4.line(400,480,400,490);s4.line(393,490,407,490);s4.line(395,494,405,494);s4.line(398,498,402,498)
s4.line(400,73,400,104);s4.text(415,91,'USB power; 20 wires',9)
s4.line(50,166,50,462)
inputs=[('D2','Cryo OPEN request'),('D3','Vent OPEN request'),('D4','Cryo CLOSED (sim)'),('D5','Vent CLOSED (sim)'),('D6','Pressure valid'),('D7','Cryo pressure band'),('D8','Cryo ready'),('D9','Other pump paths closed'),('D10','Filament / process safe'),('D11','ARM / RESET (momentary)')]
for n,(pin,lab) in enumerate(inputs):
 y=171+n*31
 s4.line(50,y,79,y);s4.circle(81,y,2,fill='white',width=.8);s4.circle(104,y,2,fill='white',width=.8)
 s4.line(83,y,101,y-10,width=1)
 s4.line(106,y,298,y,width=1)
 s4.text(115,y-7,lab,8.5);s4.text(309,y+3,pin,9,bold=True)
s4.text(60,478,'GND',9)
s4.line(50,462,38,462);s4.line(38,462,38,468);s4.line(31,468,45,468);s4.line(33,472,43,472);s4.line(36,476,40,476)
s4.line(778,212,778,426)
for i,(pin,lab) in enumerate([('A0','Cryo OPEN allowed'),('A1','Vent OPEN allowed'),('A2','Disarmed / rejected')]):
 y=212+i*95
 s4.text(490,y+3,pin,9,bold=True,align='right')
 s4.line(503,y,570,y);s4.rect(570,y-7,37,14);s4.text(588,y-14,'470 Ω',9,align='center')
 s4.line(607,y,650,y)
 # Diode triangle, cathode bar and light arrows: each LED has its own resistor.
 s4.poly([(650,y-9),(650,y+9),(665,y)],close=True,fill='white');s4.line(667,y-10,667,y+10)
 s4.line(667,y,778,y)
 for dx in [0,10]:
  s4.line(660+dx,y-13,669+dx,y-22,width=1)
  s4.poly([(664+dx,y-22),(669+dx,y-22),(669+dx,y-17)],width=1)
 s4.text(624,y+33,lab,9)
s4.text(778,449,'GND',9,align='center')
s4.line(778,426,778,432);s4.line(771,432,785,432);s4.line(773,436,783,436);s4.line(776,440,780,440)
s4.lines(30,510,['Every switch connects its pin to GND when asserted. OPEN requests start released; press/reset, then make a fresh request.',
 'LEDs represent logical permission, not valve position. Other pump valves are combined into one simulated input in this desk demo.',
 'The included sketch is a teaching / logic test artifact. It does not implement physical motion timing, real pressure or field fault handling.'],8.5,15,color=GRAY)

sheets=[s1,s2,s3,s4]

def svg(sheet):
 root=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',viewBox=f'0 0 {W} {H}',width=str(int(W*1.5)),height=str(int(H*1.5)),role='img')
 ET.SubElement(root,'title').text=sheet.title
 ET.SubElement(root,'rect',x='0',y='0',width=str(int(W*1.5)),height=str(int(H*1.5)),fill='white')
 for o in sheet.ops:
  k=o['kind'];a={'stroke':o['color'],'stroke-width':str(o.get('width',1)),'fill':o.get('fill') or 'none'}
  if o.get('dash'):a['stroke-dasharray']='4 3'
  if k=='line':ET.SubElement(root,'line',**{p:str(o[p]) for p in ['x1','x2','y1','y2']},**a)
  elif k=='rect':ET.SubElement(root,'rect',x=str(o['x']),y=str(o['y']),width=str(o['w']),height=str(o['h']),rx=str(o['r']),**a)
  elif k=='circle':ET.SubElement(root,'circle',cx=str(o['x']),cy=str(o['y']),r=str(o['r']),**a)
  elif k=='poly':ET.SubElement(root,'polygon' if o['close'] else 'polyline',points=' '.join(f'{x},{y}' for x,y in o['pts']),**a)
  else:
   ET.SubElement(root,'text',x=str(o['x']),y=str(o['y']),fill=o['color'],**{'font-family':'DejaVu Sans, Arial, sans-serif','font-size':str(o['size']),'font-weight':'700' if o['bold'] else '400','text-anchor':{'left':'start','right':'end','center':'middle'}[o['align']]}).text=o['s']
 return ET.tostring(root,encoding='unicode')

def drawio(sheets):
 mx=ET.Element('mxfile',host='app.diagrams.net',version='24.0.0')
 for sh in sheets:
  dia=ET.SubElement(mx,'diagram',name=f'{sh.number} {sh.title}',id=sh.slug)
  model=ET.SubElement(dia,'mxGraphModel',dx='842',dy='595',grid='1',gridSize='10',page='1',pageScale='1',pageWidth='842',pageHeight='595')
  rr=ET.SubElement(model,'root');ET.SubElement(rr,'mxCell',id='0');ET.SubElement(rr,'mxCell',id='1',parent='0')
  count=1
  for o in sh.ops:
   k=o['kind'];count+=1
   sty=f"strokeColor={o['color']};strokeWidth={o.get('width',1)};fillColor={o.get('fill') or 'none'};"
   if k=='text':
    sw=len(o['s'])*o['size']*.61+5
    x=o['x']-(sw if o['align']=='right' else sw/2 if o['align']=='center' else 0)
    cell=ET.SubElement(rr,'mxCell',id=str(count),value=o['s'],vertex='1',parent='1',style=f"text;html=0;strokeColor=none;fillColor=none;align={o['align']};verticalAlign=middle;whiteSpace=nowrap;rounded=0;fontFamily=DejaVu Sans;fontSize={o['size']};fontStyle={1 if o['bold'] else 0};fontColor={o['color']};spacing=0;")
    ET.SubElement(cell,'mxGeometry',x=str(x),y=str(o['y']-o['size']),width=str(sw),height=str(o['size']*1.25),**{'as':'geometry'})
   elif k in ['circle','rect']:
    if k=='circle':x,y,w,h=o['x']-o['r'],o['y']-o['r'],2*o['r'],2*o['r'];sty+='ellipse;'
    else:x,y,w,h=o['x'],o['y'],o['w'],o['h'];sty+=f"rounded={1 if o['r'] else 0};arcSize=20;"
    cell=ET.SubElement(rr,'mxCell',id=str(count),vertex='1',parent='1',style=sty)
    ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
   else:
    pts=[(o['x1'],o['y1']),(o['x2'],o['y2'])] if k=='line' else o['pts']+([o['pts'][0]] if o['close'] else [])
    # Native editable line segments; no embedded screenshot.
    for n in range(len(pts)-1):
     count+=1;cell=ET.SubElement(rr,'mxCell',id=str(count),edge='1',parent='1',style=sty+f"endArrow=none;startArrow=none;rounded=0;dashed={1 if o.get('dash') else 0};")
     geo=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
     for p,name in [(pts[n],'sourcePoint'),(pts[n+1],'targetPoint')]:ET.SubElement(geo,'mxPoint',x=str(p[0]),y=str(p[1]),**{'as':name})
 return ET.tostring(mx,encoding='unicode')

for sh in sheets:
    (OUT/f'{sh.slug}.svg').write_text(svg(sh), encoding='utf-8')
(OUT/'maize-uno.drawio').write_text(drawio(sheets), encoding='utf-8')
print('Built four SVG diagrams and the editable diagrams.net file.')
