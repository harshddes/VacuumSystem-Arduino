"""Regression checks. Running this script sends packets only on loopback.
Set CXX to a C++ compiler, for example 'clang++' or 'C:/tools/zig.exe c++'.
"""
import csv
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import tempfile
import threading

ROOT=Path(__file__).resolve().parent
FW=ROOT/"firmware/OptaTelemetry"

def compile_controller(directory):
    # Exercise the actual controller with non-deployable unit-test limits.
    for src in ("PermissionRules.h","Controller.h"):
        shutil.copy(FW/src,directory/src)
    fixture=(FW/"Installation.h").read_text()
    values={"autoPathQualified":"true","travelOpenMs":"60","travelCloseMs":"60",
            "pressureDwellMs":"5","roughdownMs":"1000","ventMs":"1000",
            "cryoEnterTorr":"1","cryoTripTorr":"2","turboEnterTorr":"1","turboTripTorr":"2",
            "roughCrossoverTorr":"0.9","ventCompleteTorr":"10","allowedPumpMasks":"4370"}
    for key,val in values.items():
        fixture,count=re.subn(r'\b'+key+r'=(false|0)\b',key+"="+val,fixture)
        assert count==1,key
    (directory/"Installation.h").write_text(fixture)
    compiler=shlex.split(os.environ.get("CXX","c++").replace("\\","/"))
    exe=directory/"controller-test.exe"
    subprocess.run([*compiler,"-std=c++14","-I",str(directory),str(ROOT/"tests/controller.cpp"),"-o",str(exe)],check=True)
    subprocess.run([str(exe)],check=True)

def transport(directory):
    exe=directory/"MAIZE.Telemetry.exe"
    shutil.copy2(ROOT/exe.name,exe)
    (directory/"Opta.address").write_text("127.0.0.1")
    def scan(memory=""):
        env=dict(os.environ,MAIZE_LOG_DIRECTORY=str(directory/"logs"))
        p=subprocess.run([str(exe)],input=memory,text=True,capture_output=True,check=True,timeout=5,env=env)
        row=p.stdout.split("|")
        assert len(row)==15,row
        return row
    def frame(nonce,seq,**override):
        fields=["MAIZE3",nonce,seq,seq*20,1,1,1,86,1,16351,31,0,0,0,1,"0.0004",120,15]
        for k,v in override.items(): fields[int(k)]=v
        return ",".join(map(str,fields))
    cases=[lambda n:frame(n,1),lambda n:frame(n,1),lambda n:frame(n,3,**{"15":"-","7":0,"17":0}),
           lambda n:frame("ffffffff" if n!="ffffffff" else "00000000",4),
           lambda n:frame(n,5,**{"15":"1100"}),lambda n:frame(n,6,**{"13":2**31}),
           lambda n:"MAIZE2,old",lambda n:frame(n,7,**{"6":2,"7":89,"14":0}),
           lambda n:frame(n,8,**{"17":0})]
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as server:
        server.bind(("127.0.0.1",44820))
        server.settimeout(5)
        def answer():
            for case in cases:
                query,peer=server.recvfrom(128)
                match=re.fullmatch(rb"MAIZE3 R ([a-f0-9]{8})\n",query)
                assert match
                server.sendto(case(match[1].decode()).encode(),peer)
        t=threading.Thread(target=answer,daemon=True);t.start()
        memory=""
        rows=[]
        for _ in cases:
            row=scan(memory);memory=row[0];rows.append(row)
        t.join(5)
        assert not t.is_alive()
    assert rows[0][11]=="1" and rows[0][12]=="Roughing OPEN" and "CG1" in rows[0][3]
    assert rows[2][5]=="0" and rows[2][3]=="Unavailable"
    assert all(rows[i][11]=="0" and rows[i][5]=="0" for i in (1,3,4,5,6,8))
    assert rows[7][12]=="Let-up request inhibited"
    assert scan(memory)[11]=="0"
    logs=list((directory/"logs").glob("*.csv"))
    assert logs
    logged=[r for f in logs for r in csv.DictReader(f.read_text().splitlines())]
    assert any(r["open_outputs"]=="1" and r["pressure_torr"]=="0.0004" for r in logged)
    assert any(r["link"].startswith("OFFLINE") and r["positions"]=="" for r in logged)
    (directory/"Opta.address").write_text("uno")
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as server:
        server.bind(("127.0.0.1",44820))
        server.settimeout(5)
        def bench_reply():
            for sequence in (30,31):
                query,peer=server.recvfrom(128)
                match=re.fullmatch(rb"UNO3 R ([a-f0-9]{8})\n",query)
                assert match
                line=frame(match[1].decode(),sequence,**{"15":"0.01"})
                if sequence==30:
                    line=line.replace("MAIZE3,","UNO3,",1)
                server.sendto(line.encode(),peer)
        t=threading.Thread(target=bench_reply,daemon=True);t.start()
        bench=scan()
        wrong_protocol=scan(bench[0])
        t.join(5)
        assert not t.is_alive()
    assert "UNO R3 BENCH" in bench[1] and bench[3]=="0.01 bench units / A2"
    assert "mismatch" in wrong_protocol[1]
    assert "no current USB sample" in scan(wrong_protocol[0])[1]
    assert any("bench_pressure_input" in p.read_text().splitlines()[0] for p in (directory/"logs").glob("*-uno.csv"))
    print("Opta and Uno transport checks passed")

if __name__=="__main__":
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        transport(folder)
        compile_controller(folder)
