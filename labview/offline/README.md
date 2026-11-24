# MAIZE offline console

Open **MAIZE Offline.lvproj**, open **MAIZE Offline Console.vi**, then press **Ctrl+R**. The Windows helper runs the simulator with USB and Ethernet disconnected. The four maintained requests are arranged Roughing, Let-up, Turbo and Cryo. The mode selector starts at OFF on a fresh open. Blue is **Arm / Reset**, white is **Pumpdown**, yellow is **Vent Start**, and red is **Close / Stop**.

A fresh model starts disarmed at a simulated 760 Torr. Both simulated reed-sensed gates start closed. Roughing and Let-up indications describe the selectors. Leave both requests at CLOSE and allow the simulated startup closing interval to finish before arming.

### Try it

1. In **MANUAL**, press **Arm / Reset** with the four requests at CLOSE. Click **Let-up OPEN** to request opening. Keep that request on and click **Roughing OPEN**. The model drops both opening outputs and displays the interlock. The two selector indicators continue to show the maintained requests.
2. Return all four requests to CLOSE. After the closing interval, press **Arm / Reset** once to acknowledge the fault. Release and press it again to arm. **Close / Stop** removes all opening commands and requires deliberate recovery.
3. To run an automatic pumpdown, leave all four requests at CLOSE, select **AUTO**, press **Arm / Reset**, then press **Pumpdown**. Watch the pressure fall as the sequence moves from Roughing through Isolation to High vacuum. Cryo turns amber when its OPEN reed is made. Press **Vent Start** to run the vent sequence.
4. Use **Test condition** to exercise pressure loss, pump readiness, interlocks and gate travel or feedback faults. **Panel inputs lost** clears the mode and request indications and latches a fault if the controller was armed. Select **Normal** to restore the inputs. **End session** stops the model.

The shared firmware state machine authorizes outputs. LabVIEW rechecks the permit flags and displays active and latched causes. Turbo and Cryo show modeled reeds in green for CLOSED, amber for OPEN, gray for unknown or travel, and red for conflicting contacts. Roughing and Let-up show selector requests in slate and blue. Read **Opening outputs** for the controller's decision in either mode. Model pressures, timings and allowed pump combinations are exercise values.

### Build

The Windows helper ships beside the VI. The project references the shared permission and fault-message VIs one directory up. To rebuild the helper from the repository root with Zig and PowerShell, run `zig c++ -std=c++17 -O2 -s "-Wl,--subsystem,windows" labview/offline/OfflineController.cpp -o labview/offline/MAIZE.Offline.exe`. Run `python labview/offline/verify.py` to test the helper. On other hosts, build a native C++17 executable and pass its path as the first argument to `verify.py`. To regenerate the VIs, use the [LabVIEW build instructions](../README.md) and run `python labview/build_panel.py --offline`.
