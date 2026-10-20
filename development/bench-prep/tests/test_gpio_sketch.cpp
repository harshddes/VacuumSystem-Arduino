// Executes the ACTUAL supplied sketch with simulated pins/time/bus.
// This does not simulate the analogue electrical behavior or the I2C library.
#include <cassert>
#include <iostream>
#include "fakes/Adafruit_MCP23X17.h"
unsigned long fakeTime=0;
int fakeLeds[20]={0};
bool fakeBus=true;
uint16_t fakeLevels=0xFFFF;
SerialFake Serial;
WireFake Wire;
#include "../firmware/gpio_interlock_bench/gpio_interlock_bench.ino"

void state(uint8_t p,bool active){if(active)fakeLevels&=~(uint16_t(1)<<p);else fakeLevels|=(uint16_t(1)<<p);}
void settle(){fakeTime+=40;loop();fakeTime+=40;loop();}
void rearm(){state(0,false);state(1,false);state(10,false);settle();state(10,true);settle();state(10,false);settle();assert(logic.out.armed);}

int main(){
 for(uint8_t p:{2,3,4,5,6,8,9})state(p,true);
 setup();fakeTime=1001;loop();
 assert(configured && !logic.out.armed && fakeLeds[A0]==LOW && fakeLeds[A1]==LOW && fakeLeds[A2]==HIGH);
 rearm();assert(fakeLeds[A2]==LOW);
 state(0,true);settle();assert(fakeLeds[A0]==HIGH && fakeLeds[A1]==LOW);
 state(4,false);settle();assert(fakeLeds[A0]==LOW && !logic.out.armed);
 state(4,true);settle();assert(fakeLeds[A0]==LOW && !logic.out.armed);
 state(10,true);settle();assert(!logic.out.armed); // held request blocks re-arm
 rearm();state(4,false);settle();state(0,true);settle();assert(fakeLeds[A0]==LOW);
 state(4,true);settle();assert(fakeLeds[A0]==LOW); // denied request was not queued
 state(0,false);settle();state(0,true);settle();assert(fakeLeds[A0]==HIGH);
 state(1,true);settle();assert(!logic.out.armed && fakeLeds[A0]==LOW && fakeLeds[A1]==LOW);
 state(1,false);settle();assert(fakeLeds[A0]==LOW); // clearing conflict doesn't reopen
 rearm();state(1,true);settle();assert(fakeLeds[A1]==HIGH);
 state(8,false);settle();assert(fakeLeds[A1]==LOW && !logic.out.armed);
 state(8,true);rearm();state(0,true);settle();assert(fakeLeds[A0]==HIGH);
 fakeBus=false;loop();assert(!configured && fakeLeds[A0]==LOW && fakeLeds[A2]==HIGH);
 fakeBus=true;fakeTime+=1001;loop();assert(configured && !logic.out.armed && fakeLeds[A0]==LOW);
 rearm();state(0,true);settle();assert(fakeLeds[A0]==HIGH);
 std::cout<<"PASS: actual GPIO sketch startup, re-arm, mapping, denial/recovery, conflict, sensor loss and bus reconnect scenarios.\n";
}
