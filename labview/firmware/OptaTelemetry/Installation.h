#pragma once
#include <stdint.h>
// Replacement cabinet wiring schedule, not a survey of the old rack.
// Base I1..I8 = 1..8. D1608E I1..I16 = 9..24. Negative reverses polarity.
// Authorize a group only after checking the terminals and both physical states.
namespace installation {
constexpr bool cryoInputsVerified=false, turboInputsVerified=false;
constexpr bool selectorsVerified=false, panelAndReadinessVerified=false;
constexpr int cryoClosed=1, cryoOpen=2, turboClosed=3, turboOpen=4;
constexpr int turboAtSpeed=5, backingReady=6, ventProcessSafe=7;
constexpr int selector[4]={9,10,11,12}; // Roughing, Let-up, Turbo, Cryo
constexpr int manual=13, automatic=14, arm=15, stopHealthy=16, pumpStart=17, ventStart=18;
constexpr int air=19, roughReady=20, cryoReady=21, filamentOff=22, lab=23, inhibitFeedback=24;
constexpr int openRelay[4]={1,2,3,4}; // Proposed new wiring in the same faceplate order
constexpr bool maintainedEnergizeToOpenVerified=false, installationReleased=false;
// E1 relays are four GREEN/RED pairs in faceplate order.
constexpr bool valveLampWiringVerified=false;
// Optional E2 relays 1 and 2 serve a buzzer and a qualified filament-OFF interface.
constexpr bool autoPathQualified=false, buzzerWiringVerified=false, filamentOffInterfaceQualified=false;
constexpr uint32_t inputStableMs=0, travelOpenMs=0, travelCloseMs=0;
constexpr uint32_t pressureMaxAgeMs=0, pressureDwellMs=0, roughdownMs=0, ventMs=0;
constexpr float cryoEnterTorr=0, cryoTripTorr=0, turboEnterTorr=0, turboTripTorr=0;
constexpr float roughCrossoverTorr=0, ventCompleteTorr=0;
// Bit n permits the complete simultaneous pump-path mask n (Rough=1, Turbo=4, Cryo=8).
constexpr uint16_t allowedPumpMasks=0;
constexpr bool hornetReadEnabled=false, hornetTorrVerified=false, chamberGaugeQualified=false;
constexpr uint8_t address[4]={192,168,10,42}; // Address of this sketch on the new local Ethernet segment
}
