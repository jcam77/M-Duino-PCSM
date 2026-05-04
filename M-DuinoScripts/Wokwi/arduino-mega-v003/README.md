# Wokwi Arduino Mega Simulation For `M_Duino_v003`

This folder helps you simulate the **logic and timing flow** of
[`M_Duino_v003.ino`](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v003/M_Duino_v003.ino)
in Wokwi using an **Arduino Mega**.

`v003` differs from `v002` in one important operator behavior:

- in **spark-test mode**, `ARM` alone no longer starts spark pulses
- spark-test now requires `ARM` **and** an explicit `TRIGGER` press
- each debounced `TRIGGER` press starts one spark pulse

For readability, the Wokwi `v003` simulator also uses:

- `INPUT_PULLUP`
- active-low input wiring inside the simulator only

This keeps the diagram cleaner by removing extra pull-down / 5V wiring on the left side.
It does **not** change the intended operator behavior.

Important limits:

- this is **not** a simulation of the real Industrial Shields M-Duino hardware
- this is **not** a simulation of real relay timing, hot-wire current, ignition coil behavior, or DAQ input electronics
- it is useful for checking:
  - state transitions
  - arm / trigger logic
  - mode switching
  - hot-wire -> spark -> DAQ timing order
  - serial debug output

## Files

- [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/diagram.json)
- [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/mduino_wokwi_pins.h)
- [M_Duino_v003_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/M_Duino_v003_Wokwi.ino)
- [M_Duino_v003_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/M_Duino_v003_Wokwi_visible.ino)

## Pin Mapping Used In The Simulator

| M-Duino symbol | Firmware meaning | Arduino Mega pin |
|---|---|---:|
| `R0_5` | Arm light | `22` |
| `R0_6` | Hot wire 1 | `23` |
| `R0_7` | Hot wire 2 | `24` |
| `R0_8` | Hot wire 3 | `25` |
| `I0_4` | Trigger input | `26` |
| `I0_5` | Mode input | `27` |
| `I0_3` | Arm input | `28` |
| `Q0_1` | Spark output | `29` |
| `Q0_0` | DAQ trigger | `30` |

## Wokwi Controls

- `ARM` slide switch:
  - left = armed
  - right = not armed
- `TRIGGER` pushbutton: momentary trigger command, key `T`
- `MODE` slide switch:
  - left = spark-test mode
  - right = hydrogen-test mode

## How To Use It In Wokwi Web

1. Create a new Arduino Mega project in Wokwi.
2. Replace the default `diagram.json` with the contents of:
   [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/diagram.json)
3. Create a second file in the Wokwi project named `mduino_wokwi_pins.h`.
4. Paste into it the contents of:
   [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/mduino_wokwi_pins.h)
5. Replace the default `sketch.ino` with the contents of:
   [M_Duino_v003_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/M_Duino_v003_Wokwi.ino)
6. Start the simulation and open the Serial Monitor.

If you want the LEDs to be clearly visible during simulation, use this file instead:

- [M_Duino_v003_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v003/M_Duino_v003_Wokwi_visible.ino)

That simulator-only variant uses:
- `hotWireBurn_us = 300 ms`
- `sparkDwell_us = 500 ms`
- `daqPulse_us = 150 ms`

## Recommended Checks In Wokwi

### Spark-test mode

1. Put `MODE` in `HIGH`.
2. Switch `ARM` on.
3. Confirm that **no spark starts automatically**.
4. Press `TRIGGER`.
5. Confirm one spark pulse starts.
6. Release and press `TRIGGER` again.
7. Confirm a new spark pulse starts only on the next trigger press.

### Hydrogen-test mode

1. Put `MODE` in `LOW`.
2. Switch `ARM` on.
3. Press `TRIGGER`.
4. Confirm this sequence:
   - `Arm Light` turns on
   - `Hot Wire 1-3` turn on for the configured burn time
   - hot-wire LEDs turn off
   - `SparkOut` turns on for the dwell interval
   - `DAQTrig` turns on near the end of the dwell interval
   - both outputs turn off
   - the controller stays locked out until `ARM` and `TRIGGER` are released

## What This Simulation Does Not Prove

This simulation is good for firmware logic review, but it does **not** validate:

- real M-Duino input/output delays
- relay actuation timing
- ignition coil dwell or spark energy
- DAQ hardware trigger thresholds
- camera synchronization
- electrical safety behavior

Use it to verify the **state machine and event order**, not the final hardware timing.
