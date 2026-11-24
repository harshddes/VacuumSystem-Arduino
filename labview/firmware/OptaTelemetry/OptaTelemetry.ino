#if defined(ARDUINO_AVR_UNO)
#include "UnoBench.h"
#else
#include "Installation.h"
#include <OptaBlue.h>
#include <ArduinoRS485.h>
#include <Ethernet.h>
#include <mbed.h>
#include <UDPSocket.h>
#include "Controller.h"
using namespace Opta;
using namespace maize;
constexpr uint16_t port=44820;
const int basePins[]={A0,A1,A2,A3,A4,A5,A6,A7}, relayPins[]={D0,D1,D2,D3};
UDPSocket udp;
bool udpBound;
uint32_t lastBind;
maize::Controller control;
Snapshot field;
uint32_t sequence,sampled,gaugeStarted,gaugeReceived;
uint32_t rawBits,stableBits,validBits;
uint32_t changedAt[24];
uint32_t previousAvailable=0;
uint8_t rx[10],rxLength;
bool waiting,gaugeOK,released;
float gaugeValue;
uint8_t checksum(const uint8_t *p) {
  uint8_t crc = 0xff;
  for (unsigned i = 0; i < 8; ++i) {
    crc ^= p[i];
    for (unsigned bit = 0; bit < 8; ++bit)
      crc = (crc & 0x80) ? (crc << 1) ^ 0x1d : crc << 1;
  }
  return crc;
}

void updateGauge(uint32_t now) {
  if (!cfg::hornetReadEnabled) return;
  // Capture excess bytes so long frames cannot pass a first-nine-bytes check.
  for (unsigned i = 0; i < 24 && RS485.available(); ++i) {
    uint8_t b = RS485.read();
    if (waiting && rxLength < sizeof(rx)) rx[rxLength++] = b;
  }
  if (waiting && now - gaugeStarted >= 180) {
    waiting = false;
    gaugeOK = rxLength == 9 && rx[0] == 0x2a && rx[1] == 1 &&
              rx[2] == 3 && rx[3] == 0 && rx[8] == checksum(rx);
    if (gaugeOK) {
      // Bench capture 2A 01 03 00 7F 2D 48 44 23, little-endian binary32.
      memcpy(&gaugeValue, rx + 4, sizeof(gaugeValue));
      gaugeOK = isfinite(gaugeValue) && gaugeValue > 0 && gaugeValue < 9.0e9f &&
                (!cfg::hornetTorrVerified || fabsf(gaugeValue - 1100.0f) > 1.0f);
      if (gaugeOK) gaugeReceived = now;
    }
  }
  if (!waiting && now - gaugeStarted >= 1000) {
    const uint8_t query[] = {0x21, 1, 3, 0, 0, 0, 0, 0, 0xf1}; // READ CG1 only
    RS485.noReceive();
    RS485.beginTransmission();
    RS485.write(query, sizeof(query));
    RS485.endTransmission();
    RS485.receive();
    rxLength = 0;
    gaugeStarted = now;
    waiting = true;
  }
}


