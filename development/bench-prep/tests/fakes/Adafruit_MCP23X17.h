#pragma once
#include "Wire.h"
extern uint16_t fakeLevels;
struct Adafruit_MCP23X17 {
 bool begin_I2C(uint8_t a){return fakeBus && a==0x21;}
 void pinMode(uint8_t,int){}
 void digitalWrite(uint8_t p,int v){if(v)fakeLevels|=(uint16_t(1)<<p);else fakeLevels&=~(uint16_t(1)<<p);}
 uint16_t readGPIOAB(){return fakeLevels;}
};
