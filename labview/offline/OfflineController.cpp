#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <tuple>

// These values describe the offline exercise, in simulated Torr and milliseconds.
namespace installation {
constexpr bool autoPathQualified = true;
constexpr uint32_t travelOpenMs = 2400, travelCloseMs = 1600;
constexpr uint32_t pressureDwellMs = 600, roughdownMs = 24000, ventMs = 12000;
constexpr float cryoEnterTorr = 1, cryoTripTorr = 2, turboEnterTorr = 1, turboTripTorr = 2;
constexpr float roughCrossoverTorr = 0.8f, ventCompleteTorr = 700;
constexpr uint16_t allowedPumpMasks = (1u << 1) | (1u << 4) | (1u << 8);
}
#include "../firmware/OptaTelemetry/Controller.h"

namespace {
using namespace maize;
constexpr uint32_t scanMs = 200, gateTravelMs = 600;
constexpr float atmosphere = 760;
constexpr unsigned ready = 1 | 2 | 4 | 8 | 16 | 64 | 128 | 256 | 512 | 1024;
enum Condition {
    Normal, PressureLost, AirLost, RoughNotReady, CryoNotReady, TurboNotReady, BackingLost,
    FilamentOn, LabDisabled, CoilFeedLost, VentInhibited, TurboStuck, CryoStuck,
    TurboConflict, CryoConflict, PanelInputsLost
};
constexpr unsigned missingStatus[] = {0, 0, 2, 128, 256, 512, 1024, 64, 4, 8, 0, 0, 0, 0, 0, 16};

struct Model {
    Controller control;
    uint32_t now = 0;
    float pressure = atmosphere;
    unsigned cryoPosition = 1, turboPosition = 1, mode = Manual, previousMode = Invalid, command = 0;
    unsigned stage = Disarmed;

    // Each operating VI carries its own state between calls. No file, daemon or shared session state.
    auto fields() {
        return std::tie(now, pressure, cryoPosition, turboPosition, previousMode, command, stage,
                        control.primed, control.oldArm, control.oldPump, control.oldVent, control.silenced,
                        control.latch, control.stageSince,
                        control.motion[0], control.motion[1], control.motionSince[0], control.motionSince[1],
                        control.below[0], control.below[1], control.belowSince[0], control.belowSince[1],
                        control.qualifiedBelow[0], control.qualifiedBelow[1],
                        control.settling[0], control.settling[1], control.unsensedCloseSince[0],
                        control.unsensedCloseSince[1]);
    }
    bool load(std::istream& in) {
        std::apply([&](auto&... field) { (in >> ... >> field); }, fields());
        if (!in || !std::isfinite(pressure) || pressure <= 0 || pressure > atmosphere ||
            cryoPosition > 2 || turboPosition > 2 || previousMode > Invalid ||
            command > 15 || stage > Fault || control.latch > 0x7fffffff) return false;
        control.previousMode = Mode(previousMode);
        control.command = command;
        control.stage = Stage(stage);
        return true;
    }
    void store(std::ostream& out) {
        previousMode = control.previousMode;
        command = control.command;
        stage = control.stage;
        out << std::setprecision(9) << '1';
        std::apply([&](const auto&... field) { ((out << ' ' << field), ...); }, fields());
    }
    unsigned position(unsigned current, unsigned index, Valve valve, bool stuck) const {
        if (stuck) return current;
        if (control.motion[index] && now-control.motionSince[index] < gateTravelMs) return 0;
        return control.command & valve ? 2 : 1;
    }
    Snapshot tick(unsigned requests, Condition fault) {
        now += scanMs;
        if (control.command & Vent) pressure += (atmosphere-pressure)*0.23f;
        if (control.command & Rough) pressure = 0.04f+(pressure-0.04f)*0.78f;
        if (((control.command & Turbo) && turboPosition==2) || ((control.command & Cryo) && cryoPosition==2))
            pressure = 0.00001f+(pressure-0.00001f)*0.71f;
        cryoPosition = position(cryoPosition, 0, Cryo, fault==CryoStuck);
        turboPosition = position(turboPosition, 1, Turbo, fault==TurboStuck);

        Snapshot s;
        s.time = now;
        s.selectors = requests & 15;
        s.positions = (s.selectors & Rough ? 2 : 1) | (s.selectors & Vent ? 8 : 4);
        s.positions |= (fault==TurboConflict ? 3 : turboPosition) << 4;
        s.positions |= (fault==CryoConflict ? 3 : cryoPosition) << 6;
        s.mode = Mode(mode);
        s.arm = requests & 16;
        s.pump = requests & 32;
        s.vent = requests & 64;
        s.basic = ready & ~missingStatus[fault];
        if (requests & 128) s.basic &= ~1u;
        s.validPanel = fault!=PanelInputsLost;
        s.roughClosure = !(s.selectors & Rough) && control.closedOutput(0, now);
        s.ventClosure = !(s.selectors & Vent) && control.closedOutput(1, now);
        s.processSafe = fault!=VentInhibited;
        s.pressureValid = fault!=PressureLost;
        s.torr = pressure;
        control.tick(s, true);
        return s;
    }
};
}

int run() {
    Model model;
    unsigned requests, mode, fault;
    if (!(std::cin >> requests >> mode >> fault) || requests > 255 || mode > Auto || fault > PanelInputsLost)
        return 1;
    unsigned version;
    if (std::cin >> version) {
        if (version != 1 || !model.load(std::cin)) return 1;
    } else if (!std::cin.eof()) return 1;
    model.mode = mode;
    auto s = model.tick(requests, Condition(fault));
    const auto& c = model.control;
    const auto& d = c.d;
    static const char* modes[] = {"OFF","MANUAL","AUTO"};
    static const char* stages[] = {"Disarmed","Armed","Roughing","Isolating roughing path","High vacuum",
                                   "Preparing to vent","Venting","Closing let-up","Fault latched"};
    static const char* names[] = {"Roughing","Let-up","Turbo","Cryo"};
    model.store(std::cout);
    std::cout << "|Offline model ready|" << modes[s.mode] << " / " << stages[c.stage] << '|';
    if (s.pressureValid) std::cout << std::setprecision(4) << s.torr << " simulated Torr";
    else std::cout << "Pressure signal unavailable";
    std::cout << '|' << d.attempt << '|' << s.positions << '|' << d.status << '|' << d.site << '|'
        << d.events << '|' << c.latch << '|' << d.alarms << "|1|";
    bool first = true;
    for (unsigned i=0; i<4; ++i) {
        unsigned bit = 1u << i;
        if (!((c.command | s.selectors | d.attempt) & bit)) continue;
        if (!first) std::cout << ", ";
        std::cout << names[i] << (c.command & bit ? " OPEN command" : " request inhibited");
        first = false;
    }
    if (first) std::cout << "All opening outputs off";
    std::cout << '|' << unsigned(s.selectors) << "|15\n";
    return 0;
}

#ifdef _WIN32
int __stdcall WinMain(void*,void*,char*,int) { return run(); }
#else
int main() { return run(); }
#endif
