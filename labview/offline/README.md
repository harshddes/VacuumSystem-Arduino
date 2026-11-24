# MAIZE offline console

Open **MAIZE Offline.lvproj**, open **MAIZE Offline Console.vi**, then press **Ctrl+R**. The model runs inside the Windows software session. It can be used with USB and Ethernet disconnected. The four clickable valve requests follow the same layout as the live panel. A fresh run starts disarmed with four closed indications and a simulated chamber pressure of 760 Torr.

### Try it

1. In **MANUAL**, press **Arm / Reset** with the four requests off. Click **Let-up OPEN** to open it. Keep that request on and click **Roughing OPEN**. The model drops both opening outputs and displays the interlock. The Roughing and Let-up lamps still follow their selectors.
2. Return all four requests to CLOSED. After the model's closing interval, press **Arm / Reset** once to acknowledge the fault and once more to arm. **Close / Stop** drops the opening outputs.
3. To run an automatic pumpdown, leave all four requests off, select **AUTO**, press **Arm / Reset**, then press **Pumpdown**. Watch the pressure fall and the controller transition from Roughing to Isolating to High vacuum. Cryo goes red when the modeled gate reaches its OPEN endpoint. Press **Vent sequence** to return the chamber to the model's vent-complete pressure.
4. Use **Test condition** to exercise pressure loss, pump readiness, interlocks, and gate travel or feedback faults. Select **Normal** to remove the injected condition. **End session** stops the model. Run the VI again to start a fresh model and return any valve requests to CLOSED before arming.

The shared firmware state machine authorizes outputs. LabVIEW rechecks its opening permits and displays active and latched causes. The Turbo and Cryo lamps use modeled gate endpoint feedback. Grey indicates travel or indeterminate feedback. Roughing and Let-up lamps follow their requests, and **Opening outputs** shows what the controller granted in manual and automatic operation. Model pressures, timings and allowed pump combinations are exercise values.

### Build

The compiled Windows helper ships beside the VI, and the project references the shared permission and fault-message VIs one directory up. To rebuild the helper from the repository root with Zig and PowerShell, run `zig c++ -std=c++17 -O2 -s "-Wl,--subsystem,windows" labview/offline/OfflineController.cpp -o labview/offline/MAIZE.Offline.exe`. Run `python labview/offline/verify.py` to check manual conflicts, re-arming, automatic pumpdown and venting, gate timeout, and pressure loss. To regenerate the VIs, use the [LabVIEW build instructions](../README.md) and run `python labview/build_panel.py --offline`.
