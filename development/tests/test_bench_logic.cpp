#include <cassert>
#include <iostream>
#include "../firmware/phase1_led_demo/bench_logic.h"
Inputs good(){Inputs i;i.cryoClosed=i.ventClosed=i.pressureValid=i.pressureBand=i.cryoReady=i.otherPathsClosed=i.filamentProcessSafe=true;return i;}
void arm(BenchLogic &b,Inputs &i){i.reset=false;b.tick(i);i.reset=true;b.tick(i);i.reset=false;b.tick(i);assert(b.out.armed);}
int main(){
 int n=0;
 // Every combination of seven sensor flags and both request levels.
 for(int sensors=0;sensors<128;sensors++)for(int requests=0;requests<4;requests++){
  BenchLogic b;Inputs i=good();arm(b,i);
  i.cryoClosed=sensors&1;i.ventClosed=sensors&2;i.pressureValid=sensors&4;
  i.pressureBand=sensors&8;i.cryoReady=sensors&16;i.otherPathsClosed=sensors&32;i.filamentProcessSafe=sensors&64;
  i.cryoRequest=requests&1;i.ventRequest=requests&2;b.tick(i);
  assert(!(b.out.cryo&&b.out.vent));
  if(b.out.cryo)assert(i.ventClosed&&i.pressureValid&&i.pressureBand&&i.cryoReady);
  if(b.out.vent)assert(i.cryoClosed&&i.otherPathsClosed&&i.filamentProcessSafe);
  if(requests==3)assert(!b.out.armed&&!b.out.cryo&&!b.out.vent);
  n++;
 }
 {BenchLogic b;Inputs i=good();i.cryoRequest=true;b.tick(i);i.reset=true;b.tick(i);assert(!b.out.cryo&&!b.out.armed);n++;}
 {BenchLogic b;Inputs i=good();arm(b,i);i.pressureValid=false;i.cryoRequest=true;b.tick(i);i.pressureValid=true;b.tick(i);assert(!b.out.cryo);i.cryoRequest=false;b.tick(i);i.cryoRequest=true;b.tick(i);assert(b.out.cryo);n++;}
 {BenchLogic b;Inputs i=good();arm(b,i);i.cryoRequest=true;b.tick(i);assert(b.out.cryo);i.cryoReady=false;b.tick(i);assert(!b.out.cryo&&!b.out.armed);i.cryoReady=true;b.tick(i);assert(!b.out.cryo);n++;}
 {BenchLogic b;Inputs i=good();arm(b,i);i.ventRequest=true;b.tick(i);assert(b.out.vent);i.cryoClosed=false;b.tick(i);assert(!b.out.vent&&!b.out.armed);n++;}
 {BenchLogic b;Inputs i=good();arm(b,i);i.cryoRequest=i.ventRequest=true;b.tick(i);i.cryoRequest=i.ventRequest=false;b.tick(i);assert(!b.out.armed);n++;}
 {BenchLogic b;Inputs i=good();arm(b,i);i.pressureValid=false;i.ventRequest=true;b.tick(i);assert(b.out.vent);n++;}
 {BenchLogic b;Inputs i=good();i.reset=true;b.tick(i);b.tick(i);assert(!b.out.armed);i.reset=false;b.tick(i);i.reset=true;b.tick(i);assert(b.out.armed);n++;}
 std::cout<<"PASS: "<<n<<" core scenarios; no hardware tested.\n";
}
