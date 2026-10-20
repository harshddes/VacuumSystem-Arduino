// BENCH ONLY. No actual field signals or coil drivers may be connected to outputs.
// Matches day2-gpio-bench.kicad_sch and pin-map.csv. USB Serial 115200.
#include <Wire.h>
#include <Adafruit_MCP23X17.h>
#include "bench_logic.h"

Adafruit_MCP23X17 mcp;
BenchLogic logic;
const uint8_t address=0x21;
// A0-A6, B0-B2 on the EXPANDER. A7 and B7 deliberately unused as inputs.
const uint8_t inputs[10]={0,1,2,3,4,5,6,8,9,10};
const uint8_t leds[3]={A0,A1,A2}; // These three are UNO pins, not expander pins.
bool raw[10]={false},stable[10]={false};
unsigned long changed[10]={0};
unsigned long lastReport=0,lastRetry=0;
bool configured=false;

void lamps(bool cryo,bool vent,bool fault) {
  digitalWrite(leds[0],cryo?HIGH:LOW);
  digitalWrite(leds[1],vent?HIGH:LOW);
  digitalWrite(leds[2],fault?HIGH:LOW);
}

bool ping() {
  Wire.beginTransmission(address);
  const uint8_t result=Wire.endTransmission();
  return result==0 && !Wire.getWireTimeoutFlag();
}

void loseBus() {
  lamps(false,false,true);
  logic=BenchLogic(); // Reconnect never substitutes for a deliberate re-arm.
  configured=false;
  Wire.clearWireTimeoutFlag();
}

void setup() {
  for(uint8_t p:leds) {digitalWrite(p,LOW);pinMode(p,OUTPUT);}
  lamps(false,false,true);
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000,true);
  Serial.println(F("BENCH ONLY - MCP 0x21; A7/B7 unused; 6318 loads disconnected"));
}

void loop() {
  const unsigned long now=millis();
  if(!configured) {
    lamps(false,false,true);
    if(now-lastRetry<1000) return;
    lastRetry=now;
    Wire.clearWireTimeoutFlag();
    if(!mcp.begin_I2C(address) || !ping()) {
      Serial.println(F("MCP OFFLINE: check 5V, GND, SDA/SCL and +1 address setting"));
      return;
    }
    for(uint8_t p:inputs) mcp.pinMode(p,INPUT_PULLUP);
    // Output-only unused A7/B7 avoid changing-input erratum.
    mcp.digitalWrite(7,LOW);mcp.pinMode(7,OUTPUT);
    mcp.digitalWrite(15,LOW);mcp.pinMode(15,OUTPUT);
    const uint16_t levels=mcp.readGPIOAB();
    if(!ping()) {loseBus();return;}
    for(uint8_t i=0;i<10;i++) {
      raw[i]=stable[i]=!(levels & (uint16_t(1)<<inputs[i]));
      changed[i]=now;
    }
    configured=true;
    logic=BenchLogic();
    Serial.println(F("MCP ONLINE. Release requests and REARM, then press REARM."));
  }
  if(!ping()) {loseBus();return;}
  const uint16_t levels=mcp.readGPIOAB();
  if(!ping()) {loseBus();return;}
  for(uint8_t i=0;i<10;i++) {
    const bool sample=!(levels & (uint16_t(1)<<inputs[i]));
    if(sample!=raw[i]) {raw[i]=sample;changed[i]=now;}
    if(now-changed[i]>=30) stable[i]=raw[i];
  }
  Inputs in;
  in.cryoRequest=stable[0];in.ventRequest=stable[1];
  in.cryoClosed=stable[2];in.ventClosed=stable[3];
  in.pressureValid=stable[4];in.pressureBand=stable[5];
  in.cryoReady=stable[6];in.otherPathsClosed=stable[7];
  in.filamentProcessSafe=stable[8];in.reset=stable[9];
  logic.tick(in);
  lamps(logic.out.cryo,logic.out.vent,!logic.out.armed || logic.out.denied);
  if(now-lastReport>=1000) {
    lastReport=now;
    Serial.print(F("inputs A0,A1,A2,A3,A4,A5,A6,B0,B1,B2="));
    for(bool v:stable) Serial.print(v?'1':'0');
    Serial.print(F(" armed="));Serial.print(logic.out.armed);
    Serial.print(F(" cryo="));Serial.print(logic.out.cryo);
    Serial.print(F(" vent="));Serial.println(logic.out.vent);
  }
}
