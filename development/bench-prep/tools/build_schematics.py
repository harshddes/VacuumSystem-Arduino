#!/usr/bin/env python3
"""Build self-contained KiCad 7+ bench interconnect drawings and wire schedules.

These are module-terminal drawings, not module footprints or simulation models.
The electrical source of truth is design.json. Validate exported KiCad netlists
with validate_package.py after any change. No field wiring is released here.
"""
import csv
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
NS = uuid.UUID('10202026-1010-4010-8010-102020261010')

def uid(s):
    return str(uuid.uuid5(NS, s))

def q(s):
    return json.dumps(str(s))

def effects(size=1.27, justify=''):
    return f'(effects (font (size {size} {size})) {justify})'

def text(s, x, y, size=1.27):
    return f'(text {q(s)} (at {x} {y} 0) {effects(size,"(justify left)")} (uuid {uid(f"text:{s}:{x}:{y}")}))'

def wire(a, b, tag):
    return f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid(tag)}))'

def label(s, x, y, side='R'):
    just='(justify right bottom)' if side=='L' else '(justify left bottom)'
    return f'(label {q(s)} (at {x} {y} 0) {effects(1.05,just)} (uuid {uid(f"label:{s}:{x}:{y}")}))'

def symbol_definition(c):
    # Pin numbers are explicit module terminal identifiers, not IC package pins.
    # Passive interface pins intentionally avoid claiming an electrical model.
    pts = c['pins']
    top = min(p['dy'] for p in pts) - 5.08
    bottom = max(p['dy'] for p in pts) + 5.08
    w = c.get('half_width', 17.78)
    out = [f'(symbol {q(c["kind"])} (pin_names (offset 1.016)) (pin_numbers hide) (in_bom yes) (on_board no)',
           f'(property "Reference" {q(c["prefix"])} (at 0 {-top+3.81} 0) {effects()})',
           f'(property "Value" {q(c["value"])} (at 0 {-top+1.27} 0) {effects()})',
           f'(symbol {q(c["kind"]+"_0_1")} (rectangle (start {-w} {-top}) (end {w} {-bottom}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'(symbol {q(c["kind"]+"_1_1")}']
    for p in pts:
        x = -w-5.08 if p['side']=='L' else w+5.08
        angle = 0 if p['side']=='L' else 180
        out.append(f'(pin passive line (at {x} {-p["dy"]} {angle}) (length 5.08) (name {q(p["name"])} {effects(1.0)}) (number {q(p["id"])} {effects(0.85)}))')
    return '\n'.join(out)+'))'

def pin_at(c, pin):
    p = next(p for p in c['pins'] if p['id']==pin)
    w = c.get('half_width',17.78)
    return (round(c['x']+(-w-5.08 if p['side']=='L' else w+5.08),4),round(c['y']+p['dy'],4))

def build(stage):
    name = stage['id']
    folder = ROOT/'kicad'/name
    folder.mkdir(parents=True,exist_ok=True)
    root_id = uid(name)
    components = {c['ref']:c for c in stage['components']}
    out = ['(kicad_sch (version 20230121) (generator "ppml_bench_prep")',
           f'(uuid {root_id}) (paper "A3")',
           f'(title_block (title {q(stage["title"])}) (date "2026-10-20") (rev "1.0") (company "PPML bench preparation - no field outputs"))',
           '(lib_symbols']
    for c in stage['components']:
        out.append(symbol_definition(c))
    out.append(')')
    out.append(text(stage['title'],15,15,2.1))
    out.append(text('BENCH ONLY | USB 5 V | D5 / D6 / D7 unused | no chamber or coil connections',15,22,1.4))
    out.append(text('Same-name labels are electrically joined. Symbol positions do not indicate physical connector orientation.',15,28,1.15))
    connections = {}
    direct_pins=set()
    rows=[]
    for n,net in enumerate(stage['nets'],1):
        eps=net['ends']
        for ref,pin in eps:
            if (ref,pin) in connections:
                raise ValueError(f'Duplicate pin {ref}.{pin}')
            connections[(ref,pin)] = net['name']
        if len(eps)==2:
            a=pin_at(components[eps[0][0]],eps[0][1])
            b=pin_at(components[eps[1][0]],eps[1][1])
            if net['name'] in ['UART1_LOOP','UART2_LOOP']:
                outer=round(a[0]+(25.4 if net['name']=='UART1_LOOP' else 35.56),4)
                for j,(start,end) in enumerate([(a,(outer,a[1])),((outer,a[1]),(outer,b[1])),((outer,b[1]),b)]):
                    out.append(wire(start,end,f'{name}:loop:{net["name"]}:{j}'))
                out.append(label(net['name'],outer,round((a[1]+b[1])/2,4)))
                direct_pins.update(tuple(e) for e in eps)
            elif a[1]==b[1] and a[0]<b[0] and b[0]-a[0]<100:
                out.append(wire(a,b,f'{name}:direct:{net["name"]}'))
                out.append(label(net['name'],round((a[0]+b[0])/2,4),a[1]))
                direct_pins.update(tuple(e) for e in eps)
        # The schedule is a star/tree, not a count of purchased jumper leads.
        for b in eps[1:]:
            a=eps[0]
            ca,cb=components[a[0]],components[b[0]]
            pa=next(p for p in ca['pins'] if p['id']==a[1])
            pb=next(p for p in cb['pins'] if p['id']==b[1])
            rows.append([f'{stage["prefix"]}-{len(rows)+1:02}',name,net['name'],a[0],pa['name'],b[0],pb['name'],net.get('note',''),net.get('source','design')])
    for c in stage['components']:
        sid=uid(f'{name}:{c["ref"]}')
        top=min(p['dy'] for p in c['pins'])
        out.append(f'(symbol (lib_id {q("Bench:"+c["kind"])}) (at {c["x"]} {c["y"]} 0) (unit 1) (in_bom yes) (on_board no) (dnp no) (uuid {sid})')
        out.append(f'(property "Reference" {q(c["ref"])} (at {c["x"]} {c["y"]+top-8.89} 0) {effects(1.3)})')
        out.append(f'(property "Value" {q(c["value"])} (at {c["x"]} {c["y"]+top-6.35} 0) {effects(1.15)})')
        out.append(f'(instances (project {q(name)} (path {q("/"+root_id)} (reference {q(c["ref"])}) (unit 1))))')
        out.append(')')
        for p in c['pins']:
            if (c['ref'],p['id']) in direct_pins:
                continue
            a=pin_at(c,p['id'])
            netname=connections.get((c['ref'],p['id']))
            if netname is None:
                ncid=uid(f'nc:{name}:{c["ref"]}:{p["id"]}')
                out.append(f'(no_connect (at {a[0]} {a[1]}) (uuid {ncid}))')
            else:
                end=(round(a[0]+(-7.62 if p['side']=='L' else 7.62),4),a[1])
                out.append(wire(a,end,f'{name}:{c["ref"]}:{p["id"]}'))
                out.append(label(netname,*end,side=p['side']))
    for i,note in enumerate(stage.get('notes',[])):
        out.append(text(note,15,stage.get('notes_y',180)+i*6.35,1.25))
    out.append(')')
    # Embedded symbols are renamed to the full library id in lib_symbols only.
    content='\n'.join(out)+'\n'
    for c in stage['components']:
        content=content.replace('(symbol '+q(c['kind'])+' ', '(symbol '+q('Bench:'+c['kind'])+' ',1)
    (folder/(name+'.kicad_sch')).write_text(content)
    pro={'meta':{'filename':name+'.kicad_pro','version':1},'text_variables':{'BUILD_SCOPE':'BENCH_ONLY'},'schematic':{}}
    (folder/(name+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
    # A project-local library also allows future additions using Add Symbol.
    library='(kicad_symbol_lib (version 20220914) (generator "ppml_bench_prep")\n'+'\n'.join(symbol_definition(c) for c in stage['components'])+'\n)\n'
    (folder/'Bench.kicad_sym').write_text(library)
    (folder/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Bench")(type "KiCad")(uri "${KIPRJMOD}/Bench.kicad_sym")(options "")(descr "Bench module interfaces; no footprints or simulation models")))\n')
    return rows

def main():
    data=json.loads((ROOT/'design.json').read_text())
    rows=[]
    for stage in data['stages']:
        rows.extend(build(stage))
    with (ROOT/'wire-schedule.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['wire_id','stage','net','from_ref','from_terminal','to_ref','to_terminal','instruction','source_id'])
        writer.writerows(rows)
    with (ROOT/'pin-map.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['board','terminal','library_index','signal','control','active_state'])
        for row in data['input_map']:
            writer.writerow(['Adafruit 5346 MCP23017 at 0x21',row['terminal'],row['library_index'],row['signal'],row['control'],'grounded=true'])
    print(f'Generated {len(data["stages"])} KiCad projects and {len(rows)} connection rows.')

if __name__=='__main__':
    main()
