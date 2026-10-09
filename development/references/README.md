# Sources, evidence and laboratory references

Revision 2026-10-09

Manufacturer documents govern the particular component revision. Reported model names identify the research target, but do not prove installed configuration or functionality. Connector drawings and operating limits must match the actual unit and firmware. This package links commercial manuals rather than republishing them wholesale.

## Manufacturer sources

| Source | Use in this baseline |
|---|---|
| [Arduino Uno R3](https://docs.arduino.cc/hardware/uno-rev3/) | Board/pin reference; existing repository `docs/` contains board documents |
| [InstruTech IGM402 product](https://www.instrutechinc.com/products/full-range-vacuum-gauges/igm402-hornet-hot-cathode) | Current instrument capability and current power statement |
| [InstruTech archived manual index](https://www.instrutechinc.com/downloads/archived-user-manuals) | Firmware-to-manual matching |
| [IGM402 manual 000861-115](https://www.instrutechinc.com/media/127/download/IGM402%20User%20Manual%20Archived%20000861-115.pdf?v=1) | Firmware 1769-108; power, accessories, connector and communications reference; sections 1, 3.3, 5 and 8 |
| [InstruTech VGC301 manual](https://www.instrutechinc.com/media/51/download/VGC301%20User%20Manual.pdf?v=1) | Supplemental CVG101 model information; not a substitute for the Hornet's sensor-cable specification |
| [CTI 8200 OEM manual, RIT-hosted](https://www.cfd.rit.edu/products/manuals/CTI/8040353.pdf) | Compressor variants and power/cooling/helium/coldhead service requirements |
| [Cryo-Torr OEM instructions, Edwards](https://global.my.edwardsvacuum.com/medias/8040613-Instructions.pdf?attachment=true&context=bWFzdGVyfHJvb3R8NzgyNTU4fGFwcGxpY2F0aW9uL3BkZnxhRGRsTDJnME9TODJOakUyTkRrd09ERTVOVGczTUM4NE1EUXdOakV6SUMwZ1NXNXpkSEoxWTNScGIyNXpMbkJrWmd8ZmZhZjNjMzhmODExOTA5Nzg1MWQ2MWJiMzAzOTcxY2VmOGQxZWY0NTA4ZDZhZWU1Y2QzMzk5NjE5ODNlMWUyZQ) | Cryopump installation, temperature/crossover and regeneration limits; confirm applicability |
| [Cryo-Torr instructions, alternate OEM-manual host](https://www.idealvac.com/files/manuals/Cryo-Pumps_Install_1.pdf) | Alternate access to the manufacturer manual |
| [Agilent IDP-15](https://www.agilent.com/en/product/vacuum-technologies/dry-scroll-pumps/idp-pumps/idp-15-dry-scroll-pump) | Pump role, ports and installed-variant investigation |
| [Agilent IDP inlet-valve kit instructions](https://www.agilent.com/cs/library/usermanuals/Public/6999-04-370B%20IDP%20Series%20Inlet%20Valve%20Kit%20Instruction%20Manual.pdf) | Optional kit; presence and independent controllability still unverified |
| [Lesker molecular-sieve foreline traps](https://www.lesker.com/newweb/traps/forelinetraps_molecularsieve.cfm?pgid=inlinestraight) | Reported TSR4MS100QF trap identification; inlet versus exhaust distinction |
| [DFRobot DFR0627](https://www.dfrobot.com/product-2001.html) | Proposed additional UART; follow OEM wiring/library documentation |
| [DFRobot DFR0845](https://www.dfrobot.com/product-2392.html) | Isolated RS-485 interface; supply and isolation boundary |
| [Adafruit 6318](https://www.adafruit.com/product/6318) | Conditional DC solenoid driver; continuous rating must suit actual coil |
| [Lesker pneumatic angle-valve family](https://www.lesker.com/newweb/valves/pneumaticangle.cfm) | Candidate only; exact part/feedback/pilot specifications required before purchase |

Procurement links and price-check dates are in [BOM.md](../procurement/BOM.md) and the workbook. Historical quotes are not stock promises.

## Supplied laboratory guides

- [Chemical laboratory safety resources](lab/chemical-laboratory-safety-resources.pdf): the supplied EHS_BLS025w resource guide, preserved unchanged. It is a resource/contact index, not a vacuum-controller specification.
- [PPML safety guide](lab/PPML_safety_guide-optimized.pdf): all 105 pages of the supplied guide, optimized for repository transfer. Text/vector content is retained; embedded images are downsampled. The original source's SHA-256 is recorded in [the source manifest](source-manifest.json).

The PPML guide describes laboratory machine interlocks and individually securing gas cylinders. Its interlock-defeat procedure applies to working on existing machine interlocks. This development plan does not authorize bypassing those interlocks. Keep existing laboratory instructions alongside the manufacturer's procedures when commissioning the physical system.

## Evidence levels

1. **User reported:** equipment names and possession supplied in the conversation.
2. **Photo inference:** large gate appears pneumatic; small valves appear handwheel-operated. Not definitive model or terminal identification.
3. **Manufacturer-supported family/reference facts:** research cited above, with firmware/configuration applicability checks still required.
4. **Software verified:** current bench core scenarios and host syntax check, recorded in `verification/host-test-results.txt`.
5. **Physically verified:** initially none in this package. Record actual results and evidence as development proceeds.

No uncertain valve model, operating threshold, product review score or physical acceptance result has been promoted to a known fact.
