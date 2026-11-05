// Day 2 lamps plus Phase 3 gate. USB Serial 115200.
// Ten simulated desk inputs stay on A0,A1,A2,A3,B5,A5,A6,B0,B1,B2.
// Expander A4 = GATE_CLOSED. B4 open reed is stuck reading closed and is ignored.
// A2 stays the simulated cryo-closed jumper.
// Position comes only from the closed reed. CLOSED=0 is not an open proof.
// D8 starts LOW. Humphrey 062-4E1 spring, air on, D8 low sits on the closed reed.
// USB o holds D8 high (open direction). USB c or x releases the coil.
// UART1 polls Hornet CG1 (cmd 0x03) then CG2 (cmd 0x04). No filament, no degas.
// 6318 load terminals stay disconnected. Leave D5, D6, D7 empty.
#include <Wire.h>
#include <Adafruit_MCP23X17.h>
#include <DFRobot_IICSerial.h>
#include <math.h>
#include <string.h>
#include "bench_logic.h"

DFRobot_IICSerial uart1(Wire, SUBUART_CHANNEL_1, 1, 1);
// Proven READ CG1. READ CG2 is the next row in the same binary table: !<01><04>.
// CRC-8 poly 0x1D, init 0xFF, no final XOR. CG2 checksum is 0x3E.
const uint8_t kCg1Tx[9] = {0x21, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF1};
const uint8_t kCg2Tx[9] = {0x21, 0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3E};
const float kNoGaugeTorr = 1.01e3f;

Adafruit_MCP23X17 mcp;
BenchLogic logic;
const uint8_t address=0x21;
// Expander pins. Pressure is B5. Re-arm is B2, where the Schneider switch is wired.
// A7 and B7 stay unused as inputs.
const uint8_t inputs[10]={0,1,2,3,13,5,6,8,9,10};
const uint8_t kClosedPin=4;  // 5346 A4, wired closed reed
const uint8_t kOpenPin=12;   // 5346 B4, stuck closed, printed but ignored
const uint8_t kRelayPin=8;   // Uno D8 to relay-module IN. Jumper on H.
const uint8_t leds[3]={A0,A1,A2}; // These three are UNO pins, not expander pins.
bool raw[10]={false},stable[10]={false};
unsigned long changed[10]={0};
bool reedRaw[2]={false,false},reedStable[2]={false,false};
unsigned long reedChanged[2]={0};
unsigned long lastReport=0,lastRetry=0;
bool configured=false,relayOn=false;
enum HornetPhase : uint8_t { kHornetIdle, kHornetCollect, kHornetGap };
HornetPhase hornetPhase=kHornetIdle;
uint8_t hornetChan=0,hornetN=0,hornetRx[9];
unsigned long hornetMark=0,hornetPairAt=0;
bool hornetReady=false,cgOk[2]={false,false};
float cgVal[2]={0,0};

uint8_t crc8(const uint8_t *d,uint8_t n) {
  uint8_t crc=0xFF;
  for(uint8_t i=0;i<n;i++) {
    crc^=d[i];
    for(uint8_t b=0;b<8;b++) crc=(crc & 0x80) ? (uint8_t)((crc<<1)^0x1D) : (uint8_t)(crc<<1);
  }
  return crc;
}

bool pressureOk(float v) {
  if(!isfinite(v) || v<=0) return false;
  return fabsf(v-kNoGaugeTorr)/kNoGaugeTorr>0.02f;
}

void decodeChan(uint8_t chan) {
  cgOk[chan]=false;
  if(hornetN!=9 || crc8(hornetRx,8)!=hornetRx[8]) return;
  const uint8_t expect=chan==0 ? 0x03 : 0x04;
  if(hornetRx[0]!=0x2A || hornetRx[1]!=0x01 || hornetRx[2]!=expect || hornetRx[3]!=0x00) return;
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
  Serial.println();
}

void startChan(uint8_t chan) {
  while(uart1.available()) uart1.read();
  uart1.write(chan==0?kCg1Tx:kCg2Tx,9);
  hornetChan=chan;
  hornetN=0;
  hornetMark=millis();
  hornetPhase=kHornetCollect;
}

void hornetTick(unsigned long now) {
  if(!hornetReady) return;
  if(hornetPhase==kHornetIdle) {
    if(now-hornetPairAt<1000) return;
    cgOk[0]=cgOk[1]=false;
    startChan(0);
    return;
  }
  if(hornetPhase==kHornetGap) {
    if(now-hornetMark<50) return;
    startChan(1);
    return;
  }
  while(uart1.available() && hornetN<9) hornetRx[hornetN++]=(uint8_t)uart1.read();
  if(hornetN<9 && now-hornetMark<300) return;
  decodeChan(hornetChan);
  if(hornetChan==0) {hornetPhase=kHornetGap;hornetMark=now;return;}
  printHornet();
  hornetPairAt=now;
  hornetPhase=kHornetIdle;
}

