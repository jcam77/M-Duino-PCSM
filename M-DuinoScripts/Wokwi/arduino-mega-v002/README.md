# Wokwi Arduino Mega Simulation For `M_Duino_v002`

This folder helps you simulate the **logic and timing flow** of
[`M_Duino_v002.ino`](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v002/M_Duino_v002.ino)
in Wokwi using an **Arduino Mega**.

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

- [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/diagram.json)
- [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/mduino_wokwi_pins.h)
- [M_Duino_v002_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/M_Duino_v002_Wokwi.ino)
- [M_Duino_v002_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/M_Duino_v002_Wokwi_visible.ino)

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

- `ARM` slide switch: maintained arm signal
- `TRIGGER` pushbutton: press with keyboard key `T`
- `MODE` slide switch:
  - `HIGH` = spark-test mode
  - `LOW` = hydrogen-test mode

## How To Use It In Wokwi Web

1. Create a new Arduino Mega project in Wokwi.
2. Replace the default `diagram.json` with the contents of:
   [diagram.json](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/diagram.json)
3. Create a second file in the Wokwi project named `mduino_wokwi_pins.h`.
4. Paste into it the contents of:
   [mduino_wokwi_pins.h](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/mduino_wokwi_pins.h)
5. Replace the default `sketch.ino` with the contents of:
   [M_Duino_v002_Wokwi.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/M_Duino_v002_Wokwi.ino)
6. Start the simulation and open the Serial Monitor.

If you want the LEDs to be clearly visible during hydrogen-mode simulation,
use this file instead:

- [M_Duino_v002_Wokwi_visible.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/Wokwi/arduino-mega-v002/M_Duino_v002_Wokwi_visible.ino)

That simulator-only variant uses:
- `hotWireBurn_us = 300 ms`
- `sparkDwell_us = 500 ms`
- `daqPulse_us = 150 ms`

## Recommended Bench Checks In Wokwi

### Hydrogen-test mode

1. Put `MODE` in `LOW`.
2. Press `ARM`.
3. Press `TRIGGER`.
4. Confirm this sequence:
   - `Arm Light` turns on
   - `Hot Wire 1-3` turn on for the configured burn time
   - hot-wire LEDs turn off
   - `SparkOut` turns on for the dwell interval
   - `DAQTrig` turns on near the end of the dwell interval
   - both outputs turn off
   - the controller stays locked out until `ARM` and `TRIGGER` are released

With the production-like Wokwi file, the hydrogen-mode spark/DAQ pulses are very
brief and may be hard to notice by eye:
- `SparkOut`: `5 ms`
- `DAQTrig`: `0.6 ms`

So if the Serial Monitor shows the correct state transitions but the LEDs seem
not to blink, that does not automatically mean the logic is wrong.

### Spark-test mode

1. Put `MODE` in `HIGH`.
2. Press and hold `ARM`.
3. Confirm repeated `SparkOut` pulses.
4. Confirm `DAQTrig` stays off in spark-test mode.

## Recommended Temporary Timing Edits For Wokwi

The production timings are intentionally long for real hardware.
For faster simulation, temporarily edit only these constants inside Wokwi:

```cpp
const bool useBenchTestTimings = true;
const unsigned long sparkDwell_us = 5000UL;
const unsigned long daqPulse_us = 600UL;
```

If you want a much faster hydrogen-mode demo in Wokwi, also reduce:

```cpp
const unsigned long hotWireBurn_us =
  useBenchTestTimings ? (300UL * usPerMs) : (10UL * usPerS);
```

That change should stay in the **Wokwi copy only**, not in the production firmware,
unless you intentionally want to alter the real controller behavior.

## What This Simulation Does Not Prove

This simulation is good for firmware logic review, but it does **not** validate:

- real M-Duino input/output delays
- relay actuation timing
- ignition coil dwell or spark energy
- DAQ hardware trigger thresholds
- camera synchronization
- electrical safety behavior

Use it to verify the **state machine and event order**, not the final hardware timing.
