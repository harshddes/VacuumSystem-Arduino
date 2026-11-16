/* Pinned repository snapshot and conceptual design library. */
globalThis.VacuumData = {
  "revision": "2026-11-16",
  "repository": "harshddes/VacuumSystem-Arduino",
  "commit": "3f1b864bf9a3ba8a5a06289e71fdde082b224b33",
  "library": {
    "chamber": {
      "name": "Vacuum chamber",
      "group": "Vacuum",
      "symbol": "chamber",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "pump",
          "kind": "vacuum",
          "side": "right",
          "label": "pump"
        },
        {
          "id": "rough",
          "kind": "vacuum",
          "side": "bottom",
          "label": "rough"
        },
        {
          "id": "gauge",
          "kind": "vacuum",
          "side": "top",
          "label": "gauge"
        }
      ],
      "detail": "Connected volume, seals, material and all bypasses require an as-built survey."
    },
    "gate": {
      "name": "HVA / Lesker SG gate",
      "group": "Vacuum",
      "symbol": "gate",
      "ports": [
        {
          "id": "chamber",
          "kind": "vacuum",
          "side": "left",
          "label": "chamber"
        },
        {
          "id": "cryo",
          "kind": "vacuum",
          "side": "right",
          "label": "cryo"
        },
        {
          "id": "C",
          "kind": "pneumatic",
          "side": "top",
          "label": "C"
        },
        {
          "id": "O",
          "kind": "pneumatic",
          "side": "bottom",
          "label": "O"
        }
      ],
      "detail": "Closed reed only. Gate ID and pneumatic port mapping unresolved. NOT_CLOSED is not OPEN."
    },
    "cryo": {
      "name": "Cryo-Torr 8",
      "group": "Vacuum",
      "symbol": "cryo",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "rough",
          "kind": "vacuum",
          "side": "bottom",
          "label": "rough"
        },
        {
          "id": "He supply",
          "kind": "helium",
          "side": "top",
          "label": "He supply"
        },
        {
          "id": "He return",
          "kind": "helium",
          "side": "right",
          "label": "He return"
        }
      ],
      "detail": "Reported pump. Gas-specific speed, capacity, temperature readiness and regeneration remain to qualify."
    },
    "scroll": {
      "name": "Agilent IDP-15",
      "group": "Vacuum",
      "symbol": "pump",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "top",
          "label": "in"
        },
        {
          "id": "exhaust",
          "kind": "vacuum",
          "side": "right",
          "label": "exhaust"
        }
      ],
      "detail": "Dry roughing pump, reported. Verify fitted inlet isolation, running proof and exhaust routing. Exhaust endpoint is concept-only."
    },
    "valve": {
      "name": "Isolation valve",
      "group": "Vacuum",
      "symbol": "valve",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "out",
          "kind": "vacuum",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Proposed functional valve. Specify manual/automatic type and actual closure feedback."
    },
    "vent": {
      "name": "Metered vent valve",
      "group": "Vacuum",
      "symbol": "valve",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "out",
          "kind": "vacuum",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Separate controlled N2 vent route. Actual metering hardware, regulator and pressure rating unresolved."
    },
    "pipe": {
      "name": "Vacuum line",
      "group": "Vacuum",
      "symbol": "pipe",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "out",
          "kind": "vacuum",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Record diameter, length, flange, bends and gas regime. Conductance is pressure-dependent."
    },
    "tee": {
      "name": "Vacuum tee",
      "group": "Vacuum",
      "symbol": "tee",
      "ports": [
        {
          "id": "left",
          "kind": "vacuum",
          "side": "left",
          "label": "left"
        },
        {
          "id": "right",
          "kind": "vacuum",
          "side": "right",
          "label": "right"
        },
        {
          "id": "branch",
          "kind": "vacuum",
          "side": "bottom",
          "label": "branch"
        }
      ],
      "detail": "Three-way vacuum junction."
    },
    "gauge": {
      "name": "Hornet / convection gauge",
      "group": "Vacuum",
      "symbol": "gauge",
      "ports": [
        {
          "id": "vac",
          "kind": "vacuum",
          "side": "bottom",
          "label": "vac"
        }
      ],
      "detail": "IGM402; firmware 3351-100 reported. Range, protocol match, channel location and pressure freshness need qualification."
    },
    "trap": {
      "name": "Foreline trap",
      "group": "Vacuum",
      "symbol": "trap",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "out",
          "kind": "vacuum",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Optional oil-pump inlet trap. Not needed merely because the selected pump is a dry scroll."
    },
    "turbo": {
      "name": "Turbo pump (future)",
      "group": "Vacuum",
      "symbol": "turbo",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        },
        {
          "id": "foreline",
          "kind": "vacuum",
          "side": "bottom",
          "label": "foreline"
        }
      ],
      "detail": "Future option only. Requires matched controller, gas-specific backing limits, readiness and cooling. Not the initial cryo build."
    },
    "exhaust": {
      "name": "Approved exhaust route",
      "group": "Vacuum",
      "symbol": "exhaust",
      "ports": [
        {
          "id": "in",
          "kind": "vacuum",
          "side": "left",
          "label": "in"
        }
      ],
      "detail": "Concept endpoint. Survey the actual outlet and permitted discharge arrangement."
    },
    "nitrogen": {
      "name": "N2 vent supply",
      "group": "Vacuum",
      "symbol": "cylinder",
      "ports": [
        {
          "id": "out",
          "kind": "vacuum",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Concept vent supply with regulator. Cylinder pressure is never a chamber pressure setpoint."
    },
    "air": {
      "name": "Actuation gas supply",
      "group": "Pneumatic",
      "symbol": "cylinder",
      "ports": [
        {
          "id": "out",
          "kind": "pneumatic",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Actuation service, independent of chamber vent and CTI helium. Gate service stated <=80 psig; lower actual limits still apply."
    },
    "regulator": {
      "name": "Filter / regulator",
      "group": "Pneumatic",
      "symbol": "regulator",
      "ports": [
        {
          "id": "in",
          "kind": "pneumatic",
          "side": "left",
          "label": "in"
        },
        {
          "id": "out",
          "kind": "pneumatic",
          "side": "right",
          "label": "out"
        }
      ],
      "detail": "Actuation supply regulation and pressure proof. Actual minimum working pressure unresolved."
    },
    "pilot": {
      "name": "Humphrey 062-4E1 pilot",
      "group": "Pneumatic",
      "symbol": "pilot",
      "ports": [
        {
          "id": "P",
          "kind": "pneumatic",
          "side": "left",
          "label": "P"
        },
        {
          "id": "A",
          "kind": "pneumatic",
          "side": "top",
          "label": "A"
        },
        {
          "id": "B",
          "kind": "pneumatic",
          "side": "right",
          "label": "B"
        },
        {
          "id": "exhaust",
          "kind": "pneumatic",
          "side": "bottom",
          "label": "exhaust"
        }
      ],
      "detail": "Reported body 0624E136, spring-return four-way pilot. Electrical coil is 24 V DC / 6.7 W (~0.28 A). C/O port mapping must be confirmed."
    },
    "pneuExhaust": {
      "name": "Pilot exhaust",
      "group": "Pneumatic",
      "symbol": "exhaust",
      "ports": [
        {
          "id": "in",
          "kind": "pneumatic",
          "side": "left",
          "label": "in"
        }
      ],
      "detail": "Route per the pilot instructions; never block exhaust by assumption."
    },
    "compressor": {
      "name": "CTI 8200 compressor",
      "group": "Services",
      "symbol": "compressor",
      "ports": [
        {
          "id": "He supply",
          "kind": "helium",
          "side": "left",
          "label": "He supply"
        },
        {
          "id": "He return",
          "kind": "helium",
          "side": "bottom",
          "label": "He return"
        }
      ],
      "detail": "Helium refrigeration circuit only. Coldhead drive, mains and variant-specific cooling remain separate services."
    },
    "uno": {
      "name": "Arduino Uno R3",
      "group": "Electrical",
      "symbol": "board",
      "ports": [
        {
          "id": "5V",
          "kind": "logic5",
          "side": "top",
          "label": "5V"
        },
        {
          "id": "GND",
          "kind": "logicGround",
          "side": "bottom",
          "label": "GND"
        },
        {
          "id": "A4/SDA",
          "kind": "SDA",
          "side": "left",
          "label": "A4/SDA"
        },
        {
          "id": "A5/SCL",
          "kind": "SCL",
          "side": "left",
          "label": "A5/SCL"
        },
        {
          "id": "D8",
          "kind": "logicSignal",
          "side": "right",
          "label": "D8"
        },
        {
          "id": "USB",
          "kind": "usb",
          "side": "top",
          "label": "USB"
        }
      ],
      "detail": "D8 HIGH requests coil. D13 onboard L follows closed reed. D5/D6/D7 disconnected. A4/A5 are Uno I2C pins, distinct from expander A4."
    },
    "mcp": {
      "name": "Adafruit 5346 MCP23017",
      "group": "Electrical",
      "symbol": "board",
      "ports": [
        {
          "id": "VIN",
          "kind": "logic5",
          "side": "top",
          "label": "VIN"
        },
        {
          "id": "D0 address +1",
          "kind": "logic5",
          "side": "top",
          "label": "D0 address +1"
        },
        {
          "id": "GND",
          "kind": "logicGround",
          "side": "bottom",
          "label": "GND"
        },
        {
          "id": "SDA",
          "kind": "SDA",
          "side": "left",
          "label": "SDA"
        },
        {
          "id": "SCL",
          "kind": "SCL",
          "side": "left",
          "label": "SCL"
        },
        {
          "id": "B3",
          "kind": "logicSignal",
          "side": "right",
          "label": "B3"
        },
        {
          "id": "A0 request",
          "kind": "logicSignal",
          "side": "right",
          "label": "A0 request"
        }
      ],
      "detail": "Address 0x21. B3/index 11 is real closed reed. Expander A4 and B4 empty. A2 is a simulated cryo-closed jumper, not the gate. Set +1 address solder jumper, or tie board D0 address pin to 5 V; this is not Uno D0."
    },
    "uart": {
      "name": "DFRobot DFR0627",
      "group": "Electrical",
      "symbol": "board",
      "ports": [
        {
          "id": "+",
          "kind": "logic5",
          "side": "top",
          "label": "+"
        },
        {
          "id": "-",
          "kind": "logicGround",
          "side": "bottom",
          "label": "-"
        },
        {
          "id": "D",
          "kind": "SDA",
          "side": "left",
          "label": "D"
        },
        {
          "id": "C",
          "kind": "SCL",
          "side": "left",
          "label": "C"
        },
        {
          "id": "UART1 T",
          "kind": "uartT",
          "side": "right",
          "label": "UART1 T"
        },
        {
          "id": "UART1 R",
          "kind": "uartR",
          "side": "right",
          "label": "UART1 R"
        }
      ],
      "detail": "I2C to dual UART. Current trial uses UART1 T -> DFR0845 T, R -> R. Remove loopback jumpers."
    },
    "rs485": {
      "name": "DFRobot DFR0845",
      "group": "Electrical",
      "symbol": "board",
      "ports": [
        {
          "id": "logic +",
          "kind": "logic5",
          "side": "top",
          "label": "logic +"
        },
        {
          "id": "logic -",
          "kind": "logicGround",
          "side": "bottom",
          "label": "logic -"
        },
        {
          "id": "logic T",
          "kind": "uartT",
          "side": "left",
          "label": "logic T"
        },
        {
          "id": "logic R",
          "kind": "uartR",
          "side": "left",
          "label": "logic R"
        },
        {
          "id": "A (+)",
          "kind": "rsPlus",
          "side": "right",
          "label": "A (+)"
        },
        {
          "id": "B (-)",
          "kind": "rsMinus",
          "side": "right",
          "label": "B (-)"
        },
        {
          "id": "bus GND",
          "kind": "busGround",
          "side": "bottom",
          "label": "bus GND"
        }
      ],
      "detail": "Isolated RS485. Current trial: screw A -> Hornet 9 (+), B -> Hornet 6 (-). Bus reference is separate from logic -. 12 V screws unused."
    },
    "hornet": {
      "name": "InstruTech IGM402",
      "group": "Electrical",
      "symbol": "instrument",
      "ports": [
        {
          "id": "DE9 pin 9 (+)",
          "kind": "rsPlus",
          "side": "left",
          "label": "DE9 pin 9 (+)"
        },
        {
          "id": "DE9 pin 6 (-)",
          "kind": "rsMinus",
          "side": "left",
          "label": "DE9 pin 6 (-)"
        },
        {
          "id": "DE9 pin 4",
          "kind": "busGround",
          "side": "bottom",
          "label": "DE9 pin 4"
        }
      ],
      "detail": "Keep approved existing supply. RS485 pin 2 stays disconnected in this trial. Separate shell GND is not pin 4. 19200 8N1; current firmware polls addresses 1 and 2."
    },
    "relay": {
      "name": "Tongling 5 V relay module",
      "group": "Electrical",
      "symbol": "relay",
      "ports": [
        {
          "id": "DC+",
          "kind": "logic5",
          "side": "top",
          "label": "DC+"
        },
        {
          "id": "DC-",
          "kind": "logicGround",
          "side": "bottom",
          "label": "DC-"
        },
        {
          "id": "IN",
          "kind": "logicSignal",
          "side": "left",
          "label": "IN"
        },
        {
          "id": "COM",
          "kind": "field24",
          "side": "right",
          "label": "COM"
        },
        {
          "id": "NO",
          "kind": "field24",
          "side": "right",
          "label": "NO"
        }
      ],
      "detail": "JQC-3FF-S-Z module with onboard driver. Jumper H; NC empty. 5 V logic side and dry contact side shown separately."
    },
    "psu": {
      "name": "24 V DC supply",
      "group": "Electrical",
      "symbol": "supply",
      "ports": [
        {
          "id": "+24V",
          "kind": "field24",
          "side": "right",
          "label": "+24V"
        },
        {
          "id": "0V",
          "kind": "fieldReturn",
          "side": "bottom",
          "label": "0V"
        }
      ],
      "detail": "Humphrey coil supply only. Do not join 24 V negative to Uno ground in this circuit. Supply rating, fuse and enclosure require installed-system design."
    },
    "coil": {
      "name": "Humphrey 24 V coil",
      "group": "Electrical",
      "symbol": "coil",
      "ports": [
        {
          "id": "lead A +",
          "kind": "field24",
          "side": "left",
          "label": "lead A +"
        },
        {
          "id": "lead B -",
          "kind": "fieldReturn",
          "side": "bottom",
          "label": "lead B -"
        }
      ],
      "detail": "6.7 W / 24 V ~0.28 A. Relay NO feeds lead A. 1N400x flyback stripe toward positive."
    },
    "diode": {
      "name": "1N400x flyback diode",
      "group": "Electrical",
      "symbol": "diode",
      "ports": [
        {
          "id": "K stripe +",
          "kind": "field24",
          "side": "left",
          "label": "K stripe +"
        },
        {
          "id": "A -",
          "kind": "fieldReturn",
          "side": "bottom",
          "label": "A -"
        }
      ],
      "detail": "Across Humphrey coil only; cathode stripe on switched +24 V side. Relay module already has its own coil suppression."
    },
    "reed": {
      "name": "SG closed reed",
      "group": "Electrical",
      "symbol": "contact",
      "ports": [
        {
          "id": "signal",
          "kind": "logicSignal",
          "side": "left",
          "label": "signal"
        },
        {
          "id": "return",
          "kind": "logicGround",
          "side": "bottom",
          "label": "return"
        }
      ],
      "detail": "Two-wire dry contact: B3 -> closed reed -> logic GND. Open/melted switch disconnected. No measured OPEN proof."
    },
    "button": {
      "name": "Gate request button",
      "group": "Electrical",
      "symbol": "contact",
      "ports": [
        {
          "id": "signal",
          "kind": "logicSignal",
          "side": "left",
          "label": "signal"
        },
        {
          "id": "return",
          "kind": "logicGround",
          "side": "bottom",
          "label": "return"
        }
      ],
      "detail": "Momentary button on MCP A0; rising edge toggles bench coil memory. Panel requests do not prove actual gate position."
    },
    "computer": {
      "name": "PC / Python GUI",
      "group": "Electrical",
      "symbol": "computer",
      "ports": [
        {
          "id": "USB",
          "kind": "usb",
          "side": "bottom",
          "label": "USB"
        }
      ],
      "detail": "Existing Tk GUI: pressure plots, gate request and pump-down. Designer has no live serial connection and sends no hardware commands."
    },
    "driver6318": {
      "name": "Adafruit 6318 (unused)",
      "group": "Electrical",
      "symbol": "board",
      "ports": [
        {
          "id": "VCC",
          "kind": "logic5",
          "side": "top",
          "label": "VCC"
        },
        {
          "id": "GND",
          "kind": "logicGround",
          "side": "bottom",
          "label": "GND"
        },
        {
          "id": "SDA",
          "kind": "SDA",
          "side": "left",
          "label": "SDA"
        },
        {
          "id": "SCL",
          "kind": "SCL",
          "side": "left",
          "label": "SCL"
        }
      ],
      "detail": "Earlier bench hardware only. Not in the current Phase 3 gate circuit; load terminals and V+ remain empty."
    }
  },
  "presets": {
    "process": {
      "nodes": [
        {
          "id": "CH1",
          "type": "chamber",
          "name": "Test chamber",
          "x": 470,
          "y": 270,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "G1",
          "type": "gate",
          "name": "Cryo gate",
          "x": 770,
          "y": 270,
          "status": "bench",
          "evidence": "Closed reed B3; gate ID unresolved"
        },
        {
          "id": "CP1",
          "type": "cryo",
          "name": "Cryo-Torr 8",
          "x": 1070,
          "y": 270,
          "status": "reported",
          "evidence": ""
        },
        {
          "id": "V1",
          "type": "valve",
          "name": "Roughing isolation",
          "x": 470,
          "y": 550,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "RP1",
          "type": "scroll",
          "name": "IDP-15",
          "x": 470,
          "y": 820,
          "status": "reported",
          "evidence": ""
        },
        {
          "id": "E1",
          "type": "exhaust",
          "name": "Pump exhaust",
          "x": 820,
          "y": 820,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "N1",
          "type": "nitrogen",
          "name": "N2 vent + regulation",
          "x": 30,
          "y": 270,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "V2",
          "type": "vent",
          "name": "Metered vent",
          "x": 250,
          "y": 270,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "PG1",
          "type": "gauge",
          "name": "Chamber gauge",
          "x": 470,
          "y": 30,
          "status": "reported",
          "evidence": "Channel location to confirm"
        },
        {
          "id": "HE1",
          "type": "compressor",
          "name": "CTI 8200",
          "x": 1310,
          "y": 40,
          "status": "reported",
          "evidence": ""
        },
        {
          "id": "AIR1",
          "type": "air",
          "name": "Actuation supply",
          "x": 30,
          "y": 560,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "REG1",
          "type": "regulator",
          "name": "Air regulation",
          "x": 250,
          "y": 560,
          "status": "proposed",
          "evidence": ""
        },
        {
          "id": "SV1",
          "type": "pilot",
          "name": "Humphrey pilot",
          "x": 770,
          "y": 560,
          "status": "bench",
          "evidence": "P/A/B to actuator C/O needs confirmation"
        },
        {
          "id": "AE1",
          "type": "pneuExhaust",
          "name": "Pilot exhaust",
          "x": 1070,
          "y": 820,
          "status": "proposed",
          "evidence": ""
        }
      ],
      "edges": [
        {
          "id": "vac1",
          "a": {
            "node": "N1",
            "port": "out"
          },
          "b": {
            "node": "V2",
            "port": "in"
          }
        },
        {
          "id": "vac2",
          "a": {
            "node": "V2",
            "port": "out"
          },
          "b": {
            "node": "CH1",
            "port": "in"
          }
        },
        {
          "id": "vac3",
          "a": {
            "node": "CH1",
            "port": "pump"
          },
          "b": {
            "node": "G1",
            "port": "chamber"
          }
        },
        {
          "id": "vac4",
          "a": {
            "node": "G1",
            "port": "cryo"
          },
          "b": {
            "node": "CP1",
            "port": "in"
          }
        },
        {
          "id": "vac5",
          "a": {
            "node": "CH1",
            "port": "rough"
          },
          "b": {
            "node": "V1",
            "port": "in"
          }
        },
        {
          "id": "vac6",
          "a": {
            "node": "V1",
            "port": "out"
          },
          "b": {
            "node": "RP1",
            "port": "in"
          }
        },
        {
          "id": "vac7",
          "a": {
            "node": "RP1",
            "port": "exhaust"
          },
          "b": {
            "node": "E1",
            "port": "in"
          }
        },
        {
          "id": "vac8",
          "a": {
            "node": "PG1",
            "port": "vac"
          },
          "b": {
            "node": "CH1",
            "port": "gauge"
          }
        },
        {
          "id": "he1",
          "a": {
            "node": "CP1",
            "port": "He supply"
          },
          "b": {
            "node": "HE1",
            "port": "He supply"
          }
        },
        {
          "id": "he2",
          "a": {
            "node": "CP1",
            "port": "He return"
          },
          "b": {
            "node": "HE1",
            "port": "He return"
          }
        },
        {
          "id": "air1",
          "a": {
            "node": "AIR1",
            "port": "out"
          },
          "b": {
            "node": "REG1",
            "port": "in"
          }
        },
        {
          "id": "air2",
          "a": {
            "node": "REG1",
            "port": "out"
          },
          "b": {
            "node": "SV1",
            "port": "P"
          }
        },
        {
          "id": "air3",
          "a": {
            "node": "SV1",
            "port": "A"
          },
          "b": {
            "node": "G1",
            "port": "C"
          }
        },
        {
          "id": "air4",
          "a": {
            "node": "SV1",
            "port": "B"
          },
          "b": {
            "node": "G1",
            "port": "O"
          }
        },
        {
          "id": "air5",
          "a": {
            "node": "SV1",
            "port": "exhaust"
          },
          "b": {
            "node": "AE1",
            "port": "in"
          }
        }
      ]
    },
    "electrical": {
      "nodes": [
        {
          "id": "PC1",
          "type": "computer",
          "name": "Python GUI / laptop",
          "x": 60,
          "y": 20,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "U1",
          "type": "uno",
          "name": "Uno R3",
          "x": 60,
          "y": 250,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "U2",
          "type": "mcp",
          "name": "5346 · 0x21",
          "x": 400,
          "y": 20,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "U3",
          "type": "uart",
          "name": "DFR0627 · UART1",
          "x": 400,
          "y": 300,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "U4",
          "type": "rs485",
          "name": "DFR0845 · isolated",
          "x": 780,
          "y": 300,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "IG1",
          "type": "hornet",
          "name": "Hornet · addr 1 / 2",
          "x": 1190,
          "y": 300,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "K1",
          "type": "relay",
          "name": "Tongling · jumper H",
          "x": 780,
          "y": 600,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "PS1",
          "type": "psu",
          "name": "24 V field supply",
          "x": 400,
          "y": 850,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "SOL1",
          "type": "coil",
          "name": "Humphrey · 6.7 W",
          "x": 1190,
          "y": 700,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "D1",
          "type": "diode",
          "name": "1N400x · stripe +",
          "x": 1190,
          "y": 990,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "SW1",
          "type": "reed",
          "name": "Closed reed · B3",
          "x": 780,
          "y": 20,
          "status": "bench",
          "evidence": ""
        },
        {
          "id": "SW2",
          "type": "button",
          "name": "Gate button · A0",
          "x": 1190,
          "y": 20,
          "status": "bench",
          "evidence": ""
        }
      ],
      "edges": [
        {
          "id": "w1",
          "a": {
            "node": "PC1",
            "port": "USB"
          },
          "b": {
            "node": "U1",
            "port": "USB"
          }
        },
        {
          "id": "w2",
          "a": {
            "node": "U1",
            "port": "5V"
          },
          "b": {
            "node": "U2",
            "port": "VIN"
          }
        },
        {
          "id": "w3",
          "a": {
            "node": "U1",
            "port": "GND"
          },
          "b": {
            "node": "U2",
            "port": "GND"
          }
        },
        {
          "id": "w4",
          "a": {
            "node": "U1",
            "port": "A4/SDA"
          },
          "b": {
            "node": "U2",
            "port": "SDA"
          }
        },
        {
          "id": "w5",
          "a": {
            "node": "U1",
            "port": "A5/SCL"
          },
          "b": {
            "node": "U2",
            "port": "SCL"
          }
        },
        {
          "id": "w6",
          "a": {
            "node": "U1",
            "port": "5V"
          },
          "b": {
            "node": "U3",
            "port": "+"
          }
        },
        {
          "id": "w7",
          "a": {
            "node": "U1",
            "port": "GND"
          },
          "b": {
            "node": "U3",
            "port": "-"
          }
        },
        {
          "id": "w8",
          "a": {
            "node": "U1",
            "port": "A4/SDA"
          },
          "b": {
            "node": "U3",
            "port": "D"
          }
        },
        {
          "id": "w9",
          "a": {
            "node": "U1",
            "port": "A5/SCL"
          },
          "b": {
            "node": "U3",
            "port": "C"
          }
        },
        {
          "id": "w10",
          "a": {
            "node": "U1",
            "port": "5V"
          },
          "b": {
            "node": "U4",
            "port": "logic +"
          }
        },
        {
          "id": "w11",
          "a": {
            "node": "U1",
            "port": "GND"
          },
          "b": {
            "node": "U4",
            "port": "logic -"
          }
        },
        {
          "id": "w12",
          "a": {
            "node": "U3",
            "port": "UART1 T"
          },
          "b": {
            "node": "U4",
            "port": "logic T"
          }
        },
        {
          "id": "w13",
          "a": {
            "node": "U3",
            "port": "UART1 R"
          },
          "b": {
            "node": "U4",
            "port": "logic R"
          }
        },
        {
          "id": "w14",
          "a": {
            "node": "U4",
            "port": "A (+)"
          },
          "b": {
            "node": "IG1",
            "port": "DE9 pin 9 (+)"
          }
        },
        {
          "id": "w15",
          "a": {
            "node": "U4",
            "port": "B (-)"
          },
          "b": {
            "node": "IG1",
            "port": "DE9 pin 6 (-)"
          }
        },
        {
          "id": "w16",
          "a": {
            "node": "U4",
            "port": "bus GND"
          },
          "b": {
            "node": "IG1",
            "port": "DE9 pin 4"
          }
        },
        {
          "id": "w17",
          "a": {
            "node": "U1",
            "port": "5V"
          },
          "b": {
            "node": "K1",
            "port": "DC+"
          }
        },
        {
          "id": "w18",
          "a": {
            "node": "U1",
            "port": "GND"
          },
          "b": {
            "node": "K1",
            "port": "DC-"
          }
        },
        {
          "id": "w19",
          "a": {
            "node": "U1",
            "port": "D8"
          },
          "b": {
            "node": "K1",
            "port": "IN"
          }
        },
        {
          "id": "w20",
          "a": {
            "node": "PS1",
            "port": "+24V"
          },
          "b": {
            "node": "K1",
            "port": "COM"
          }
        },
        {
          "id": "w21",
          "a": {
            "node": "K1",
            "port": "NO"
          },
          "b": {
            "node": "SOL1",
            "port": "lead A +"
          }
        },
        {
          "id": "w22",
          "a": {
            "node": "SOL1",
            "port": "lead B -"
          },
          "b": {
            "node": "PS1",
            "port": "0V"
          }
        },
        {
          "id": "w23",
          "a": {
            "node": "SOL1",
            "port": "lead A +"
          },
          "b": {
            "node": "D1",
            "port": "K stripe +"
          }
        },
        {
          "id": "w24",
          "a": {
            "node": "SOL1",
            "port": "lead B -"
          },
          "b": {
            "node": "D1",
            "port": "A -"
          }
        },
        {
          "id": "w25",
          "a": {
            "node": "U2",
            "port": "B3"
          },
          "b": {
            "node": "SW1",
            "port": "signal"
          }
        },
        {
          "id": "w26",
          "a": {
            "node": "SW1",
            "port": "return"
          },
          "b": {
            "node": "U1",
            "port": "GND"
          }
        },
        {
          "id": "w27",
          "a": {
            "node": "U2",
            "port": "A0 request"
          },
          "b": {
            "node": "SW2",
            "port": "signal"
          }
        },
        {
          "id": "w28",
          "a": {
            "node": "SW2",
            "port": "return"
          },
          "b": {
            "node": "U1",
            "port": "GND"
          }
        },
        {
          "id": "w29",
          "a": {
            "node": "U1",
            "port": "5V"
          },
          "b": {
            "node": "U2",
            "port": "D0 address +1"
          }
        }
      ]
    }
  },
  "sources": [
    {
      "id": "NASA",
      "title": "NASA Langley: 6 ft × 6 ft TVAC upgrades (2014)",
      "url": "https://ntrs.nasa.gov/citations/20150000594",
      "use": "Inspiration for valve permission matrix and independent hardware interlocks; no claim of NASA certification."
    },
    {
      "id": "CERN",
      "title": "CERN: Vacuum Controls and Diagnostics (2020)",
      "url": "https://cds.cern.ch/record/2723216/files/2006.03263.pdf",
      "use": "Field devices, interface/controllers, machine protection and supervisory display as distinct layers."
    },
    {
      "id": "LEYBOLD",
      "title": "Leybold: Fundamentals of Vacuum Technology",
      "url": "https://www.leybold.com/content/dam/brands/leybold/downloads/brochures/general-brochures/Fundamentals_of_Vacuum_Technology_EN.pdf",
      "use": "Long-tube molecular conductance (air baseline), series conductance and effective pumping speed. Gas and temperature scaling use kinetic-theory square-root dependence."
    },
    {
      "id": "CONDUCTANCE",
      "title": "Leybold: Calculating conductance values",
      "url": "https://content.leybold.com/migration/en/knowledge/how-to-calculate-conductance-values",
      "use": "1/Seff = 1/Spump + 1/C; conductance depends on flow regime."
    },
    {
      "id": "GATE",
      "title": "Repo: current Phase 3 gate wiring",
      "url": "https://github.com/harshddes/VacuumSystem-Arduino/blob/3f1b864bf9a3ba8a5a06289e71fdde082b224b33/development/bench-prep/08-gate-position.md",
      "use": "D8/relay/24 V coil, B3 closed reed, isolated field return, disconnected damaged switch."
    },
    {
      "id": "HOLDS",
      "title": "Repo: field holds",
      "url": "https://github.com/harshddes/VacuumSystem-Arduino/blob/3f1b864bf9a3ba8a5a06289e71fdde082b224b33/development/bench-prep/06-field-holds.md",
      "use": "Unknown gate diameter, air-loss behavior, independent inhibit and unqualified interfaces remain visible."
    },
    {
      "id": "RS485",
      "title": "Repo: Hornet read trial, latest prose wiring",
      "url": "https://github.com/harshddes/VacuumSystem-Arduino/blob/3f1b864bf9a3ba8a5a06289e71fdde082b224b33/development/bench-prep/07-hornet-read-trial.md",
      "use": "T→T, R→R; DFR0845 A→pin 9, B→pin 6. Older Mermaid and wire-schedule rows conflict. Resolve before issuing an as-built harness."
    },
    {
      "id": "FIRMWARE",
      "title": "Repo: actual current bench firmware",
      "url": "https://github.com/harshddes/VacuumSystem-Arduino/blob/3f1b864bf9a3ba8a5a06289e71fdde082b224b33/development/bench-prep/firmware/gpio_interlock_bench/gpio_interlock_bench.ino",
      "use": "B3 index 11, D8, 300 ms expander-loss handling, o/c/x requests, four convection channels. Current gate commands do not enforce the proposed complete interlocks."
    },
    {
      "id": "GUI",
      "title": "Repo: Python GUI sequence logic",
      "url": "https://github.com/harshddes/VacuumSystem-Arduino/blob/3f1b864bf9a3ba8a5a06289e71fdde082b224b33/development/bench-prep/hornet_plot/logic.py",
      "use": "1100 Torr open-jack and ≥9e9 off flags; GUI thresholds are implementation history, not released physical limits."
    },
    {
      "id": "INVENTORY",
      "title": "Repo: equipment inventory",
      "url": "https://github.com/harshddes/VacuumSystem-Arduino/blob/3f1b864bf9a3ba8a5a06289e71fdde082b224b33/development/07-machines.md",
      "use": "Cryo-Torr 8, CTI 8200, IDP-15; turbo is a future option. Plumbing is a concept, not a surveyed installation."
    }
  ]
};