void lamps(bool cryo,bool vent,bool fault) {
  digitalWrite(leds[0],cryo?HIGH:LOW);
  digitalWrite(leds[1],vent?HIGH:LOW);
  digitalWrite(leds[2],fault?HIGH:LOW);
}

void coilOff() {
  digitalWrite(kRelayPin,LOW);
  relayOn=false;
}

void coilOn() {
  digitalWrite(kRelayPin,HIGH);
  relayOn=true;
}

bool ping() {
  Wire.beginTransmission(address);
  const uint8_t result=Wire.endTransmission();
  return result==0 && !Wire.getWireTimeoutFlag();
}

void loseBus() {
  coilOff();
  lamps(false,false,true);
  logic=BenchLogic(); // Reconnect never substitutes for a deliberate re-arm.
  configured=false;
  Wire.clearWireTimeoutFlag();
}

const char *gatePos(bool,bool gateClosed) {
  if(gateClosed) return "CLOSED";
  return "NOT_CLOSED";
}

void setup() {
  digitalWrite(kRelayPin,LOW);
  pinMode(kRelayPin,OUTPUT);
  coilOff();
  for(uint8_t p:leds) {digitalWrite(p,LOW);pinMode(p,OUTPUT);}
  lamps(false,false,true);
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000,true);
  Serial.println(F("GATE BENCH - MCP 0x21; A4 closed reed; B4 ignored; D8 LOW"));
  Serial.println(F("USB o = hold open. USB c or x = release, spring returns closed."));
  hornetReady=uart1.begin(19200,IICSerial_8N1)==DFROBOT_IICSERIAL_ERR_OK;
  Wire.setWireTimeout(25000,true);
  if(!hornetReady) Serial.println(F("HORNET UART OFFLINE"));
}

void loop() {
  const unsigned long now=millis();
  while(Serial.available()) {
    const char c=Serial.read();
    if(c=='o' || c=='O') {
      if(!configured) Serial.println(F("OPEN REFUSED: expander offline"));
      else {coilOn();Serial.println(F("OPEN HOLD"));}
    } else if(c=='c' || c=='C' || c=='x' || c=='X') {
      coilOff();
      Serial.println(F("RELEASED CLOSED"));
    }
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
    mcp.pinMode(kOpenPin,INPUT_PULLUP);
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
    reedRaw[0]=reedStable[0]=!(levels & (uint16_t(1)<<kOpenPin));
    reedRaw[1]=reedStable[1]=!(levels & (uint16_t(1)<<kClosedPin));
    reedChanged[0]=reedChanged[1]=now;
    configured=true;
    logic=BenchLogic();
    Serial.println(F("MCP ONLINE. D8 still LOW until USB o."));
  }
  if(!ping()) {loseBus();return;}
  const uint16_t levels=mcp.readGPIOAB();
  if(!ping()) {loseBus();return;}
  for(uint8_t i=0;i<10;i++) {
    const bool sample=!(levels & (uint16_t(1)<<inputs[i]));
    if(sample!=raw[i]) {raw[i]=sample;changed[i]=now;}
    if(now-changed[i]>=30) stable[i]=raw[i];
  }
  const bool openSample=!(levels & (uint16_t(1)<<kOpenPin));
  const bool closedSample=!(levels & (uint16_t(1)<<kClosedPin));
  if(openSample!=reedRaw[0]) {reedRaw[0]=openSample;reedChanged[0]=now;}
  if(closedSample!=reedRaw[1]) {reedRaw[1]=closedSample;reedChanged[1]=now;}
  if(now-reedChanged[0]>=30) reedStable[0]=reedRaw[0];
  if(now-reedChanged[1]>=30) reedStable[1]=reedRaw[1];
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
    Serial.print(F("OPEN="));Serial.print(reedStable[0]?'1':'0');
    Serial.print(F(" CLOSED="));Serial.print(reedStable[1]?'1':'0');
    Serial.print(F(" POS="));Serial.print(gatePos(reedStable[0],reedStable[1]));
    Serial.print(F(" D8="));Serial.print(relayOn?'1':'0');
    Serial.print(F(" all A0-A7,B0-B7="));
    for(uint8_t b=0;b<16;b++) Serial.print((levels & (uint16_t(1)<<b)) ? '0' : '1');
    Serial.print(F(" inputs A0,A1,A2,A3,B5,A5,A6,B0,B1,B2="));
    for(bool v:stable) Serial.print(v?'1':'0');
    Serial.print(F(" armed="));Serial.print(logic.out.armed);
    Serial.print(F(" cryo="));Serial.print(logic.out.cryo);
    Serial.print(F(" vent="));Serial.println(logic.out.vent);
  }
  hornetTick(now);
}
