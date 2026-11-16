// Day 2 lamps plus Phase 3 gate. USB Serial 115200.
// Ten simulated desk inputs stay on A0,A1,A2,A3,B5,A5,A6,B0,B1,B2.
// Expander B3 is the only gate switch. A4 stayed NOT_CLOSED on 2026-11-16
// and is left empty. The open switch is a melted short.
// It is not wired, not configured, and not read.
// A2 stays the simulated cryo-closed jumper.
// D8 starts LOW. Humphrey 062-4E1 spring, air on, D8 low sits on the closed reed.
// A0 is a press that pops back. One rising edge flips the coil memory.
// USB o forces that memory open. USB c or x clears it.
// Uno L on D13 stays lit while the closed reed is made.
// UART1 polls address 1 then address 2. Each box: CG1 (0x03) then CG2 (0x04).
// No filament, no degas. Address 2 CG2 checksum is 0xD9.
// 6318 load terminals stay disconnected. Leave D5, D6, D7 empty.
#include <Wire.h>
#include <Adafruit_MCP23X17.h>
#include <DFRobot_IICSerial.h>
#include <math.h>
#include <string.h>
#include "bench_logic.h"

DFRobot_IICSerial uart1(Wire, SUBUART_CHANNEL_1, 1, 1);
// Order: addr1 CG1, addr1 CG2, addr2 CG1, addr2 CG2.
// CRC-8 poly 0x1D, init 0xFF, no final XOR.
const uint8_t kHornetTx[4][9] = {
  {0x21, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF1},
  {0x21, 0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3E},
  {0x21, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x16},
  {0x21, 0x02, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD9},
};

Adafruit_MCP23X17 mcp;
BenchLogic logic;
const uint8_t address=0x21;
// Expander pins. Pressure is B5. Re-arm is B2, where the Schneider switch is wired.
// A7 and B7 stay unused as inputs.
const uint8_t inputs[10]={0,1,2,3,13,5,6,8,9,10};
const uint8_t kClosedPin=11;  // 5346 B3. A4 is empty and not read.
const uint8_t kRelayPin=8;   // Uno D8 to relay-module IN. Jumper on H.
const uint8_t kLampPin=13;   // Uno L. Lit means the closed reed is made.
const uint8_t leds[3]={A0,A1,A2}; // These three are UNO pins, not expander pins.
bool raw[10]={false},stable[10]={false};
unsigned long changed[10]={0};
bool closedRaw=false,closedStable=false;
unsigned long closedChanged=0;
unsigned long lastReport=0,lastRetry=0;
bool configured=false,relayOn=false,coilWanted=false,prevA0=false;
bool busBad=false;
unsigned long busBadSince=0;
const char *gateSrc="BOOT";
enum HornetPhase : uint8_t { kHornetIdle, kHornetCollect, kHornetGap };
HornetPhase hornetPhase=kHornetIdle;
uint8_t hornetChan=0,hornetN=0,hornetRx[9];
unsigned long hornetMark=0,hornetPairAt=0;
bool hornetReady=false,cgOk[4]={false,false,false,false};
float cgVal[4]={0,0,0,0};

uint8_t crc8(const uint8_t *d,uint8_t n) {
  uint8_t crc=0xFF;
  for(uint8_t i=0;i<n;i++) {
    crc^=d[i];
    for(uint8_t b=0;b<8;b++) crc=(crc & 0x80) ? (uint8_t)((crc<<1)^0x1D) : (uint8_t)(crc<<1);
  }
  return crc;
}

bool pressureOk(float v) {
  // A high convection number can be atmosphere. Keep it.
  return isfinite(v) && v>0;
}

bool igPermit() {
  // Every live convection reading must be at or below 1.1e-3 Torr.
  // 1100 Torr is the open jack. 9.9e9 is the ion-gauge off flag.
  bool saw=false;
  for(uint8_t i=0;i<4;i++) {
    if(!cgOk[i]) continue;
    if(fabsf(cgVal[i]-1100.f)<=1.f) continue;
    if(cgVal[i]>=9.0e9f) continue;
    saw=true;
    if(cgVal[i]>1.1e-3f) return false;
  }
  return saw;
}

void sendIg(bool on) {
  // Manual 000861-116: 5-byte !<01><05> turns the filament on, !<01><06> turns it off.
  // Data byte is the placeholder. Checksum matches the CG reads: poly 0x1D, init 0xFF.
  const uint8_t frameOn[5]={0x21,0x01,0x05,0x00,0x9F};
  const uint8_t frameOff[5]={0x21,0x01,0x06,0x00,0x4B};
  if(on && !igPermit()) {
    Serial.println(F("IG REFUSED: pressure still too high"));
    return;
  }
  uart1.write(on?frameOn:frameOff,5);
  Serial.println(on?F("IG ON SENT"):F("IG OFF SENT"));
}

