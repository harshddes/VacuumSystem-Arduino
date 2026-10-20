#!/usr/bin/env python3
"""Run source checks and actual-sketch host scenarios; optionally native KiCad."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--kicad',action='store_true')
    p.add_argument('--cli',default='kicad-cli')
    args=p.parse_args()
    cmd=[sys.executable,str(ROOT/'tools/validate_package.py')]
    if args.kicad:cmd+=['--kicad','--cli',args.cli]
    subprocess.run(cmd,check=True)
    with tempfile.TemporaryDirectory(prefix='ppml-check-') as temp:
        for source,includes,name in [
            (ROOT.parent/'tests/test_bench_logic.cpp',[],'core'),
            (ROOT/'tests/test_gpio_sketch.cpp',['-I',str(ROOT/'tests/fakes')],'actual-gpio-sketch')]:
            output=Path(temp)/name
            subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror',*includes,str(source),'-o',str(output)],check=True)
            subprocess.run([str(output)],check=True)
    print('Physical hardware is NOT TESTED. AVR target builds are recorded separately.')

if __name__=='__main__':main()
