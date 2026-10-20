// BENCH ONLY. Day 1 loopback drawing. No RS485, Hornet, coils or valves.
// DFR0627 DIP A1=A0=1. UART1 T->R and UART2 T->R. USB Serial 115200.
#include <Wire.h>
#include <DFRobot_IICSerial.h>

DFRobot_IICSerial uart1(Wire, SUBUART_CHANNEL_1, 1, 1);
DFRobot_IICSerial uart2(Wire, SUBUART_CHANNEL_2, 1, 1);
const uint8_t frame[] = {'P','P','M','L','_',0x00,0x55,0xAA,0xFF};
uint16_t passed=0, failed=0;
bool ready=false;

bool roundTrip(DFRobot_IICSerial &port, const __FlashStringHelper *name) {
  // A missing bus must not silently count as a successful echo.
  const unsigned long drainStart=millis();
  while(port.available() && millis()-drainStart<30) port.read();
  const size_t sent=port.write(frame,sizeof(frame));
  uint8_t received[sizeof(frame)];
  size_t count=0;
  const unsigned long start=millis();
  while(count<sizeof(frame) && millis()-start<300) {
    if(port.available()) received[count++]=static_cast<uint8_t>(port.read());
    if(Wire.getWireTimeoutFlag()) break;
  }
  bool ok=sent==sizeof(frame) && count==sizeof(frame) && !Wire.getWireTimeoutFlag();
  for(size_t i=0;i<count;i++) if(received[i]!=frame[i]) ok=false;
  Serial.print(name);Serial.println(ok?F(" PASS"):F(" FAIL - inspect power, DIP and same-port T/R loop"));
  Wire.clearWireTimeoutFlag();
  return ok;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(25000,true);
  Wire.clearWireTimeoutFlag();
  Serial.println(F("BENCH ONLY: both UART T/R loops fitted, no RS485 adapter"));
  const int first=uart1.begin(9600);
  const int second=uart2.begin(9600);
  ready=first==DFROBOT_IICSERIAL_ERR_OK && second==DFROBOT_IICSERIAL_ERR_OK;
  Wire.setWireTimeout(25000,true);
  if(!ready) Serial.println(F("INIT FAIL: power down and inspect supply, A4/A5 and DIP A1=A0=1"));
  Serial.println(F("USB 115200; module UARTs 9600. Testing every 2 seconds."));
}

void loop() {
  if(!ready) {delay(1000);return;}
  if(roundTrip(uart1,F("UART1"))) passed++; else failed++;
  if(roundTrip(uart2,F("UART2"))) passed++; else failed++;
  Serial.print(F("cumulative pass="));Serial.print(passed);
  Serial.print(F(" fail="));Serial.println(failed);
  delay(2000); // Diagnostic only. Never reuse this timing structure for valve control.
}