bool assigned(int n) { return n && abs(n)<=24; }
bool known(int n) { return assigned(n) && (validBits & (1UL<<(abs(n)-1))); }
bool active(int n) {
  return known(n) && (bool(stableBits & (1UL<<(abs(n)-1)))==(n>0));
}
// A falling protective contact removes permission immediately; recovery must debounce.
bool healthy(int n) {
  return active(n) && bool(rawBits & (1UL<<(abs(n)-1)))==(n>0);
}
bool qualifiedInstallation() {
  const int pins[]={cfg::selector[0],cfg::selector[1],cfg::selector[2],cfg::selector[3],
    cfg::turboClosed,cfg::turboOpen,cfg::cryoClosed,cfg::cryoOpen,cfg::manual,cfg::automatic,
    cfg::arm,cfg::stopHealthy,cfg::pumpStart,cfg::ventStart,cfg::air,cfg::lab,cfg::inhibitFeedback,
    cfg::roughReady,cfg::cryoReady,cfg::filamentOff,cfg::turboAtSpeed,cfg::backingReady,cfg::ventProcessSafe};
  uint32_t allocated=0;
  for(int n:pins) {
    if(!assigned(n)) return false;
    uint32_t bit=1UL<<(abs(n)-1);
    if(allocated&bit) return false;
    allocated|=bit;
  }
  uint8_t outputs=0;
  for(int n:cfg::openRelay) {
    if(n<1 || n>4 || (outputs&(1u<<(n-1)))) return false;
    outputs|=1u<<(n-1);
  }
  return cfg::cryoInputsVerified && cfg::turboInputsVerified && cfg::selectorsVerified && cfg::panelAndReadinessVerified && cfg::installationReleased && cfg::maintainedEnergizeToOpenVerified &&
    cfg::inputStableMs && cfg::travelOpenMs && cfg::travelCloseMs && cfg::pressureMaxAgeMs &&
    cfg::pressureDwellMs && cfg::cryoEnterTorr>0 && cfg::cryoTripTorr>=cfg::cryoEnterTorr &&
    cfg::turboEnterTorr>0 && cfg::turboTripTorr>=cfg::turboEnterTorr && cfg::allowedPumpMasks &&
    cfg::hornetReadEnabled && cfg::hornetTorrVerified && cfg::chamberGaugeQualified &&
    (!cfg::autoPathQualified || (cfg::roughdownMs && cfg::ventMs && cfg::roughCrossoverTorr>0 && cfg::ventCompleteTorr>cfg::roughCrossoverTorr));
}
void readContacts(uint32_t now) {
  uint32_t bits=0, available=255;
  for(int i=0;i<8;i++) if(digitalRead(basePins[i])) bits|=1UL<<i;
  const auto moduleType=OptaController.getExpansionNum()>=1 ?
      OptaController.getExpansionType(0) : EXPANSION_NOT_VALID;
  if(moduleType==EXPANSION_OPTA_DIGITAL_STS || moduleType==EXPANSION_OPTA_DIGITAL_MEC) {
    DigitalExpansion e(OptaController.getExpansion(0));
    if(e && e.execute(GET_DIGITAL_INPUT)==EXECUTE_OK) {
      available|=0xffff00UL;
      for(int i=0;i<16;i++) if(e.digitalRead(i,false)) bits|=1UL<<(i+8);
    }
  }
  if(!cfg::selectorsVerified) for(int n:cfg::selector) if(assigned(n)) available &= ~(1UL<<(abs(n)-1));
  if(!cfg::cryoInputsVerified) for(int n:{cfg::cryoOpen,cfg::cryoClosed}) if(assigned(n)) available &= ~(1UL<<(abs(n)-1));
  if(!cfg::turboInputsVerified) for(int n:{cfg::turboOpen,cfg::turboClosed}) if(assigned(n)) available &= ~(1UL<<(abs(n)-1));
  if(!cfg::panelAndReadinessVerified) for(int n:{cfg::manual,cfg::automatic,cfg::arm,cfg::stopHealthy,cfg::pumpStart,cfg::ventStart,
      cfg::air,cfg::roughReady,cfg::cryoReady,cfg::filamentOff,cfg::lab,cfg::inhibitFeedback,cfg::turboAtSpeed,cfg::backingReady,cfg::ventProcessSafe})
    if(assigned(n)) available &= ~(1UL<<(abs(n)-1));
  validBits &= available;
  for(unsigned i=0;i<24;i++) {
    uint32_t bit=1UL<<i;
    if(!(available&bit)) continue;
    if(!((previousAvailable)&bit) || ((rawBits^bits)&bit)) {
      changedAt[i]=now;
      // First sample after disconnect must qualify. Existing contacts retain their debounced state.
      if(!(previousAvailable&bit)) validBits &= ~bit;
    }
    if(now-changedAt[i]>=cfg::inputStableMs) {
      stableBits=(stableBits&~bit)|(bits&bit);
      validBits|=bit;
    }
  }
  previousAvailable=available; rawBits=bits;
}
unsigned gate(int closeInput,int openInput) {
  if(!known(closeInput) || !known(openInput)) return 0;
  return (active(closeInput)?1:0)|(active(openInput)?2:0);
}
bool auxiliaryHealthy=true;
bool writeModule(unsigned index,uint8_t type,uint8_t bits,uint8_t assignedOutputs) {
  if(OptaController.getExpansionNum()<=index ||
      OptaController.getExpansionType(index)!=type) return false;
  DigitalExpansion e(OptaController.getExpansion(index));
  if(!e) return false;
  for(unsigned i=0;i<8;i++) if(assignedOutputs&(1u<<i))
    e.digitalWrite(i,(bits&(1u<<i))?HIGH:LOW,false);
  return e.execute(SET_DIGITAL_OUTPUT)==EXECUTE_OK;
}
bool writeAuxiliary() {
  if(cfg::faultLampWiringVerified)
    writeModule(0,EXPANSION_OPTA_DIGITAL_STS,control.latch?1:0,1);
  uint8_t installed=(cfg::buzzerWiringVerified?1:0)|(cfg::filamentOffInterfaceQualified?2:0);
  if(!released || !installed) return true;
  bool requestOff=control.stage==VentPreparation || control.stage==Venting ||
      (field.mode==Manual && (field.selectors&Vent));
  uint8_t bits=(control.latch && !control.silenced?1:0)|(requestOff?2:0);
  return writeModule(1,EXPANSION_OPTA_DIGITAL_MEC,bits,installed);
}
void scan(uint32_t now) {
  readContacts(now);
  Snapshot s;
  s.time=now;
  s.validPanel=known(cfg::manual)&&known(cfg::automatic)&&known(cfg::arm)&&known(cfg::stopHealthy)&&known(cfg::pumpStart)&&known(cfg::ventStart);
  for(unsigned i=0;i<4;i++) {
    if(!known(cfg::selector[i])) s.validPanel=false;
    if(active(cfg::selector[i])) s.selectors|=1u<<i;
    if(i<2 && known(cfg::selector[i])) s.positions|=(active(cfg::selector[i])?2u:1u)<<(2*i);
  }
  s.positions|=gate(cfg::turboClosed,cfg::turboOpen)<<4;
  s.positions|=gate(cfg::cryoClosed,cfg::cryoOpen)<<6;
  s.mode=known(cfg::manual)&&known(cfg::automatic)?Mode(active(cfg::manual)+2*active(cfg::automatic)):Invalid;
  s.arm=active(cfg::arm); s.pump=active(cfg::pumpStart); s.vent=active(cfg::ventStart);
  s.basic=(healthy(cfg::stopHealthy)?1:0)|(healthy(cfg::air)?2:0)|(healthy(cfg::lab)?4:0)|
    (healthy(cfg::inhibitFeedback)?8:0)|(s.validPanel?16:0)|(healthy(cfg::filamentOff)?64:0)|
    (healthy(cfg::roughReady)?128:0)|(healthy(cfg::cryoReady)?256:0)|(healthy(cfg::turboAtSpeed)?512:0)|
    (healthy(cfg::backingReady)?1024:0);
  s.roughClosure=(s.positions&3)==1 && control.closedOutput(0,now);
  s.ventClosure=(s.positions&12)==4 && control.closedOutput(1,now);
  s.processSafe=healthy(cfg::ventProcessSafe);
  s.torr=gaugeValue;
  s.pressureValid=gaugeOK && cfg::chamberGaugeQualified && cfg::hornetTorrVerified &&
    now-gaugeReceived<=cfg::pressureMaxAgeMs && cfg::pressureMaxAgeMs;
  if(!auxiliaryHealthy) s.basic &= ~16u;
  control.tick(s,released);
  if(released) for(int i=0;i<4;i++) digitalWrite(relayPins[cfg::openRelay[i]-1],(control.command&(1u<<i))?HIGH:LOW);
  field=s;
  auxiliaryHealthy=writeAuxiliary();
  if(!auxiliaryHealthy && released) {
    control.d.status&=~16u;
    control.d.alarms|=16;
    control.latch|=16; control.enter(Fault,now); control.setCommand(0,now);
    for(int p:relayPins) digitalWrite(p,LOW);
  }
  sampled=now; ++sequence;
}
void reply() {
  // Neither cable loss nor a blocked display client can delay the local control scan.
  if(Ethernet.linkStatus()!=LinkON) {
    if(udpBound) { udp.close(); udpBound=false; }
    return;
  }
  if(!udpBound) {
    if(millis()-lastBind<1000) return;
    lastBind=millis();
    if(udp.open(Ethernet.getNetwork())!=NSAPI_ERROR_OK) return;
    udp.set_blocking(false);
    if(udp.bind(port)!=NSAPI_ERROR_OK) { udp.close(); return; }
    udpBound=true;
  }
  SocketAddress peer;
  char req[20];
  int size=udp.recvfrom(&peer,req,sizeof(req));
  if(size!=18 || memcmp(req,"MAIZE3 R ",9) || req[17]!='\n') return;
  for(int i=9;i<17;i++) if(!isxdigit((unsigned char)req[i])) return;
  req[17]=0;
  char pressure[32]="-";
  // Pressure shown only while this physical source is current.
  if(gaugeOK && cfg::hornetTorrVerified && cfg::pressureMaxAgeMs &&
     millis()-gaugeReceived<=cfg::pressureMaxAgeMs) snprintf(pressure,sizeof pressure,"%.8g",(double)gaugeValue);
  unsigned selKnown=0; for(int i=0;i<4;i++) if(known(cfg::selector[i])) selKnown|=1u<<i;
  char packet[256];
  const Decision &d=control.d;
  snprintf(packet,sizeof packet,"MAIZE3,%s,%lu,%lu,%u,%u,%u,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%u,%s,%lu,%u",
    req,(unsigned long)sequence,(unsigned long)sampled,(unsigned)field.mode,(unsigned)control.stage,
    field.selectors,(unsigned long)field.positions,(unsigned long)d.attempt,(unsigned long)d.status,
    (unsigned long)d.site,(unsigned long)d.events,(unsigned long)d.alarms,(unsigned long)control.latch,control.command,pressure,(unsigned long)(gaugeOK?millis()-gaugeReceived:0),selKnown);
  udp.sendto(peer,packet,strlen(packet));
}
void setup() {
  released=qualifiedInstallation();
  for(int p:basePins) pinMode(p,INPUT);
  for(int p:relayPins) { digitalWrite(p,LOW); pinMode(p,OUTPUT); }
  OptaController.begin();
  if(cfg::hornetReadEnabled) { RS485.begin(19200,SERIAL_8N1); RS485.receive(); }
  IPAddress ip(cfg::address[0],cfg::address[1],cfg::address[2],cfg::address[3]);
  IPAddress gateway(cfg::address[0],cfg::address[1],cfg::address[2],1);
  Ethernet.begin(nullptr,ip,gateway,gateway,IPAddress(255,255,255,0),0,0);
  mbed::Watchdog::get_instance().start(4000);
  scan(millis());
}
void loop() {
  OptaController.update();
  uint32_t now=millis();
  updateGauge(now);
  if(now-sampled>=20) scan(now);
  reply();
  mbed::Watchdog::get_instance().kick();
}
#endif