void decodeChan(uint8_t chan) {
  cgOk[chan]=false;
  if(hornetN!=9 || crc8(hornetRx,8)!=hornetRx[8]) return;
  const uint8_t expectCmd=(chan & 1) ? 0x04 : 0x03;
  const uint8_t expectAddr=chan<2 ? 0x01 : 0x02;
  if(hornetRx[0]!=0x2A || hornetRx[1]!=expectAddr || hornetRx[2]!=expectCmd || hornetRx[3]!=0x00) return;
  uint32_t bits=(uint32_t)hornetRx[4] | ((uint32_t)hornetRx[5]<<8)
    | ((uint32_t)hornetRx[6]<<16) | ((uint32_t)hornetRx[7]<<24);
  float v;
  memcpy(&v,&bits,sizeof v);
  if(!pressureOk(v)) return;
  cgVal[chan]=v;
  cgOk[chan]=true;
}

void printSci(bool ok,float v) {
  if(!ok) return;
  int exp=0;
  if(v<0) {Serial.write('-');v=-v;}
  while(v>=10.0f && exp<30) {v/=10.0f;exp++;}
  while(v<1.0f && exp>-30) {v*=10.0f;exp--;}
  Serial.print(v,3);
  Serial.write('E');
  Serial.write(exp>=0?'+':'-');
  const int ae=exp>=0?exp:-exp;
  if(ae<10) Serial.write('0');
  Serial.print(ae);
}

void printHornet() {
  Serial.print(F("HORNET CG1="));
  printSci(cgOk[0],cgVal[0]);
  Serial.print(F(" CG2="));
  printSci(cgOk[1],cgVal[1]);
  Serial.print(F(" A2CG1="));
  printSci(cgOk[2],cgVal[2]);
  Serial.print(F(" A2CG2="));
  printSci(cgOk[3],cgVal[3]);
  Serial.println();
}

void startChan(uint8_t chan) {
  while(uart1.available()) uart1.read();
  uart1.write(kHornetTx[chan],9);
  hornetChan=chan;
  hornetN=0;
  hornetMark=millis();
  hornetPhase=kHornetCollect;
}

void hornetTick(unsigned long now) {
  if(!hornetReady) return;
  if(hornetPhase==kHornetIdle) {
    if(now-hornetPairAt<1000) return;
    cgOk[0]=cgOk[1]=cgOk[2]=cgOk[3]=false;
    startChan(0);
    return;
  }
  if(hornetPhase==kHornetGap) {
    if(now-hornetMark<50) return;
    startChan(hornetChan+1);
    return;
  }
  while(uart1.available() && hornetN<9) hornetRx[hornetN++]=(uint8_t)uart1.read();
  if(hornetN<9 && now-hornetMark<300) return;
  decodeChan(hornetChan);
  // 50 ms between questions. Print only after both boxes have been asked.
  if(hornetChan<3) {hornetPhase=kHornetGap;hornetMark=now;return;}
  printHornet();
  hornetPairAt=now;
  hornetPhase=kHornetIdle;
}

void lamps(bool cryo,bool vent,bool fault) {
  digitalWrite(leds[0],cryo?HIGH:LOW);
  digitalWrite(leds[1],vent?HIGH:LOW);
  digitalWrite(leds[2],fault?HIGH:LOW);
}

void applyCoil() {
  // Expander loss must drop the coil even if the memory was still open.
  const bool on=coilWanted && configured;
  digitalWrite(kRelayPin,on?HIGH:LOW);
  relayOn=on;
}

void applyLamp() {
  // L follows the closed reed. A coil command is not a position.
  digitalWrite(kLampPin,(configured && closedStable)?HIGH:LOW);
}

void printGate() {
  Serial.print(F("GATE ASK="));
  Serial.print(coilWanted?F("OPEN"):F("RELEASED"));
  Serial.print(F(" D8="));
  Serial.print(relayOn?'1':'0');
  Serial.print(F(" REED="));
  Serial.print(closedStable?F("CLOSED"):F("NOT_CLOSED"));
  Serial.print(F(" SRC="));
  Serial.println(gateSrc);
}

void setCoil(bool want,const char *src) {
  if(want && !configured) {
    Serial.println(F("OPEN REFUSED: expander offline"));
    return;
  }
  coilWanted=want;
  gateSrc=src;
  applyCoil();
  printGate();
}

bool ping() {
  // A Hornet read on this same bus can leave the timeout flag set.
  // That flag is not proof the expander died.
  Wire.clearWireTimeoutFlag();
  Wire.beginTransmission(address);
  const uint8_t result=Wire.endTransmission();
  const bool ok=result==0 && !Wire.getWireTimeoutFlag();
  Wire.clearWireTimeoutFlag();
  return ok;
}

void loseBus() {
  // A dead expander must not leave the last open request sitting there.
  busBad=false;
  coilWanted=false;
  gateSrc="BUS";
  configured=false;
  applyCoil();
  applyLamp();
  lamps(false,false,true);
  logic=BenchLogic(); // Reconnect never substitutes for a deliberate re-arm.
  Wire.clearWireTimeoutFlag();
  printGate();
}

