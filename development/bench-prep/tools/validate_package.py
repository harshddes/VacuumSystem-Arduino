#!/usr/bin/env python3
"""Check source/firmware pin agreement and the actual KiCad-exported net graph."""
import argparse
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def demand(ok,message):
    if not ok:raise AssertionError(message)

def expected(stage):
    return {n['name']:frozenset(tuple(e) for e in n['ends']) for n in stage['nets']}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--kicad',action='store_true',help='require native netlist export and SVG rendering')
    parser.add_argument('--cli',default='kicad-cli')
    args=parser.parse_args()
    data=json.loads((ROOT/'design.json').read_text())
    stages={s['id']:s for s in data['stages']}
    demand(set(stages)=={'day1-loopback','day1-rs485-logic','day2-gpio-bench'},'unexpected stage')
    for s in stages.values():
        refs={c['ref']:c for c in s['components']}
        demand(len(refs)==len(s['components']),'duplicate component reference')
        seen=set()
        for name,nodes in expected(s).items():
            demand(len(nodes)>=2,'single-ended declared connection '+name)
            for ref,p in nodes:
                demand(ref in refs and p in {x['id'] for x in refs[ref]['pins']},'invalid terminal '+ref+'.'+p)
                demand((ref,p) not in seen,'terminal on two nets')
                demand(not(ref=='U1' and p in {'D5','D6','D7','5','6','7'}),'failed Uno pin used')
                seen.add((ref,p))
    loop=expected(stages['day1-loopback'])
    demand(loop['I2C_SDA']=={('U1','A4'),('U2','SDA')},'SDA source mismatch')
    demand(loop['I2C_SCL']=={('U1','A5'),('U2','SCL')},'SCL source mismatch')
    demand(loop['UART1_LOOP']=={('U2','T1'),('U2','R1')},'UART1 loop wrong')
    demand(loop['UART2_LOOP']=={('U2','T2'),('U2','R2')},'UART2 loop wrong')
    rs=expected(stages['day1-rs485-logic'])
    demand(rs['UART1_TX']=={('U2','T1'),('U3','R')},'TTL transmit must reach adapter receive')
    demand(rs['UART1_RX']=={('U2','R1'),('U3','T')},'TTL receive must come from adapter transmit')
    used=set().union(*rs.values())
    demand(not any(('U3',p) in used for p in ['BUS12','BUSGND','A','B','EXT12','EXTGND']),'unreleased bus wiring present')
    reference=[('A0',0,'CRYO_REQUEST'),('A1',1,'VENT_REQUEST'),('A2',2,'CRYO_CLOSED'),('A3',3,'VENT_CLOSED'),('A4',4,'PRESSURE_VALID'),('A5',5,'PRESSURE_LOW'),('A6',6,'CRYO_READY'),('B0',8,'OTHER_PATHS_CLOSED'),('B1',9,'FILAMENT_OFF'),('B2',10,'REARM')]
    demand([(r['terminal'],r['library_index'],r['signal']) for r in data['input_map']]==reference,'input map drift')
    gpio=expected(stages['day2-gpio-bench'])
    for i,(p,_,name) in enumerate(reference,1):
        demand(gpio['B_'+name]=={('U2',p),('SW'+str(i),'1')},'input signal miswired: '+name)
        demand(('SW'+str(i),'2') in gpio['LOGIC_GND'],'contact return missing')
    used=set().union(*gpio.values())
    demand(('U2','ADDR0') in gpio['USB_5V'],'expander +1 address strap missing')
    demand(not any(('U3',p) in used for p in ['VLOAD']+['OUT'+str(i) for i in range(8)]),'coil connection in bench stage')
    firmware=(ROOT/'firmware/gpio_interlock_bench/gpio_interlock_bench.ino').read_text()
    match=re.search(r'inputs\[10\]\s*=\s*\{([^}]+)\}',firmware)
    demand(match and [int(x) for x in match[1].split(',')]==[r[1] for r in reference],'firmware input ordering differs')
    demand('address=0x21' in firmware,'firmware address drift')
    core=ROOT.parent/'firmware/phase1_led_demo/bench_logic.h'
    demand(core.read_text().strip()==(ROOT/'firmware/gpio_interlock_bench/bench_logic.h').read_text().strip(),'copied bench core drifted')
    rows=list(csv.DictReader((ROOT/'wire-schedule.csv').open()))
    demand(len({r['wire_id'] for r in rows})==len(rows),'duplicate wire ID')
    demand(len(rows)==sum(len(n['ends'])-1 for s in data['stages'] for n in s['nets']),'CSV connection count drift')
    for row in rows:
        stage=stages[row['stage']]
        refmap={c['ref']:c for c in stage['components']}
        nodes=expected(stage)[row['net']]
        for side in ['from','to']:
            ref=row[side+'_ref'];name=row[side+'_terminal']
            p=next(p['id'] for p in refmap[ref]['pins'] if p['name']==name)
            demand((ref,p) in nodes,'CSV endpoint on wrong net')
    print(f'PASS: {len(stages)} bench stages, {len(rows)} scheduled connections, fixed I/O/addresses, excluded field terminals.')
    if not args.kicad:return
    cli=shutil.which(args.cli)
    demand(cli is not None,'kicad-cli not found; native validation NOT RUN')
    print('KiCad:',subprocess.check_output([cli,'version'],text=True).strip())
    previews=ROOT/'previews';previews.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='ppml-net-') as temp:
        for stage in data['stages']:
            name=stage['id'];sch=ROOT/'kicad'/name/(name+'.kicad_sch')
            output=Path(temp)/(name+'.xml')
            subprocess.run([cli,'sch','export','netlist','--format','kicadxml','--output',str(output),str(sch)],check=True,capture_output=True,text=True)
            actual={}
            for n in ET.parse(output).findall('./nets/net'):
                nodes=frozenset((e.attrib['ref'],e.attrib['pin']) for e in n.findall('node'))
                if len(nodes)>=2:actual[n.attrib['name'].lstrip('/')]=nodes
            demand(actual==expected(stage),f'Native KiCad net graph differs in {name}: actual={actual}, expected={expected(stage)}')
            subprocess.run([cli,'sch','export','svg','--output',str(previews)+'/',str(sch)],check=True,capture_output=True,text=True)
            svg=previews/(name+'.svg')
            svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
            print('PASS:',name,'native parsing, exported connection graph, SVG plot')

if __name__=='__main__':main()
