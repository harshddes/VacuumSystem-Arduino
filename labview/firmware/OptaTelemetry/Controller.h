#pragma once
#include <stdint.h>

namespace maize {
namespace cfg = installation;
enum Valve { Rough=1, Vent=2, Turbo=4, Cryo=8 };
enum Mode { Off, Manual, Auto, Invalid };
enum Stage { Disarmed, Armed, Roughing, Isolating, HighVacuum, VentPreparation, Venting, VentClosing, Fault };
struct Snapshot {
  uint32_t time=0, positions=0, basic=0;
  uint8_t selectors=0;
  Mode mode=Invalid;
  bool arm=false, pump=false, vent=false, validPanel=false;
  bool roughClosure=false, ventClosure=false, processSafe=false;
  bool pressureValid=false;
  float torr=0;
};
struct Decision {
  uint32_t attempt=0, status=0, site=0, events=0, alarms=0;
};
inline uint32_t evaluate(uint32_t attempt,uint32_t pos,uint32_t status,uint32_t site,uint32_t events) {
  uint32_t alarms;
  #include "PermissionRules.h"
  return alarms;
}
struct Controller {
  Stage stage=Disarmed;
  Mode previousMode=Invalid;
  bool silenced=false, primed=false, oldArm=false, oldPump=false, oldVent=false, motion[2]={};
  uint8_t command=0;
  uint32_t latch=0, stageSince=0, motionSince[2]={}, belowSince[2]={};
  bool below[2]={}, qualifiedBelow[2]={};
  Decision d;
  bool armed() const { return stage!=Disarmed && stage!=Fault; }
  void enter(Stage next,uint32_t now) { if(stage!=next) {stage=next; stageSince=now;} }
  void updatePressure(const Snapshot& s,unsigned index,float enter,float trip,uint32_t permission,uint8_t valve) {
    bool low=s.pressureValid && enter>0 && s.torr<enter;
    if(low && !below[index]) belowSince[index]=s.time;
    if(!low) qualifiedBelow[index]=false;
    else if(uint32_t(s.time-belowSince[index])>=cfg::pressureDwellMs) qualifiedBelow[index]=true;
    below[index]=low;
    // An authorized opening uses entry dwell; a continuing opening uses trip hysteresis.
    if ((command & valve) ? s.pressureValid && s.torr<trip :
        qualifiedBelow[index]) d.status |= permission;
  }
  void supervise(const Snapshot& s,unsigned i,uint8_t valve,unsigned shift) {
    unsigned p=(s.positions>>shift)&3;
    unsigned expected=(command & valve)?2:1;
    uint32_t limit=(command & valve)?cfg::travelOpenMs:cfg::travelCloseMs;
    if(p==expected) motion[i]=false;
    if(motion[i]) {
      if(limit && uint32_t(s.time-motionSince[i])<limit) d.events |= i==0?1:2;
      else { d.events |= 16; motion[i]=false; }
    } else if(p!=expected && p!=3) d.events |= 64;
  }
  uint32_t unsensedCloseSince[2]={};
  bool settling[2]={};
  bool closedOutput(unsigned index,uint32_t now) {
    if(settling[index] && uint32_t(now-unsensedCloseSince[index])>=cfg::travelCloseMs) settling[index]=false;
    return !(command&(1u<<index)) && !settling[index];
  }
  void setCommand(uint8_t next,uint32_t now) {
    for(unsigned i=0;i<2;i++) if((command & ~next) & (1u<<i)) {
      unsensedCloseSince[i]=now; settling[i]=true;
    }
    for(unsigned i=0;i<2;i++) if ((next^command)&(i==0?Cryo:Turbo)) {
      motion[i]=true; motionSince[i]=now;
    }
    command=next;
  }
  void tick(const Snapshot& s,bool released) {
    const bool wasArmed=armed();
    d=Decision();
    d.status=s.basic;
    if (!primed && s.validPanel) {
      for (unsigned i=0; i<2; ++i) {
        unsensedCloseSince[i]=s.time;
        settling[i]=true;
      }
    }
    const bool roughClosed=primed && s.roughClosure;
    const bool ventClosed=primed && s.ventClosure;
    d.site=(released?1:0)|(ventClosed?2:0)|(roughClosed?4:0)|(s.processSafe?16:0);
    if(s.pressureValid) d.status|=2048;
    updatePressure(s,0,cfg::cryoEnterTorr,cfg::cryoTripTorr,4096,Cryo);
    updatePressure(s,1,cfg::turboEnterTorr,cfg::turboTripTorr,8192,Turbo);
    bool modeChange=s.mode!=previousMode;
    bool edgeAllowed=primed && !modeChange && s.validPanel;
    bool armEdge=edgeAllowed && s.arm && !oldArm;
    bool pumpEdge=edgeAllowed && s.pump && !oldPump, ventEdge=edgeAllowed && s.vent && !oldVent;
    bool neutral=s.selectors==0 && !s.pump && !s.vent;
    if (!primed || modeChange || s.mode==Off) enter(latch?Fault:Disarmed,s.time);
    if (s.mode==Invalid) d.status|=32;
    if (s.mode==Auto && s.selectors) d.events|=4;
    if ((s.pump && s.vent) || (s.mode!=Auto && (s.pump || s.vent))) d.events|=8;
    if ((s.selectors || s.pump || s.vent) && !armed()) d.events|=256;
    if (s.mode==Auto && (s.pump || s.vent || stage>Armed) && stage!=Fault && !cfg::autoPathQualified) d.events|=128;
    supervise(s,0,Cryo,6); supervise(s,1,Turbo,4);
    if (s.mode==Auto && armed() && !(d.events&(4|8|128))) {
      if(ventEdge) enter(VentPreparation,s.time);
      else if(pumpEdge && stage==Armed) enter(Roughing,s.time);
      else if(pumpEdge) d.events|=8;
      switch(stage) {
        case Roughing:
          if(!s.pressureValid) d.events|=32;
          else if(uint32_t(s.time-stageSince)>=cfg::roughdownMs) d.events|=32;
          else if(s.torr<=cfg::roughCrossoverTorr) enter(Isolating,s.time);
          break;
        case Isolating:
          if(!s.pressureValid || uint32_t(s.time-stageSince)>cfg::roughdownMs) d.events|=32;
          else if(!roughClosed && uint32_t(s.time-stageSince)>cfg::travelCloseMs) d.events|=16;
          else if(roughClosed && (s.positions&3)==1 && (d.status&4096)) enter(HighVacuum,s.time);
          break;
        case VentPreparation:
          if(!s.pressureValid) d.events|=32;
          else if(roughClosed && (s.positions&243)==81 && (s.basic&64) && s.processSafe)
            enter(s.torr>=cfg::ventCompleteTorr?VentClosing:Venting,s.time);
          else if(uint32_t(s.time-stageSince)>cfg::travelCloseMs) {
            if(!roughClosed || (s.positions&243)!=81) d.events|=16;
            else if(uint32_t(s.time-stageSince)>cfg::ventMs) d.events|=32;
          }
          break;
        case Venting:
          if(!s.pressureValid || uint32_t(s.time-stageSince)>=cfg::ventMs) d.events|=32;
          else if(s.torr>=cfg::ventCompleteTorr) enter(VentClosing,s.time);
          break;
        case VentClosing:
          if(ventClosed && (s.positions&12)==4) enter(Armed,s.time);
          else if(uint32_t(s.time-stageSince)>cfg::travelCloseMs) d.events|=16;
          break;
        default: break;
      }
    }
    if(s.mode==Manual) d.attempt=s.selectors;
    else if(s.mode==Auto) d.attempt=stage==Roughing?Rough:stage==HighVacuum?Cryo:stage==Venting?Vent:0;
    // Count a path until it is closed. This includes the roughing close interval
    // and gate travel between reed switches during a change of pump path.
    unsigned paths=((d.attempt | command)&(Rough|Turbo|Cryo)) | (roughClosed?0:Rough)
      | ((s.positions&48)==16?0:Turbo) | ((s.positions&192)==64?0:Cryo);
    if(paths==0 || (cfg::allowedPumpMasks & (1u<<paths))) d.site|=8;
    d.alarms=evaluate(d.attempt,s.positions,d.status,d.site,d.events);
    if (((wasArmed || armed()) && d.alarms) || (d.alarms & 8192)) {
      latch|=d.alarms;
      enter(Fault,s.time);
    }
    if (!latch) silenced=false;
    if (stage==Fault && armEdge) silenced=true;
    if (stage==Fault && !armEdge) latch|=d.alarms;
    if (armEdge && neutral && roughClosed && ventClosed && !d.alarms &&
        s.positions==85 && (s.mode==Manual || s.mode==Auto)) {
      if(latch) {latch=0; enter(Disarmed,s.time);} // acknowledge, then a separate arm edge
      else enter(Armed,s.time);
    }
    setCommand(armed() && !d.alarms && released ? d.attempt : 0,s.time);
    primed=s.validPanel; previousMode=s.mode; oldArm=s.arm; oldPump=s.pump; oldVent=s.vent;
  }
};
}
