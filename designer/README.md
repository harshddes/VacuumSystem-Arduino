# Vacuum System Workbench

A dependency-free, browser-local vacuum design module for the existing Propellant Workbench. This directory is a **reviewable implementation**, not a deployed change to that Site. No firmware or existing controller files are modified.

The source checkout/build workspace was unavailable during preparation. The existing Site could be identified and its hosting state read, but its source could not be opened, edited, built, or published. The existing Site's visual system could not be inspected. This module uses a compatible engineering-workbench layout as a proposed integration surface; an exact match to existing styling remains to be checked.

## Open and test

Serve this directory with any static file server, or open \`index.html\` in a browser. No installation or build is required. Scripts and data are local files. Optional Google Fonts fall back to system fonts.

Run the repeatable logic tests with Node 18 or later:

\`\`\`sh
node designer/core.test.cjs
\`\`\`

During preparation, the same test body was executed in the available V8 runtime: **65 passed, 0 failed**. JavaScript syntax and graph consistency were also checked. Node execution and browser/DOM testing were unavailable and remain to be run. See \`VALIDATION.md\`.

## Included

- Separate plumbing/pneumatics/helium and electrical/control drawings.
- 31 component types: vacuum chamber, gate, cryopump, dry scroll, optional future turbo, valves, lines, gauges, gas services, Uno, MCP23017, DFR0627/DFR0845, Hornet, relay, 24 V supply, pilot coil, diode, reed and operator button.
- Component drag, keyboard movement, editable labels/evidence, typed port connections, connection removal, undo, search, and SVG export. Line crossings are not junctions.
- Independent browser-local project state, validated JSON import/export, connection CSV and drawing component inventory export. A process symbol and its electrical representation are not automatically reconciled into a procurement BOM.
- Preliminary molecular-flow line conductance, series effective pumping speed, gas throughput/pressure floor, constant-speed interval time and N2/air Knudsen estimate.
- Proposed interlock simulator with deliberate re-arm, invalid/stale pressure rejection, fault injection, coil-command/position separation, and no automatic reopening.
- Read-only replay of the numeric Hornet logger CSV format. Sentinel readings and missing samples are omitted from plots; replay never grants a permission.
- Evidence checklist and print/PDF report using the browser's print dialog.

There is no equipment connection, Web Serial support, background service, email sending, or real actuation. Export/import is explicit; browser-local projects do not synchronize across devices. A browser reset may clear local storage; use project export to keep a transferable copy.

## Repository basis

Hardware and firmware references are pinned to:

\`3f1b864bf9a3ba8a5a06289e71fdde082b224b33\` (2026-11-16).

The current circuit uses **MCP B3 / library index 11** for the real closed reed. The damaged open switch and expander A4/B4 are disconnected. Uno D8 drives the relay module IN with the H/L jumper on H. Relay COM/NO switch the separate 24 V Humphrey coil circuit; NC is empty. A 1N400x diode crosses the Humphrey coil with its stripe positive. The 24 V negative stays separate from Uno ground in this bench circuit.

The current DFR0627/DFR0845 trial prose says T→T and R→R, DFR0845 A→Hornet pin 9 (+), and B→pin 6 (−). Older wire schedule and Mermaid rows conflict. The app flags this discrepancy rather than treating the complete harness as released. The Hornet supply and isolated bus-reference limits are retained.

The actual bench sketch accepts gate requests separately from the complete proposed interlock policy. The simulator is **not a digital twin or certification of that firmware**. An unchecked full-system acceptance record stays unchecked.

Plumbing is conceptual, based on the reported Cryo-Torr 8, CTI 8200 and Agilent IDP-15 arrangement. The cryopump pre-evacuation/regeneration route, installed bypasses, vent metering, air port mapping, cooling and mains services still need an as-built survey. Position sensors, readiness and ratings are not inferred from the diagram.

## Calculation scope

Inputs start blank. The N2 example is explicitly labelled and is not the stand's specification. Calculation parameters are entered independently of canvas geometry; moving a line does not imply a physical length.

- Long straight molecular-flow tube: \`C = 12.1 d³/L sqrt(28.97/M) sqrt(T/293.15)\` in L/s, with d and L in cm, T in K and M in g/mol.
- Effective speed: \`1/Seff = 1/Spump + 1/Ctube + 1/Cvalve\`. A blank valve conductance omits that resistance and triggers a notice.
- SCCM reference is 0 °C / 1 atm. Chamber gas throughput scales with T/Tstd.
- Gas-load floor is Q/Seff. Time uses the fixed-volume, fixed-load, constant-speed isothermal solution and refuses targets at or below that floor.
- N2/air mean free path uses a hard-sphere 0.37 nm collision diameter. Knudsen regime thresholds are explanatory approximations; not a transition-flow solver.
- The display warns for short tubes, non-molecular conditions and unconfirmed intervals. Numerical outputs outside the stated regime are unvalidated mathematical estimates, not equipment predictions.
- No water/desorption model, cryopump capacity/regeneration, gas-dependent capture model, pump performance curves, rarefied CFD, or 3D chamber solver is included.

The library includes a turbo as a future option, not as the reported initial configuration.

## Integrate into the existing Site

Target project (copied from Sites): \`appgprj_6af920d6359881919730ca120f080033\`.

When the Site source workspace is available:

1. Open the existing Site source through the supported Sites workflow and preserve its project identity, audience, bindings, integrations and project data.
2. Inspect its actual routing, component system, storage/identity and build output. Do not overwrite the root application.
3. For static assets, copy this directory's browser files into the source's public/static asset directory under \`vacuum/\`. The deployed result should serve \`/vacuum/index.html\`. For a router-based app, mount an equivalent route and reuse the existing shell/tokens; preserve this module's independent state namespace.
4. Add **Vacuum system** beside the existing Propellant workspace navigation, linking to \`/vacuum/index.html\`. The module's Propellant link returns to the existing root.
5. Check that relative script/CSS paths work under the final base path and that existing authentication remains in force.
6. Run \`core.test.cjs\`, complete the browser checklist below, and verify the existing propellant features still work.
7. Package/push/publish through the existing Site's supported workflow without changing its audience.

Do not add another hosting manifest or create a replacement Site. This branch does not contain the existing Site source and cannot complete that integration by itself.

## Browser acceptance checklist

- Load both drawings at desktop and mobile widths; check routing/port labels for overlaps.
- Add and move parts with pointer and keyboard; connect compatible ports, reject incompatible domains, remove edges and undo.
- Export SVG and reopen it; ensure long labels/ports remain readable.
- Export a project; import it into a fresh browser; compare both graphs and sizing inputs.
- Confirm the examples are visibly labelled and values outside molecular flow are flagged.
- Exercise all interlock faults while commanded open; confirm no automatic re-open and no measured OPEN state.
- Import a real repo CSV including gaps/sentinels; inspect log axes and discontinuities.
- Test browser-storage denial and malformed imports; confirm export still works.
- Verify print/PDF output and actual installed-Site navigation/authentication.
