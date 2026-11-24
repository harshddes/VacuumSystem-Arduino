#include "Installation.h"
#include "Controller.h"
#include <cassert>
#include <iostream>

using namespace maize;
constexpr unsigned healthy=1|2|4|8|16|64|128|256|512|1024;
struct Rack {
    Controller c;
    Snapshot s;
    Rack(Mode mode=Manual) {
        s.mode=mode; s.basic=healthy; s.positions=85; s.pressureValid=true;
        s.validPanel=true; s.processSafe=true; s.torr=0.5f;
        scan(); scan(installation::travelCloseMs);
    }
    void scan(unsigned increment=10,bool released=true) {
        s.time+=increment;
        s.roughClosure=(s.positions&3)==1 && c.closedOutput(0,s.time);
        s.ventClosure=(s.positions&12)==4 && c.closedOutput(1,s.time);
        c.tick(s,released);
    }
    void arm() {s.arm=true; scan(); s.arm=false;scan();}
    void start(){s.pump=true;scan();s.pump=false;}
    void set(unsigned selectors) {
        s.selectors=selectors;
        s.positions=(s.positions&240) | ((selectors&Rough)?2:1) | ((selectors&Vent)?8:4);
    }
};
int main() {
    // Each source condition below independently inhibits the appropriate path.
    unsigned all=healthy|2048|4096|8192,site=31;
    for(unsigned v:{1u,2u,4u,8u}) assert(evaluate(v,85,all,site,0)==0);
    for(unsigned i=0;i<5;i++) assert(evaluate(0,85,all&~(1u<<i),site,0)&(1u<<i));
    assert(evaluate(0,85,all|32,site,0)&32);
    assert(evaluate(0,213,all,site,0)&64);
    assert(evaluate(0,117,all,site,0)&128);
    assert(evaluate(0,21,all,site,0)&256);
    assert(!(evaluate(0,21,all,site,1)&256));
    assert(evaluate(0,69,all,site,0)&512);
    assert(evaluate(0,85,all,site,4)&1024);
    assert(evaluate(0,85,all,site,8)&2048);
    assert(evaluate(0,85,all,0,0)&4096);
    for(unsigned pump:{1u,4u,8u}) {
        assert(evaluate(pump|Vent,85,all,site,0)&8192);
        assert(evaluate(pump,89,all,site,0)&16384);
    }
    for(unsigned p:{86u,101u,149u,21u}) assert(evaluate(Vent,p,all,site,0)&32768);
    for(unsigned i=0;i<9;i++){
        unsigned v[]={Vent,Rough,Cryo,Turbo,Turbo,Cryo,Cryo,Turbo,Rough};
        uint32_t bit=1u<<(16+i);
        if(i<8) assert(evaluate(v[i],85,all&~(1u<<(6+i)),site,0)&bit);
        else assert(evaluate(Rough,85,all,site&~8,0)&bit);
    }
    assert(evaluate(Vent,85,all,site&~16,0)&(1u<<28));
    for(unsigned e:{16u,32u,64u,128u,256u}) assert(evaluate(0,85,all,site,e)!=0);

    Rack startup;
    startup.c=Controller();
    startup.scan();startup.arm();
    assert(!startup.c.armed());
    startup.scan(installation::travelCloseMs);startup.arm();
    assert(startup.c.armed());

    Rack r; r.set(Rough);r.scan();assert(!r.c.command);
    r.arm();assert(!r.c.command); r.set(0);r.scan();r.arm();assert(r.c.stage==Armed);
    r.set(Rough);r.scan();assert(r.c.command==Rough);
    r.set(Rough|Vent);r.scan();assert(r.c.stage==Fault && !r.c.command && (r.c.latch&8192));
    r.set(Rough);r.scan();assert(!r.c.command);r.arm();assert(!r.c.command);
    r.set(0);r.scan(80);r.arm();assert(!r.c.armed());r.arm();assert(r.c.armed());
    r.set(Turbo);r.scan();assert(r.c.command==Turbo);
    r.s.positions=69;r.scan();assert(r.c.command==Turbo); // travelling
    r.s.positions=101;r.scan();assert(r.c.command==Turbo);
    r.s.basic &= ~1024u;r.scan();assert(!r.c.command && (r.c.latch&(1u<<20)));

    Rack crossPath;crossPath.arm();crossPath.set(Rough);crossPath.scan();
    assert(crossPath.c.command==Rough);
    crossPath.set(0);crossPath.scan();
    crossPath.set(Turbo);crossPath.scan();
    assert(!crossPath.c.command && (crossPath.c.latch&(1u<<24)));
    Rack gateTravel;gateTravel.arm();gateTravel.set(Cryo);gateTravel.scan();
    gateTravel.s.positions=21;gateTravel.set(0);gateTravel.scan();
    gateTravel.set(Rough);gateTravel.scan();
    assert(!gateTravel.c.command && (gateTravel.c.latch&(1u<<24)));
    Rack t;t.arm();t.set(Cryo);t.scan();assert(t.c.command==Cryo);
    t.s.positions=21;t.scan(61);assert(t.c.latch&(1u<<25));
    Rack lost;lost.arm();lost.set(Cryo);lost.scan();lost.s.positions=149;lost.scan();
    lost.s.torr=1.5f;lost.scan();assert(lost.c.command==Cryo); // below trip after authorized entry
    lost.s.pressureValid=false;lost.scan();assert(!lost.c.command && (lost.c.latch&(1u<<21)));
    Rack stop;stop.arm();stop.set(Rough);stop.scan();stop.s.basic&=~1u;
    stop.scan();assert(!stop.c.command && stop.c.latch);
    Rack swap;swap.arm();swap.set(Rough);swap.scan();swap.s.mode=Auto;swap.scan();
    assert(!swap.c.command && !swap.c.armed());
    Rack config;config.s.arm=true;config.scan(10,false);assert(!config.c.armed());
    Rack autoRig(Auto);autoRig.s.torr=5;autoRig.arm();autoRig.start();assert(autoRig.c.command==Rough);
    autoRig.s.torr=0.5f;autoRig.scan();assert(!autoRig.c.command && autoRig.c.stage==Isolating);
    autoRig.scan(30);assert(!autoRig.c.command);autoRig.scan(40);assert(autoRig.c.command==Cryo);
    autoRig.s.positions=149;autoRig.scan();autoRig.s.vent=true;autoRig.scan();
    assert(!autoRig.c.command && autoRig.c.stage==VentPreparation);
    autoRig.s.vent=false;autoRig.s.positions=85;autoRig.s.basic&=~64u;autoRig.scan();
    assert(!autoRig.c.command);autoRig.s.basic|=64;autoRig.scan();assert(autoRig.c.command==Vent);
    autoRig.s.torr=12;autoRig.scan();assert(!autoRig.c.command && autoRig.c.stage==VentClosing);
    autoRig.scan(65);assert(autoRig.c.stage==Armed);
    Rack deadline(Auto);deadline.arm();deadline.s.torr=10;deadline.start();deadline.scan(1001);
    assert(deadline.c.latch&(1u<<26));
    Rack wrap; wrap.s.time=0xfffffff0u;wrap.arm();wrap.set(Cryo);wrap.scan();assert(wrap.c.command==Cryo);
    wrap.s.positions=21;wrap.scan(80);assert(wrap.c.latch&(1u<<25));
    std::cout<<"Controller permission, recovery, sequence and rollover checks passed\n";
}
