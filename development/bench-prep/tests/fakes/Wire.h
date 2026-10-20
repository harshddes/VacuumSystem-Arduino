#pragma once
#include "Arduino.h"
extern bool fakeBus;
struct WireFake {
 uint8_t address=0;
 void begin(){}
 void setWireTimeout(unsigned long,bool){}
 void clearWireTimeoutFlag(){}
 bool getWireTimeoutFlag(){return false;}
 void beginTransmission(uint8_t a){address=a;}
 uint8_t endTransmission(){return fakeBus && address==0x21 ? 0 : 4;}
};
extern WireFake Wire;