void noteBus(bool ok, unsigned long now) {
  if(ok) { busBad=false; return; }
  if(!busBad) { busBad=true; busBadSince=now; return; }
  // One missed answer must not spring the gate shut. 300 ms of real silence does.
  if(now-busBadSince>=300) loseBus();
}

const char *gatePos(bool gateClosed) {
  if(gateClosed) return "CLOSED";
  return "NOT_CLOSED";
}

void setup() {
  digitalWrite(kRelayPin,LOW);
  digitalWrite(kLampPin,LOW);
  pinMode(kRelayPin,OUTPUT);
  pinMode(kLampPin,OUTPUT);
  applyCoil();
  for(uint8_t p:leds) {digitalWrite(p,LOW);pinMode(p,OUTPUT);}
  lamps(false,false,true);
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000,true);
  Serial.println(F("GATE BENCH - MCP 0x21; B3 closed reed only; A4 empty; D8 LOW; L follows closed"));
  Serial.println(F("A0 press toggles. USB o forces open. USB c or x releases."));
  hornetReady=uart1.begin(19200,IICSerial_8N1)==DFROBOT_IICSERIAL_ERR_OK;
  Wire.setWireTimeout(25000,true);
  if(!hornetReady) Serial.println(F("HORNET UART OFFLINE"));
}

void loop() {
  const unsigned long now=millis();
  while(Serial.available()) {
    const char c=Serial.read();
    if(c=='o' || c=='O') setCoil(true,"USB");
    else if(c=='c' || c=='C' || c=='x' || c=='X') setCoil(false,"USB");
    else if(c=='i' || c=='I') sendIg(true);
    else if(c=='k' || c=='K') sendIg(false);
  }
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
    mcp.pinMode(kClosedPin,INPUT_PULLUP);
    // Output-only unused A7/B7 avoid changing-input erratum.
    mcp.digitalWrite(7,LOW);mcp.pinMode(7,OUTPUT);
    mcp.digitalWrite(15,LOW);mcp.pinMode(15,OUTPUT);
    const uint16_t levels=mcp.readGPIOAB();
    if(!ping()) {loseBus();return;}
    for(uint8_t i=0;i<10;i++) {
      raw[i]=stable[i]=!(levels & (uint16_t(1)<<inputs[i]));
      changed[i]=now;
    }
    closedRaw=closedStable=!(levels & (uint16_t(1)<<kClosedPin));
    closedChanged=now;
    configured=true;
    logic=BenchLogic();
    // A finger already down at reconnect is not a new press.
    prevA0=stable[0];
    coilWanted=false;
    gateSrc="BOOT";
    applyCoil();
    applyLamp();
    Serial.println(F("MCP ONLINE. D8 LOW until a press or USB o."));
    printGate();
  }
  if(!ping()) { noteBus(false, now); return; }
  noteBus(true, now);
  const uint16_t levels=mcp.readGPIOAB();
  if(!ping()) { noteBus(false, now); return; }
  noteBus(true, now);
  for(uint8_t i=0;i<10;i++) {
    const bool sample=!(levels & (uint16_t(1)<<inputs[i]));
    if(sample!=raw[i]) {raw[i]=sample;changed[i]=now;}
    if(now-changed[i]>=30) stable[i]=raw[i];
  }
  const bool closedSample=!(levels & (uint16_t(1)<<kClosedPin));
  if(closedSample!=closedRaw) {closedRaw=closedSample;closedChanged=now;}
  if(now-closedChanged>=30) closedStable=closedRaw;
  applyLamp();
  Inputs in;
  in.cryoRequest=stable[0];in.ventRequest=stable[1];
  in.cryoClosed=stable[2];in.ventClosed=stable[3];
  in.pressureValid=stable[4];in.pressureBand=stable[5];
  in.cryoReady=stable[6];in.otherPathsClosed=stable[7];
  in.filamentProcessSafe=stable[8];in.reset=stable[9];
  logic.tick(in);
  lamps(logic.out.cryo,logic.out.vent,!logic.out.armed || logic.out.denied);
  // Level would close the gate the instant the finger lifts. The edge remembers.
  if(stable[0] && !prevA0) setCoil(!coilWanted,"BUTTON");
  prevA0=stable[0];
  if(now-lastReport>=1000) {
    lastReport=now;
    Serial.print(F("CLOSED="));Serial.print(closedStable?'1':'0');
    Serial.print(F(" POS="));Serial.print(gatePos(closedStable));
    Serial.print(F(" D8="));Serial.print(relayOn?'1':'0');
    Serial.print(F(" L="));Serial.print(closedStable?'1':'0');
    Serial.print(F(" inputs A0,A1,A2,A3,B5,A5,A6,B0,B1,B2="));
    for(bool v:stable) Serial.print(v?'1':'0');
    Serial.print(F(" armed="));Serial.print(logic.out.armed);
    Serial.print(F(" cryo="));Serial.print(logic.out.cryo);
    Serial.print(F(" vent="));Serial.println(logic.out.vent);
    printGate();
  }
  hornetTick(now);
}
