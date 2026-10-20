#pragma once
// BENCH SIMULATION ONLY. No field-driver mapping, pressure values or timing qualification.
struct Inputs {
  bool cryoRequest=false, ventRequest=false, cryoClosed=false, ventClosed=false;
  bool pressureValid=false, pressureBand=false, cryoReady=false;
  bool otherPathsClosed=false, filamentProcessSafe=false, reset=false;
};
struct Outputs { bool cryo=false, vent=false, armed=false, denied=false; };
class BenchLogic {
 public:
  Outputs out;
  void tick(const Inputs &in) {
    const bool cryoPermit=in.ventClosed && in.pressureValid && in.pressureBand && in.cryoReady;
    const bool ventPermit=in.cryoClosed && in.otherPathsClosed && in.filamentProcessSafe;
    const bool conflict=in.cryoRequest && in.ventRequest;
    const bool trip=conflict || (out.cryo && !cryoPermit) || (out.vent && !ventPermit);
    if(trip) { out.armed=false; out.cryo=false; out.vent=false; }
    if(!in.cryoRequest) out.cryo=false;
    if(!in.ventRequest) out.vent=false;
    // A re-arm button held at boot is not a new operator action.
    if(!in.reset) resetReleased=true;
    // Re-arm only after a release and new edge with BOTH requests released.
    if(!trip && resetReleased && in.reset && !prev.reset && !in.cryoRequest && !in.ventRequest) out.armed=true;
    // Rejected requests are never queued: only a fresh edge can be accepted.
    if(out.armed && !trip) {
      if(in.cryoRequest && !prev.cryoRequest && cryoPermit) out.cryo=true;
      if(in.ventRequest && !prev.ventRequest && ventPermit) out.vent=true;
    }
    if(!out.armed) { out.cryo=false; out.vent=false; }
    out.denied=(in.cryoRequest && !out.cryo) || (in.ventRequest && !out.vent);
    prev=in;
  }
 private:
  Inputs prev;
  bool resetReleased=false;
};
